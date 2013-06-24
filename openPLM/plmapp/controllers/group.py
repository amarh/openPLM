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
This module contains a class called :class:`GroupController` which
provides a controller for :class:`~django.contrib.auth.models.Group`.
This class is similar to :class:`.PLMObjectController` but some methods
from :class:`.PLMObjectController` are not defined.
"""


from django.shortcuts import get_object_or_404
from django.utils import timezone

import openPLM.plmapp.models as models
from openPLM.plmapp.mail import send_mail
from openPLM.plmapp.tasks import update_index
from openPLM.plmapp.exceptions import PermissionError
from openPLM.plmapp.controllers.base import Controller, permission_required
from openPLM.plmapp.references import validate_reference

class GroupController(Controller):
    u"""
    Object used to manage a :class:`~django.contrib.auth.models.Group` and store his
    modification in a history

    :attributes:
        .. attribute:: object

            The :class:`~django.contrib.auth.models.Group` managed by the controller

    :param obj: managed object
    :type obj: an instance of :class:`~django.contrib.auth.models.Group`
    :param user: user who modify *obj*
    :type user: :class:`~django.contrib.auth.models.Group`

    .. note::
        This class does not inherit from :class:`.PLMObjectController`.

    """

    HISTORY = models.GroupHistory

    def __init__(self, obj, user, block_mails=False, no_index=False):
        if hasattr(obj, "groupinfo"):
            obj = obj.groupinfo
        super(GroupController, self).__init__(obj, user, block_mails, no_index)

    @classmethod
    def create(cls, name, description, user, data={}):
        profile = user.profile
        if not (profile.is_contributor or profile.is_administrator):
            raise PermissionError("%s is not a contributor" % user)
        if profile.restricted:
            raise PermissionError("Restricted account can not create a group.")
        if not user.is_active:
            raise PermissionError(u"%s's account is inactive" % user)
        if not name:
            raise ValueError("name must not be empty")
        try:
            validate_reference(name)
        except:
            raise ValueError("Name contains a '/' or a '..'")

        obj = models.GroupInfo(name=name, description=description)
        obj.creator = user
        obj.owner = user
        if data:
            for key, value in data.iteritems():
                if key not in ["name", "description"]:
                    setattr(obj, key, value)
        obj.save()
        infos = {"name" : name, "description" : description}
        infos.update(data)
        details = ",".join("%s : %s" % (k, v) for k, v in infos.items())
        res = cls(obj, user)
        user.groups.add(obj)
        res._save_histo("Create", details)
        update_index.delay("plmapp", "groupinfo", obj.pk)
        return res

    @classmethod
    def create_from_form(cls, form, user):
        u"""
        Creates a :class:`PLMObjectController` from *form* and associates *user*
        as the creator/owner of the PLMObject.

        This method raises :exc:`ValueError` if *form* is invalid.

        :param form: a django form associated to a model
        :param user: user who creates/owns the object
        :rtype: :class:`PLMObjectController`
        """
        if form.is_valid():
            name = form.cleaned_data["name"]
            desc = form.cleaned_data["description"]
            obj = cls.create(name, desc, user)
            return obj
        else:
            raise ValueError("form is invalid")

    @classmethod
    def load(cls, type, reference, revision, user):
        return cls(get_object_or_404(models.Group, name=reference), user)

    def has_permission(self, role):
        if not self._user.is_active:
            return False
        if role == models.ROLE_OWNER:
            return self.owner == self._user
        return False

    def update_users(self, formset):
        u"""
        Updates users with data from *formset*

        :param formset:
        :type formset: a formset_factory of
                        :class:`~plmapp.forms.ModifyUserForm`

        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
            :attr:`object`.
        """

        self.check_permission("owner")
        users = []
        if formset.is_valid():
            for form in formset.forms:
                group = form.cleaned_data["group"]
                if group.pk != self.object.pk:
                    raise ValueError("Bad group %s (%s expected)" % (group, self.object))
                delete = form.cleaned_data["delete"]
                user = form.cleaned_data["user"]
                if user == self.owner:
                    raise ValueError("Bad user %s" % user)
                if user.profile.restricted:
                    raise ValueError("Restricted account can not join a group")
                if delete:
                    users.append(user)
            for user in users:
                user.groups.remove(group)
            self._save_histo("User removed", ", ".join((u.username for u in users)))

    @permission_required(role=models.ROLE_OWNER)
    def add_user(self, user):
        """
        Asks *user* to join the group.

        An email is sent to *user* so that he can validate its inscription.

        :raises: :exc:`ValueError` if user's email is empty.
        """
        if not user.email:
            raise ValueError("user's email is empty")
        if user.profile.restricted:
            raise ValueError("Restricted account can not join a group")
        if not user.is_active:
            raise ValueError(u"%s's account is inactive" % user)
        inv = models.Invitation.objects.create(group=self.object, owner=self._user,
                guest=user, guest_asked=False)
        self.send_invitation_to_guest(inv)

    def ask_to_join(self):
        """
        Asks to join the group.

        An email is sent to the group's owner so that he can validate the
        inscription.

        :raises: :exc:`ValueError` if the owner's email is empty.
        """
        if not self.owner.email:
            raise ValueError("user's email is empty")
        if self._user.profile.restricted:
            raise ValueError("Restricted account can not join a group")
        if not self._user.is_active:
            raise PermissionError(u"%s's account is inactive" % self._user)
        inv = models.Invitation.objects.create(group=self.object, owner=self.owner,
                guest=self._user, guest_asked=True)
        self.send_invitation_to_owner(inv)

    def accept_invitation(self, invitation):
        """
        Accepts an invitation.

        If the owner sent *invitation*, it checks that :attr:`_user` is the
        guest and adds him to the group.

        If the guest sent *invitation*, it checks that :attr:`_user` is the
        owner and adds the guest to the group.
        """
        if invitation.state != models.Invitation.PENDING:
            raise ValueError("Invalid invitation")
        if invitation.guest_asked:
            if self._user != invitation.owner:
                raise PermissionError("You can not accept this invitation.")
        else:
            if self._user != invitation.guest:
                raise PermissionError("You can not accept this invitation.")
        if not self._user.is_active:
            raise PermissionError(u"%s's account is inactive" % self._user)

        invitation.state = models.Invitation.ACCEPTED
        invitation.validation_time = timezone.now()

        user = invitation.guest
        user.groups.add(self.object)
        invitation.save()
        user.save()
        self._save_histo("User added", user.username, users=(user,))

    def send_invitation_to_owner(self, invitation):
        """
        Sends a mail to the owner asking him to accept the invitation
        to join the group.

        This method can be called to resend an invitation.

        :raises: :exc:`ValueError` if the invitation's state is not
            :attr:`.Invitation.PENDING`
        """
        if invitation.state != models.Invitation.PENDING:
            raise ValueError("Invalid invitation")
        if self._user != invitation.guest:
            raise PermissionError("You can not send this invitation.")
        if not self._user.is_active:
            raise PermissionError(u"%s's account is inactive" % self._user)
        ctx = { "group" : self.object,
                "invitation" : invitation,
                "guest" : self._user,
                }
        subject = "[PLM] %s asks you to join the group %s" % (self._user, self.name)
        self._send_mail(send_mail, subject, [self.owner], ctx, "mails/invitation2")

    def send_invitation_to_guest(self, invitation):
        """
        Sends a mail to the guest asking him to accept the invitation
        to join the group.

        This method can be called to resend an invitation.

        :raises: :exc:`ValueError` if the invitation's state is not
            :attr:`.Invitation.PENDING`
        """
        if invitation.state != models.Invitation.PENDING:
            raise ValueError("Invalid invitation")
        if self._user != invitation.owner:
            raise PermissionError("You can not send this invitation.")
        if not self._user.is_active:
            raise PermissionError(u"%s's account is inactive" % self._user)
        ctx = { "group" : self.object,
                "invitation" : invitation,
                }
        subject = "[PLM] Invitation to join the group %s" % self.name
        self._send_mail(send_mail, subject, [invitation.guest], ctx,
                "mails/invitation1")

    def refuse_invitation(self, invitation):
        """
        Refuses an invitation.

        If the owner sent *invitation*, it checks that :attr:`_user` is the
        guest and *invitation* is marked as refused.

        If the guest sent *invitation*, it checks that :attr:`_user` is the
        owner and *invitation* is marked as refused.

        """
        if invitation.state != models.Invitation.PENDING:
            raise ValueError("Invalid invitation")
        if invitation.guest_asked:
            if self._user != invitation.owner:
                raise PermissionError("You can not refuse this invitation.")
        else:
            if self._user != invitation.guest:
                raise PermissionError("You can not refuse this invitation.")
        if not self._user.is_active:
            raise PermissionError(u"%s's account is inactive" % self._user)
        invitation.state = models.Invitation.REFUSED
        invitation.validation_time = timezone.now()
        invitation.save()
        # TODO mail

    def save(self, with_history=True):
        u"""
        Saves :attr:`object` and records its history in the database.
        If *with_history* is False, the history is not recorded.
        """
        super(GroupController, self).save(with_history)
        update_index.delay("plmapp", "groupinfo", self.object.pk)

    def get_attached_parts(self):
        types = models.get_all_parts().keys()
        return self.plmobject_group.exclude_cancelled().filter(type__in=types)

    def get_attached_documents(self):
        types = models.get_all_documents().keys()
        return self.plmobject_group.exclude_cancelled().filter(type__in=types)

    def check_readable(self, raise_=True):
        if self._user.profile.restricted or not self._user.is_active:
            if raise_:
                raise PermissionError("You can not see this group")
            return False
        return True

