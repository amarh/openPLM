###########################################################################
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
"""

import re

from django.conf import settings
from django.shortcuts import get_object_or_404

import openPLM.plmapp.models as models
from openPLM.plmapp.exceptions import PermissionError,\
    PromotionError, ControllerError
from openPLM.plmapp.references import validate_reference
from openPLM.plmapp.utils import level_to_sign_str
from openPLM.plmapp.controllers.base import Controller

from .models import ECR, ECRHistory, ECRUserLink

class ECRController(Controller):
    u"""
    """

    HISTORY = ECRHistory

    @classmethod
    def create(cls, reference, user, data={}, block_mails=False,
            no_index=False):
        u"""
        This method builds a new :class:`.ECR` of
        type *class_* and return a :class:`ECRController` associated to
        the created object.

        :param reference: reference of the objet
        :param user: user who creates/owns the object
        :param data: a dict<key, value> with informations to add to the ECR
        :rtype: :class:`ECRController`
        """


        if not user.is_active:
            raise PermissionError(u"%s's account is inactive" % user)
        # even a restricted account can create an ECR
        if not reference:
            raise ValueError("Empty value not permitted for reference")
        validate_reference(reference)
        # create an object
        try:
            reference_number = int(re.search(r"^ECR_(\d+)$", reference).group(1))
            if reference_number > 2**31 - 1:
                reference_number = 0
        except:
            reference_number = 0
        obj = ECR(reference=reference, owner=user, creator=user,
                reference_number=reference_number)
        if no_index:
            obj.no_index = True
        if data:
            for key, value in data.iteritems():
                if key != "reference":
                    setattr(obj, key, value)
        obj.state = models.get_default_state(obj.lifecycle)
        obj.save()
        res = cls(obj, user)
        if block_mails:
            res.block_mails()
        # record creation in history
        infos = {"reference" : reference}
        infos.update(data)
        details = u",".join(u"%s : %s" % (k, v) for k, v in infos.items())
        res._save_histo("Create", details)
        # add links
        ECRUserLink.objects.create(ecr=obj, user=user, role="owner")
        try:
            l = models.DelegationLink.current_objects.get(delegatee=user,
                    role=models.ROLE_SPONSOR)
            sponsor = l.delegator
            if sponsor.username == settings.COMPANY:
                sponsor = user
        except models.DelegationLink.DoesNotExist:
            sponsor = user
        # the user can promote to the next state
        ECRUserLink.objects.create(ecr=obj, user=user, role=level_to_sign_str(0))
        # from the next state, only the sponsor can promote this object
        for i in range(1, obj.lifecycle.nb_states - 1):
            ECRUserLink.objects.create(ecr=obj, user=sponsor, role=level_to_sign_str(i))

        #res._update_state_history()
        return res

    @classmethod
    def create_from_form(cls, form, user, block_mails=False, no_index=False):
        u"""
        Creates a :class:`ECRController` from *form* and associates *user*
        as the creator/owner of the ECR.

        This method raises :exc:`ValueError` if *form* is invalid.

        :param form: a django form associated to a model
        :param user: user who creates/owns the object
        :rtype: :class:`ECRController`
        """
        if form.is_valid():
            ref = form.cleaned_data["reference"]
            obj = cls.create(ref, user, form.cleaned_data, block_mails, no_index)
            return obj
        else:
            raise ValueError("form is invalid")

    @classmethod
    def load(cls, type, reference, revision, user):
        obj = get_object_or_404(ECR, reference=reference)
        return cls(obj, user)

    # FIXME: lot of copy/paste from PLMObjectController
    def can_approve_promotion(self, user=None):
        return bool(self.get_represented_approvers(user))

    def get_represented_approvers(self, user=None):
        if user is None:
            user = self._user
        role = self.get_current_signer_role()
        delegators = set(models.DelegationLink.get_delegators(self._user, role))
        delegators.add(self._user.id)
        delegators.difference_update(self.get_approvers())
        delegators.intersection_update(self.get_current_signers())
        return delegators

    def is_last_promoter(self):
        role = self.get_current_signer_role()
        is_signer = self.has_permission(role)
        represented = self.get_represented_approvers()
        if is_signer and represented:
            approvers = self.get_approvers()
            other_signers = self.get_current_signers()\
                    .exclude(user__in=approvers).exclude(user__in=represented)
            return not other_signers.exists()
        else:
            return False

    def _all_approved(self):
        not_approvers = self.get_current_signers().exclude(user__in=self.get_approvers())
        return not not_approvers.exists()

    def approve_promotion(self):
        if self.object.is_promotable():
            lcl = self.lifecycle.to_states_list()
            role = level_to_sign_str(lcl.index(self.state.name))
            self.check_permission(role)

            represented = self.get_represented_approvers()
            if not represented:
                raise PromotionError()
            next_state = lcl.next_state(self.state.name)
            nxt = models.State.objects.get(name=next_state)
            users = list(models.User.objects.filter(id__in=represented))
            for user in users:
                self.approvals.create(user=user, current_state=self.object.state, next_state=nxt)
            if self._all_approved():
                self.promote(checked=True)
            else:
                details = u"Current state: %s, next state:%s\n" % (self.state.name, next_state)
                details += u"Represented users: %s" % u", ".join(u.username for u in users)
                self._save_histo(u"Approved promotion", details, roles=(role,))
        else:
            raise PromotionError()

    def discard_approvals(self):
        role = self.get_current_signer_role()
        self.check_permission(role)
        self._clear_approvals()
        details = u"Current state:%s" % self.state.name
        self._save_histo(u"Removed promotion approvals", details, roles=(role,))

    def _clear_approvals(self):
        self.approvals.now().end()

    def promote(self, checked=False):
        u"""
        Promotes :attr:`object` in its lifecycle and writes its promotion in
        the history

        :raise: :exc:`.PromotionError` if :attr:`object` is not promotable
        :raise: :exc:`.PermissionError` if the use can not sign :attr:`object`
        """
        if checked or self.object.is_promotable():
            state = self.object.state
            lifecycle = self.object.lifecycle
            lcl = lifecycle.to_states_list()
            if not checked:
                self.check_permission(level_to_sign_str(lcl.index(state.name)))
            try:
                new_state = lcl.next_state(state.name)
                self.object.state = models.State.objects.get_or_create(name=new_state)[0]
                self.object.save()
                details = "change state from %(first)s to %(second)s" % \
                                     {"first" :state.name, "second" : new_state}
                self._save_histo("Promote", details, roles=["sign_"])
                if self.object.state == lifecycle.official_state:
                    self._officialize()
                #self._update_state_history()
                self._clear_approvals()
            except IndexError:
                # FIXME raises it ?
                pass
        else:
            raise PromotionError()

    def _officialize(self):
        """ Officialize the object (called by :meth:`promote`)."""
        # changes the owner to the company
        cie = models.User.objects.get(username=settings.COMPANY)
        self.set_owner(cie, True)

    def demote(self):
        u"""
        Demotes :attr:`object` in irs lifecycle and writes irs demotion in the
        history

        :raise: :exc:`.PermissionError` if the use can not sign :attr:`object`
        """
        if not self.is_proposed:
            raise PromotionError()
        state = self.object.state
        lifecycle = self.object.lifecycle
        lcl = lifecycle.to_states_list()
        try:
            new_state = lcl.previous_state(state.name)
            self.check_permission(level_to_sign_str(lcl.index(new_state)))
            self.object.state = models.State.objects.get_or_create(name=new_state)[0]
            self.object.save()
            self._clear_approvals()
            details = "change state from %(first)s to %(second)s" % \
                    {"first" :state.name, "second" : new_state}
            self._save_histo("Demote", details, roles=["sign_"])
            #self._update_state_history()
        except IndexError:
            # FIXME raises it ?
            pass

    def _save_histo(self, action, details, blacklist=(), roles=(), users=()):
        """
        Records *action* with details *details* made by :attr:`_user` in
        on :attr:`object` in the histories table.

        *blacklist*, if given, should be a list of email whose no mail should
        be sent (empty by default).

        A mail is sent to all notified users. Moreover, more roles can be
        notified by settings the *roles" argument.
        """
        roles = ["notified"] + list(roles)
        super(ECRController, self)._save_histo(action, details,
                blacklist, roles, users)

    def has_permission(self, role):
        if not self._user.is_active:
            return False
        if role == models.ROLE_OWNER and self.owner == self._user:
            return True
        if self.users.now().filter(user=self._user, role=role).exists():
            return True

        users = models.DelegationLink.get_delegators(self._user, role)
        if users:
            qset = self.users.now().filter(user__in=users,
                                                          role=role)
            return qset.exists()
        else:
            return False

    def check_editable(self):
        """
        Raises a :exc:`.PermissionError` if :attr:`object` is not editable.
        """
        if not self.object.is_editable:
            raise PermissionError("The object is not editable")

    def check_in_group(self, user, raise_=True):
        """
        Checks that *user* belongs to the object's group.

        Returns True if the user belongs to the group.
        Otherwise, returns False if *raise_* is False or raises
        a :exc:`.PermissionError` if *raise_* is True.

        Note that it always returns True if *user* is the company.
        """
        return True

    def set_owner(self, new_owner, dirty=False):
        """
        Sets *new_owner* as current owner.

        .. note::
            This method does **NOT** check that the current user
            is the owner of the object. :meth:`set_role` does that check.

        :param new_owner: the new owner
        :type new_owner: :class:`~django.contrib.auth.models.User`
        :param dirty: True if set_owner should skip sanity checks and
                      should not send a mail (usefull for tests, default is
                      False)
        :raise: :exc:`.PermissionError` if *new_owner* is not a contributor
        :raise: :exc:`ValueError` if *new_owner* is the company and the
                object is editable

        """

        if not dirty:
            self.check_contributor(new_owner)
            if new_owner.username == settings.COMPANY:
                if self.is_editable:
                    raise ValueError("The company cannot own an editable object.")

        links = ECRUserLink.objects.now().filter(ecr=self.object, role="owner")
        links.end()
        ECRUserLink.objects.create(user=new_owner, ecr=self.object, role="owner")
        if dirty:
            self.object.owner = new_owner
            self.object.save()
        else:
            self.owner = new_owner
            self.save()
        # we do not need to write this event in a history since save() has
        # already done it

    def add_notified(self, new_notified):
        """
        Adds *new_notified* to the list of users notified when :attr:`object`
        changes.

        :param new_notified: the new user who would be notified
        :type new_notified: :class:`~django.contrib.auth.models.User`
        :raise: :exc:`IntegrityError` if *new_notified* is already notified
            when :attr:`object` changes
        """
        if new_notified != self._user:
            self.check_permission("owner")
        if not new_notified.is_active:
            raise PermissionError(u"%s's account is inactive" % new_notified)
        ECRUserLink.objects.create(ecr=self.object, user=new_notified, role="notified")
        details = u"user: %s" % new_notified
        self._save_histo("New notified", details)

    def add_reader(self, new_reader):
        if not self.is_official:
            raise ValueError("Object is not official")
        if not new_reader.is_active:
            raise PermissionError(u"%s's account is inactive" % new_reader)
        ECRUserLink.objects.create(ecr=self.object,
            user=new_reader, role=models.ROLE_READER)
        details = "user: %s" % new_reader
        self._save_histo("New reader", details)

    def check_edit_signer(self, raise_=True):
        """
        .. versionadded:: 1.2

        Checks that the current user can edit the signers of the object:

            * He must own the object
            * No user should have approved the promotion

        :raise: :exc:`.PermissionError` if *raise_* is True and one of the
                above conditions is not met
        :return: True if the user can edit the signers
        """
        r = self.check_permission("owner", raise_=raise_)
        if r and self.approvals.now().exists():
            if raise_:
                raise PermissionError("One user has appproved a promotion.")
            return False
        return r

    def can_edit_signer(self):
        """
        .. versionadded:: 1.2

        Returns True if the user can edit signers of the object.
        """
        return self.check_edit_signer(raise_=False)

    def check_signer(self, user, role):
        """
        .. versionadded:: 1.2

        Checks that *user* can become a signer.

        :raise: :exc:`.PermissionError` if *user* is not a contributor
        :raise: :exc:`ValueError` if *role* is not a valid signer role according to
                the object's lifecycle
        """
        self.check_contributor(user)
        # check if the role is valid
        if not role.startswith(models.ROLE_SIGN):
            raise ValueError("Invalid role")
        max_level = self.lifecycle.nb_states - 1
        level = int(re.search(r"\d+", role).group(0))
        if level > max_level:
            raise ValueError("Invalid role")

    def add_signer(self, new_signer, role):
        """
        .. versionadded:: 1.2

        Adds *new_signer* to the list of signer for the role *role*.

        :raise: exceptions raised by :meth:`check_edit_signer`
        :raise: exceptions raised by :meth:`check_signer`
        """
        self.check_edit_signer()
        self.check_signer(new_signer, role)
        ECRUserLink.objects.create(ecr=self.object, user=new_signer, role=role)
        details = u"user: %s" % new_signer
        self._save_histo("New %s" % role, details, roles=(role,))

    def remove_notified(self, notified):
        """
        Removes *notified* to the list of users notified when :attr:`object`
        changes.

        :param notified: the user who would be no more notified
        :type notified: :class:`~django.contrib.auth.models.User`
        :raise: :exc:`ObjectDoesNotExist` if *notified* is not notified
            when :attr:`object` changes
        """

        if notified != self._user:
            self.check_permission("owner")
        link = ECRUserLink.current_objects.get(ecr=self.object,
                user=notified, role="notified")
        link.end()
        details = u"user: %s" % notified
        self._save_histo("Notified removed", details)

    def remove_reader(self, reader):
        """
        Removes *reader* to the list of restricted readers when :attr:`object`
        changes.

        :param reader: the user who would be no more reader
        :type reader: :class:`~django.contrib.auth.models.User`
        :raise: :exc:`ObjectDoesNotExist` if *reader* is not reader
        """

        link = ECRUserLink.current_objects.get(ecr=self.object,
                user=reader, role=models.ROLE_READER)
        link.end()
        details = u"user: %s" % reader
        self._save_histo("Reader removed", details)

    def remove_signer(self, signer, role):
        """
        .. versionadded:: 1.2

        Removes *signer* to the list of signers for role *role*.

        :param signer: the user who would be no more signer
        :type signer: :class:`~django.contrib.auth.models.User`
        :raise: :exc:`.PermissionError` if:

            * user is not the owner
            * one signer has approved the promotion
            * there is only one signer

        :raise: :exc:`ObjectDoesNotExist` if *signer* is not a signer
        """
        self.check_edit_signer()
        if not role.startswith(models.ROLE_SIGN):
            raise ValueError("Not a sign role")
        if self.users.now().filter(role=role).count() <= 1:
            raise PermissionError("Can not remove signer, there is only one signer.")
        link = ECRUserLink.current_objects.get(ecr=self.object,
                user=signer, role=role)
        link.end()
        details = u"user: %s" % signer
        self._save_histo("%s removed" % role, details, roles=(role,))

    def replace_signer(self, old_signer, new_signer, role):
        """
        .. versionadded:: 1.2

        Sets *new_signer* as current signer instead of *old_signer* for *role*.
        *role* must be a valid sign role (see :func:`.level_to_sign_str` to get a role from a
        sign level (int)).

        :param old_signer: the replaced signer
        :type old_signer: :class:`~django.contrib.auth.models.User`
        :param new_signer: the new signer
        :type new_signer: :class:`~django.contrib.auth.models.User`
        :param str role: the sign role
        :raise: :exc:`.PermissionError` if *signer* is not a contributor
        :raise: :exc:`.ValueError` if *role* is invalid (level to high)
        """

        self.check_edit_signer()
        self.check_signer(new_signer, role)

        # remove old signer
        try:
            link = self.users.now().get(user=old_signer,
               role=role)
        except ECRUserLink.DoesNotExist:
            raise ValueError("Invalid old signer")
        link.end()
        # add new signer
        ECRUserLink.objects.create(ecr=self.object, user=new_signer, role=role)
        details = u"new signer: %s" % new_signer
        details += u", old signer: %s" % old_signer
        self._save_histo("New %s" % role, details, roles=(role,))

    def set_role(self, user, role):
        """
        Sets role *role* (like `owner` or `notified`) for *user*

        .. note::
            If *role* is :const:`.ROLE_OWNER`, the previous owner is
            replaced by *user*.

        :raise: :exc:`ValueError` if *role* is invalid
        :raise: :exc:`.PermissionError` if *user* is not allowed to has role
            *role*
        """
        if role == "owner":
            self.check_permission("owner")
            self.set_owner(user)
        elif role == models.ROLE_NOTIFIED:
            self.add_notified(user)
        elif role.startswith(models.ROLE_SIGN):
            self.check_permission("owner")
            self.add_signer(user, role)
        elif role == models.ROLE_READER:
            self.add_reader(user)
        else:
            raise ValueError("bad value for role")

    def remove_user(self, link):
        if link.role == models.ROLE_NOTIFIED:
            self.remove_notified(link.user)
        elif link.role == models.ROLE_READER:
            self.remove_reader(link.user)
        elif link.role.startswith(models.ROLE_SIGN):
            self.remove_signer(link.user, link.role)
        else:
            raise ValueError("Bad link")

    def check_permission(self, role, raise_=True):
        if self._user.username == settings.COMPANY:
            # the company is like a super user
            return True
        return super(ECRController, self).check_permission(role, raise_)

    def check_readable(self, raise_=True):
        """
        Returns ``True`` if the user can read (is allowed to) this object.

        Raises a :exc:`.PermissionError` if the user cannot read the object
        and *raise_* is ``True`` (the default).
        """
        if not self._user.is_active:
            raise PermissionError(u"%s's account is inactive" % self._user)
        if not self._user.profile.restricted:
            return True
        else:
            if self.owner_id == self._user.id:
                return True
        if raise_:
            raise PermissionError("You can not see this object.")
        return False

    def check_restricted_readable(self, raise_=True):
        """
        Returns ``True`` if the user can read (is allowed to) the restricted
        data of this object.

        Raises a :exc:`.PermissionError` if the user cannot read the object
        and *raise_* is ``True`` (the default).
        """
        if not self._user.is_active:
            raise PermissionError(u"%s's account is inactive" % self._user)
        if not self._user.profile.restricted:
            return self.check_readable(raise_)
        if self._user == self.owner:
            return True
        return super(ECRController, self).check_permission(models.ROLE_READER, raise_)

    def cancel(self):
        """
        Cancels the object:

            * Its lifecycle becomes "cancelled".
            * Its owner becomes the company.
            * It removes all signer.
        """
        company = models.User.objects.get(username=settings.COMPANY)
        self.lifecycle = models.get_cancelled_lifecycle()
        self.state = models.get_cancelled_state()
        self.set_owner(company, True)
        self.users.filter(role__startswith=models.ROLE_SIGN).end()
        self.plmobjects.end()
        self._clear_approvals()
        self.save(with_history=False)
        self._save_histo("Cancel", "Object cancelled")
        #self._update_state_history()

    def can_publish(self):
        """
        .. versionadded:: 1.1

        Returns True if the user can publish this object.
        """
        return False

    def can_unpublish(self):
        """
        .. versionadded:: 1.1

        Returns True if the user can unpublish this object.
        """
        return False

    def check_cancel(self,raise_=True):
        """
        .. versionadded:: 1.1

        Checks that an object can be cancelled.

        If *raise_* is True:

            :raise: :exc:`.PermissionError` if the object is not draft
            :raise: :exc:`.PermissionError` if the object has related previous
                    or next revision
            :raise: :exc:`.PermissionError` if the user has not owner rights on
                an object

        If *raise_* is False:

            Returns True if all previous tests has been succesfully passed,
            False otherwise.
        """
        res = self.is_draft
        if (not res) and raise_:
            raise PermissionError("Invalid state: the object is not draft")
        res = res and self.check_permission("owner",raise_=False)
        if (not res) and raise_:
            raise PermissionError("You are not allowed to cancel this object")
        return res

    def can_cancel(self):
        """
        .. versionadded:: 1.1

        Returns True if the user can cancel this object.
        """
        return self.check_cancel(raise_=False)

    def safe_cancel(self):
        self.check_cancel()
        self.cancel()

    def check_clone(self, raise_=True):
        """
        .. versionadded:: 1.1

        Checks that an object can be cloned.

        If *raise_* is True:

            :raise: :exc:`.PermissionError` if the object is not readable
            :raise: :exc:`.PermissionError` if the object can not be read
            :raise: :exc:`.PermissionError` if the object is not cloneable

        If *raise_* is False:

            Returns True if all previous tests has been succesfully passed,
            False otherwise.
        """
        if raise_:
            raise PermissionError()
        return False

    def can_clone(self):
        """
        Returns True if the user can clone this object.
        """
        return False

    def publish(self):
        raise ControllerError("An ECR can not be published")

    def unpublish(self):
        raise ControllerError("An ECR can not be unpublished")

    def get_previous_revisions(self):
        return []
    def get_next_revisions(self):
        return []
    def get_all_revisions(self):
        return [self.objects]

    def attach_object(self, plmobject):
        self.check_attach_object(plmobject)
        self.plmobjects.create(plmobject=plmobject)
        details = u"%s // %s // %s" % (plmobject.type, plmobject.reference, plmobject.revision)
        self._save_histo("Object attached", details)

    def detach_object(self, plmobject):
        self.check_detach_object(plmobject)
        self.plmobjects.now().filter(plmobject=plmobject.id).end()
        details = u"%s // %s // %s" % (plmobject.type, plmobject.reference, plmobject.revision)
        self._save_histo("Object detached", details)

    def is_object_attached(self, plmobject):
        return self.plmobjects.now().filter(plmobject=plmobject.id).exists()

    def check_attach_object(self, plmobject, raise_=True):
        self.check_permission(models.ROLE_OWNER, raise_)
        if self.is_cancelled:
            if raise_:
                raise ValueError("ECR is cancelled")
            return False
        if raise_:
            self.check_editable()
        elif not self.is_editable:
            return False
        if self.is_object_attached(plmobject):
            if raise_:
                raise ValueError("Object is already attached")
            return False
        return True

    def can_attach_object(self, plmobject):
        return self.check_attach_object(plmobject, False)

    def check_detach_object(self, plmobject, raise_=True):
        self.check_permission(models.ROLE_OWNER, raise_)
        if self.is_cancelled:
            if raise_:
                raise ValueError("ECR is cancelled")
            return False
        if raise_:
            self.check_editable()
        elif not self.is_editable:
            return False
        if not self.is_object_attached(plmobject):
            if raise_:
                raise ValueError("Object is not attached")
            return False
        return True

    def can_detach_plmobject(self, plmobject):
        return self.check_detach_object(plmobject, False)

    def get_attached_parts(self, time=None):
        types = models.get_all_parts().keys()
        return self.plmobjects.filter(plmobject__type__in=types).at(time)

    def get_attached_documents(self, time=None):
        types = models.get_all_documents().keys()
        return self.plmobjects.filter(plmobject__type__in=types).at(time)

