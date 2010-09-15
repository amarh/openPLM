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

import kjbuckets

from django.conf import settings
from django.core.mail import send_mail as sm

from openPLM.plmapp.models import User, DelegationLink

_TEMPLATE = u"""
Message from OpenPLM

Modification for {plmobject}:
    - Type : {action}
    - By : {user}
    - Details :
        {details}
"""

def send_mail(plmobject, role, action, details, user, blacklist=()):
    """
    Sends a mail to users who have role *role* for *plmobject*.

    :param plmobject: object which was modified
    :type plmobject: :class:`.PLMObject`
    :param str role: role of the users who should be notified (can be just the
                     first characters of the role to match several roles)
    :param str action: type of modification
    :param str details: details
    :param user: user who made the modification
    :type user: :class:`~django.contrib.auth.models.User` 
    :param blacklist: list of emails whose no mail should be sent (empty by default).
    :return: set of emails whose a mail was sent

    .. note::

        This function fails silently if it can not send the mail.
    """
    subject = u"[OpenPLM] -- %s" % plmobject
    details = details.replace("\n", "\n" + " " * 8)
    message = _TEMPLATE.format(**locals())
    users = plmobject.plmobjectuserlink_plmobject.filter(role__contains=role).values_list("user", flat=True)
    recipients = set(users)
    links = DelegationLink.objects.filter(role__contains=role)\
                .values_list("delegator", "delegatee")
    gr = kjbuckets.kjGraph(tuple(links))
    for user in users:
        recipients.update(gr.reachable(user).items())
    if recipients:
        emails = User.objects.filter(id__in=recipients).exclude(email="")\
                        .values_list("email", flat=True)
        emails = set(emails) - set(blacklist)
        sm(subject, message, settings.EMAIL_OPENPLM, emails, fail_silently=True)
        return emails
    return set()

