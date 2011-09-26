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

from threading import Thread

import kjbuckets

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.models import Site

from openPLM.plmapp.models import User, DelegationLink


def send_mail(plmobject, roles, last_action, histories, user, blacklist=(),
              template="mails/history"):
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
    :return: set of emails whose a mail was sent

    .. note::

        This function fails silently if it can not send the mail.
        The mail is sent in a separated thread. 
    """
    subject = "[PLM] " + unicode(plmobject)

    recipients = set()
    manager = plmobject.plmobjectuserlink_plmobject
    for role in roles:
        users = manager.filter(role__contains=role).values_list("user", flat=True)
        recipients.update(users)
        links = DelegationLink.objects.filter(role__contains=role)\
                    .values_list("delegator", "delegatee")
        gr = kjbuckets.kjGraph(tuple(links))
        for u in users:
            recipients.update(gr.reachable(u).items())

    if recipients:
        emails = User.objects.filter(id__in=recipients).exclude(email="")\
                        .values_list("email", flat=True)
        emails = set(emails) - set(blacklist)
        ctx = {
                "last_action" : last_action,
                "histories" : histories, 
                "plmobject" : plmobject,
                "user" : user,
                "site" : Site.objects.get_current(),
            }
        html_content = render_to_string(template + ".htm", ctx)
        message = render_to_string(template + ".txt", ctx)
        msg = EmailMultiAlternatives(subject, message, settings.EMAIL_OPENPLM,
                emails)
        msg.attach_alternative(html_content, "text/html")
        t = Thread(target=msg.send, kwargs={"fail_silently" : True })
        t.start()
        return emails

    return set()



