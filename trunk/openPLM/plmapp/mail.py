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
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pierre.cosquer@insa-rennes.fr
################################################################################

"""
This module contains a function :func:`send_mail` which can be used to notify
users about a changement in a :class:`.PLMObject`.
"""
from collections import Iterable, Mapping

import kjbuckets

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Model, Q
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from celery.task import task

from openPLM.plmapp.models import User, DelegationLink, ROLE_OWNER, ROLE_SIGN


def get_recipients(obj, roles, users):
    recipients = set(users)
    if hasattr(obj, "plmobjectuserlink_plmobject"):
        manager = obj.plmobjectuserlink_plmobject.order_by()
        users_q = Q()

        for role in roles:
            if role == ROLE_SIGN:
                users_q |= Q(role__startswith=role)
            else:
                users_q |= Q(role=role)
        users = manager.filter(users_q).values_list("user", flat=True)
        recipients.update(users)
        links = DelegationLink.objects.filter(users_q)\
                        .values_list("delegator", "delegatee")
        gr = kjbuckets.kjGraph(tuple(links))
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
    def __init__(self, ct_id, pk):
        self.ct_id = ct_id
        self.pk = pk

    @classmethod
    def from_object(cls, obj):
        return cls(ContentType.objects.get_for_model(obj).id, obj.pk)

    def get_object(self, ct_cache):
        ct = ct_cache.get(self.ct_id)
        if not ct:
            ct = ct_cache[self.ct_id] = ContentType.objects.get_for_id(self.ct_id)
        return ct.get_object_for_this_type(pk=self.pk)


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

def unserialize(obj, ct_cache):
    if isinstance(obj, basestring):
        return obj
    if isinstance(obj, CT):
        return obj.get_object(ct_cache)
    elif isinstance(obj, Mapping):
        new_ctx = {}
        for key, value in obj.iteritems():
            new_ctx[key] = unserialize(value, ct_cache)
        return new_ctx
    elif isinstance(obj, Iterable):
        return [unserialize(o, ct_cache) for o in obj]
    return obj

@task(ignore_result=True)
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

    .. note::

        This function fails silently if it can not send the mail.
        The mail is sent in a separated thread. 
    """
    ct_cache = {}
    plmobject = unserialize(plmobject, ct_cache)
    user = unserialize(user, ct_cache)
    subject = "[PLM] " + unicode(plmobject)
    recipients = get_recipients(plmobject, roles, users) 
    
    if recipients:
        ctx = {
                "last_action" : last_action,
                "histories" : histories, 
                "plmobject" : plmobject,
                "user" : user,
            }
        do_send_mail(subject, recipients, ctx, template, blacklist, ct_cache)

@task(ignore_result=True)
def do_send_mail(subject, recipients, ctx, template, blacklist=(), ct_cache=None):
    if recipients:
        ctx = unserialize(ctx, ct_cache or {})
        emails = User.objects.filter(id__in=recipients).exclude(email="")\
                        .values_list("email", flat=True)
        emails = set(emails) - set(blacklist)
        ctx["site"] = Site.objects.get_current()
        html_content = render_to_string(template + ".htm", ctx)
        message = render_to_string(template + ".txt", ctx)
        msg = EmailMultiAlternatives(subject, message, settings.EMAIL_OPENPLM,
            emails)
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=True)

def send_mail(subject, recipients, ctx, template, blacklist=()):
    ctx = serialize(ctx)
    do_send_mail.delay(subject, convert_users(recipients),
            ctx, template, blacklist) 

def send_histories_mail(plmobject, roles, last_action, histories, user, blacklist=(),
              users=(), template="mails/history"):
    if hasattr(plmobject, "object"):
        plmobject = plmobject.object
    plmobject = CT.from_object(plmobject)
    histories = serialize(histories)
    user = CT.from_object(user)
    do_send_histories_mail.delay(plmobject, roles, last_action, histories, user, blacklist,
              convert_users(users), template)


