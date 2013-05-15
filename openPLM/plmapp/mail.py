############################################################################
# openPLM - open source PLM
# Copyright 2010 Philippe Joulaud, Pierre Cosquer
#
# This file is part of openPLM.
#
#    openPLM is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    openPLM is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with openPLM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

"""
This module contains a function :func:`send_mail` which can be used to notify
users about a changement in a :class:`.PLMObject`.
"""
from collections import Iterable, Mapping, defaultdict
from operator import itemgetter
from itertools import groupby

import kjbuckets

from django.conf import settings
from django.utils import translation
from django.utils.translation import ugettext as _
from django.core.mail import EmailMultiAlternatives
from django.db.models import Model, Q
from django.template.loader import render_to_string
from django.db.models.loading import get_model
from django.contrib.sites.models import Site
from djcelery_transactions import task

from openPLM.plmapp.models import (User, UserProfile,
        DelegationLink, ROLE_OWNER, ROLE_SIGN)


def get_recipients(obj, roles, users):
    recipients = set(users)
    if hasattr(obj, "users"):
        manager = obj.users.now().order_by()
        roles_filter = Q()

        for role in roles:
            if role == ROLE_SIGN:
                roles_filter |= Q(role__startswith=role)
            else:
                roles_filter |= Q(role=role)
        users = list(manager.filter(roles_filter).values_list("user", flat=True).distinct())
        recipients.update(users)
        links = tuple(DelegationLink.current_objects.filter(roles_filter).order_by("role")\
                .values_list("role", "delegator", "delegatee"))
        for role, group in groupby(links, itemgetter(0)):
            gr = kjbuckets.kjGraph(tuple((x[1], x[2]) for x in group))
            for u in users:
                recipients.update(gr.reachable(u).items())
    elif roles == [ROLE_OWNER]:
        if hasattr(obj, "owner"):
            recipients.add(obj.owner_id)
        elif isinstance(obj, User):
            recipients.add(obj.id)
    return recipients

def convert_users(users):
    if users:
        r = iter(users).next()
        if hasattr(r, "id"):
            users = [x.id for x in users]
    return users

class CT(object):
    __slots__ = ("app_label", "module_name", "pk")

    def __init__(self, app_label, module_name, pk):
        self.app_label = app_label
        self.module_name = module_name
        self.pk = pk

    def __getstate__(self):
        return dict(app_label=self.app_label,
                    module_name=self.module_name,
                    pk=self.pk)

    def __setstate__(self, state):
        self.app_label = state["app_label"]
        self.module_name = state["module_name"]
        self.pk = state["pk"]

    @classmethod
    def from_object(cls, obj):
        return cls(obj._meta.app_label, obj._meta.module_name, obj.pk)

    def get_object(self):
        model_class = get_model(self.app_label, self.module_name)
        return model_class.objects.get(pk=self.pk)


def serialize(obj):
    if isinstance(obj, basestring):
        return obj
    if isinstance(obj, Model):
        return CT.from_object(obj)
    elif isinstance(obj, Mapping):
        new_ctx = {}
        for key, value in obj.iteritems():
            new_ctx[key] = serialize(value)
        return new_ctx
    elif isinstance(obj, Iterable):
        return [serialize(o) for o in obj]
    return obj

def unserialize(obj):
    if isinstance(obj, basestring):
        return obj
    if isinstance(obj, CT):
        return obj.get_object()
    elif isinstance(obj, Mapping):
        new_ctx = {}
        for key, value in obj.iteritems():
            new_ctx[key] = unserialize(value)
        return new_ctx
    elif isinstance(obj, Iterable):
        return [unserialize(o) for o in obj]
    return obj

@task(name="openPLM.plmapp.mail.do_send_histories_mail",ignore_result=True)
def do_send_histories_mail(plmobject, roles, last_action, histories, user, blacklist=(),
              users=(), template="mails/history"):
    """
    Sends a mail to users who have role *role* for *plmobject*.

    :param plmobject: object which was modified
    :type plmobject: :class:`.PLMObject`
    :param str roles: list of roles of the users who should be notified
    :param str last_action: type of modification
    :param str histories: list of :class:`.AbstractHistory`
    :param user: user who made the modification
    :type user: :class:`~django.contrib.auth.models.User`
    :param blacklist: list of emails whose no mail should be sent (empty by default).

    """
    plmobject = unserialize(plmobject)
    recipients = get_recipients(plmobject, roles, users)
    if recipients:
        user = unserialize(user)
        subject = "[PLM] " + unicode(plmobject)
        ctx = {
                "last_action" : last_action,
                "histories" : histories,
                "plmobject" : plmobject,
                "user" : user,
            }
        do_send_mail(subject, recipients, ctx, template, blacklist)

@task(name="openPLM.plmapp.mail.do_send_mail", ignore_result=True)
def do_send_mail(subject, recipients, ctx, template, blacklist=()):
    if recipients:
        lang_to_email = defaultdict(set)
        if len(recipients) == 1:
            recipient = User.objects.select_related("profile__language").get(id=recipients.pop())
            if not recipient.is_active:
                return
            if not recipient.email or recipient.email in blacklist:
                return
            lang_to_email[recipient.profile.language].add(recipient.email)
        else:
            qs = UserProfile.objects.filter(user__in=recipients,
                    user__is_active=True).exclude(user__email="")
            for lang, email in qs.values_list("language", "user__email"):
                if email not in blacklist:
                    lang_to_email[lang].add(email)
            if not lang_to_email:
                return

        ctx = unserialize(ctx)
        ctx["site"] = Site.objects.get_current()
        for lang, emails in lang_to_email.iteritems():
            translation.activate(lang)
            html_content = render_to_string(template + ".html", ctx)
            message = _(render_to_string(template + ".txt", ctx))
            subj_translation = _(subject)
            msg = EmailMultiAlternatives(subj_translation, message.strip(),
                settings.EMAIL_OPENPLM, bcc=emails)
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=getattr(settings, "EMAIL_FAIL_SILENTLY", True))

        if lang_to_email:
            translation.deactivate()

def send_mail(subject, recipients, ctx, template, blacklist=()):
    ctx = serialize(ctx)
    do_send_mail.delay(subject, convert_users(recipients),
            ctx, template, blacklist)

def send_histories_mail(plmobject, roles, last_action, histories, user, blacklist=(),
              users=(), template="mails/history"):
    plmobject = CT.from_object(plmobject)
    histories = serialize(histories)
    user = CT.from_object(user)
    do_send_histories_mail.delay(plmobject, roles, last_action, histories,
            user, blacklist, convert_users(users), template)


