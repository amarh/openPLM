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
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import openPLM.plmapp.models as models
from openPLM.plmapp.exceptions import RevisionError, PermissionError,\
    PromotionError
from openPLM.plmapp.references import parse_reference_number, validate_reference, validate_revision
from openPLM.plmapp.utils import level_to_sign_str
from openPLM.plmapp.controllers import get_controller
from openPLM.plmapp.controllers.base import Controller


class PLMObjectController(Controller):
    u"""
    Object used to manage a :class:`~plmapp.models.PLMObject` and store his
    modification in a history

    :attributes:
        .. attribute:: object

            The :class:`.PLMObject` managed by the controller
        .. attribute:: _user

            :class:`~django.contrib.auth.models.User` who modifies ``object``

    :param obj: managed object
    :type obj: a subinstance of :class:`.PLMObject`
    :param user: user who modifies *obj*
    :type user: :class:`~django.contrib.auth.models.User`
    """

    HISTORY = models.History

    @classmethod
    def create(cls, reference, type, revision, user, data={}, block_mails=False,
            no_index=False):
        u"""
        This method builds a new :class:`.PLMObject` of
        type *class_* and return a :class:`PLMObjectController` associated to
        the created object.

        Raises :exc:`ValueError` if *reference*, *type* or *revision* are
        empty. Raises :exc:`ValueError` if *type* is not valid.

        :param reference: reference of the objet
        :param type: type of the object
        :param revision: revision of the object
        :param user: user who creates/owns the object
        :param data: a dict<key, value> with informations to add to the plmobject
        :rtype: :class:`PLMObjectController`
        """

        profile = user.profile
        if not (profile.is_contributor or profile.is_administrator):
            raise PermissionError("%s is not a contributor" % user)
        if not user.is_active:
            raise PermissionError(u"%s's account is inactive" % user)
        if profile.restricted:
            raise PermissionError("Restricted account can not create a part or document.")
        if not reference or not type or not revision:
            raise ValueError("Empty value not permitted for reference/type/revision")
        validate_reference(reference)
        validate_revision(revision)
        try:
            class_ = models.get_all_plmobjects()[type]
        except KeyError:
            raise ValueError("Incorrect type")
        # create an object
        reference_number = parse_reference_number(reference, class_)
        obj = class_(reference=reference, type=type, revision=revision,
                     owner=user, creator=user, reference_number=reference_number)
        if no_index:
            obj.no_index = True
        if data:
            for key, value in data.iteritems():
                if key not in ["reference", "type", "revision", "auto", "pfiles"]:
                    setattr(obj, key, value)
        obj.state = models.get_default_state(obj.lifecycle)
        obj.save()
        res = cls(obj, user)
        if block_mails:
            res.block_mails()
        # record creation in history
        infos = {"type" : type, "reference" : reference, "revision" : revision}
        infos.update(data)
        details = u" / ".join(u"%s : %s" % (k, v) for k, v in infos.items()
                if k not in ("auto", "pfiles", "type", "reference", "revision", "name"))
        res._save_histo("created", details)

        # add links (bulk create)
        ctime = obj.ctime
        links = [models.PLMObjectUserLink(plmobject=obj, user=user, role="owner", ctime=ctime)]
        try:
            l = models.DelegationLink.current_objects.select_related("delegator").get(delegatee=user,
                    role=models.ROLE_SPONSOR)
            sponsor = l.delegator
            if sponsor.username == settings.COMPANY:
                sponsor = user
            elif not res.check_in_group(sponsor, False):
                sponsor = user
        except models.DelegationLink.DoesNotExist:
            sponsor = user
        # the user can promote to the next state
        links.append(models.PLMObjectUserLink(plmobject=obj, user=user,
            role=level_to_sign_str(0), ctime=ctime))
        # from the next state, only the sponsor can promote this object
        for i in range(1, obj.lifecycle.nb_states - 1):
            links.append(models.PLMObjectUserLink(plmobject=obj, user=sponsor,
                role=level_to_sign_str(i), ctime=ctime))
        models.PLMObjectUserLink.objects.bulk_create(links)

        res._update_state_history()
        return res

    @classmethod
    def create_from_form(cls, form, user, block_mails=False, no_index=False):
        u"""
        Creates a :class:`PLMObjectController` from *form* and associates *user*
        as the creator/owner of the PLMObject.

        This method raises :exc:`ValueError` if *form* is invalid.

        :param form: a django form associated to a model
        :param user: user who creates/owns the object
        :rtype: :class:`PLMObjectController`
        """
        if form.is_valid():
            ref = form.cleaned_data["reference"]
            type = form.Meta.model.__name__
            rev = form.cleaned_data["revision"]
            obj = cls.create(ref, type, rev, user, form.cleaned_data,
                    block_mails, no_index)
            return obj
        else:
            raise ValueError("form is invalid")

    @classmethod
    def load(cls, type, reference, revision, user):
        model = models.get_all_plmobjects()[type]
        obj = get_object_or_404(model, type=type, reference=reference,
                revision=revision)
        return cls(obj, user)

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
                details = u"Represented users: %s" % u", ".join(u.username for u in users)
                details += u"promoted from state: %s to state:%s" % (self.state.name, next_state)
                self._save_histo(u"promoted", details, roles=(role,))
        else:
            raise PromotionError()

    def discard_approvals(self):
        role = self.get_current_signer_role()
        self.check_permission(role)
        self._clear_approvals()
        details = u"Current state stays : %s" % self.state.name
        self._save_histo(u"removed promotion approvals", details, roles=(role,))

    def _clear_approvals(self):
        self.approvals.now().end()

    def promote(self, checked=False):
        u"""
        Promotes :attr:`object` in its lifecycle and writes its promotion in
        the history

        :raise: :exc:`.PromotionError` if :attr:`object` is not promotable
        :raise: :exc:`.PermissionError` if the use can not sign :attr:`object`
        :returns: a dictionary with two keys:

            new_state
                the new current :class:`.State` of the object

            updated_revisions
                a list of updated (deprecated or cancelled) revisions
        """
        if checked or self.object.is_promotable():
            state = self.object.state
            lifecycle = self.object.lifecycle
            lcl = lifecycle.to_states_list()
            if not checked:
                self.check_permission(level_to_sign_str(lcl.index(state.name)))
            new_state = lcl.next_state(state.name)
            self.object.state = models.State.objects.get_or_create(name=new_state)[0]
            self.object.save()
            details = "from state %(first)s to state %(second)s" % \
                                 {"first" :state.name, "second" : new_state}
            self._save_histo("promoted", details, roles=["sign_"])
            updated_revisions = []
            if self.object.state == lifecycle.official_state:
               updated_revisions = self._officialize()
            self._update_state_history()
            self._clear_approvals()
            return {"new_state": self.object, "updated_revisions": updated_revisions}
        else:
            raise PromotionError()

    def _officialize(self):
        """ Officialize the object (called by :meth:`promote`)."""
        # changes the owner to the company
        cie = models.User.objects.get(username=settings.COMPANY)
        self.set_owner(cie, True)
        updated_revisions = []
        for rev in self.get_previous_revisions():
            if rev.is_cancelled:
                # nothing to do
                pass
            elif rev.is_editable or rev.is_official:
                no_index = getattr(self.object, "no_index", False)
                ctrl = type(self)(rev.get_leaf_object(), self._user,
                        self._mail_blocked, no_index)
                if rev.is_editable:
                    ctrl.cancel()
                else:
                    ctrl._deprecate()
                if self._mail_blocked:
                    self._pending_mails.extends(ctrl._pending_mails)
                    del ctrl._pending_mails[:]
                updated_revisions.append(ctrl.object)
        return updated_revisions

    def _update_state_history(self):
        """ Updates the :class:`.StateHistory` table of the object."""
        now = timezone.now()
        # ends previous StateHistory if it exists
        # here we do not try to see if the state has not changed since
        # we are sure it is not the case and it would not be a problem
        # if it has not changed
        models.StateHistory.objects.filter(plmobject__id=self.object.id,
            end_time=None).update(end_time=now)
        models.StateHistory.objects.create(plmobject=self.object,
                start_time=now, end_time=None, state=self.state,
                lifecycle=self.lifecycle)

    def _deprecate(self):
        """ Deprecate the object. """
        cie = models.User.objects.get(username=settings.COMPANY)
        self.state = self.lifecycle.last_state
        self.set_owner(cie, True)
        self._clear_approvals()
        self.save()
        self._update_state_history()

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
            details = "from state %(first)s to state %(second)s" % \
                    {"first" :state.name, "second" : new_state}
            self._save_histo("demoted", details, roles=["sign_"])
            self._update_state_history()
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
        super(PLMObjectController, self)._save_histo(action, details,
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
            qset = self.users.now().filter(user__in=users, role=role)
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
        .. versionadded:: 1.0.1

        Checks that *user* belongs to the object's group.

        Returns True if the user belongs to the group.
        Otherwise, returns False if *raise_* is False or raises
        a :exc:`.PermissionError` if *raise_* is True.

        Note that it always returns True if *user* is the company.
        """
        if user.username == settings.COMPANY:
            return True
        if not self.group.user_set.filter(id=user.id).exists():
            if raise_:
                raise PermissionError("The user %s does not belong to the group." % user.username)
            else:
                return False
        return True

    def revise(self, new_revision, group=None):
        u"""
        Makes a new revision: duplicates :attr:`object`. The duplicated
        object's revision is *new_revision*.

        Returns a controller of the new object.
        """
        self.check_readable()
        if not new_revision or new_revision == self.revision:
            raise RevisionError("Bad value for new_revision")
        try:
            validate_revision(new_revision)
        except ValueError as e:
            raise RevisionError(unicode(e))
        if self.is_cancelled or self.is_deprecated:
            raise RevisionError("Object is deprecated or cancelled.")
        if models.RevisionLink.objects.now().filter(old=self.object.pk).exists():
            raise RevisionError("A revision already exists for %s" % self.object)
        if group is None:
            group = self.object.group
        if not group.user_set.filter(id=self._user.id).exists():
            raise ValueError("Invalid group")
        data = {}
        fields = self.get_modification_fields() + self.get_creation_fields()
        for attr in fields:
            if attr not in ("reference", "type", "revision"):
                data[attr] = getattr(self.object, attr)
        data["group"] = group
        data["state"] = models.get_default_state(self.lifecycle)
        new_controller = self.create(self.reference, self.type, new_revision,
                                     self._user, data)
        details = "old : %s, new : %s" % (self.object, new_controller.object)
        self._save_histo(models.RevisionLink.ACTION_NAME, details)
        models.RevisionLink.objects.create(old=self.object, new=new_controller.object)
        return new_controller

    def is_revisable(self, check_user=True):
        """
        Returns True if :attr:`object` is revisable: if :meth:`revise` can be
        called safely.

        If *check_user* is True (the default), it also checks if :attr:`_user` can
        see the object.
        """
        # a cancelled or deprecated object cannot be revised.
        if self.is_cancelled or self.is_deprecated:
            return False

        # objects.get fails if a link does not exist
        # we can revise if any links exist
        try:
            models.RevisionLink.objects.now().get(old=self.object.pk)
            return False
        except ObjectDoesNotExist:
            if check_user:
                return self.check_readable(False)
            else:
                return True

    def get_previous_revisions(self):
        all_revisions = self.get_all_revisions()
        return all_revisions[:all_revisions.index(self.object.plmobject_ptr)]

    def get_next_revisions(self):
        all_revisions = self.get_all_revisions()
        return all_revisions[all_revisions.index(self.object.plmobject_ptr)+1:]

    def get_all_revisions(self):
        """
        Returns a list of all revisions, ordered from less recent to most recent

        :rtype: list of :class:`.PLMObject`
        """
        objects = list(models.PLMObject.objects.filter(type=self.type,
            reference=self.reference))
        # maybe we could simply sort objects by their ctime...
        if len(objects) == 1:
            return objects
        rev_links = models.RevisionLink.current_objects.filter(old__in=objects).values_list("old", "new")
        id2obj = dict((o.id, o) for o in objects)
        for old, new in rev_links:
            old_obj = id2obj[old]
            new_obj = id2obj[new]
            objects.remove(old_obj)
            objects.insert(objects.index(new_obj), old_obj)
        return objects

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

        .. versionchanged:: 1.0.1

        :raise: :exc:`.PermissionError` if *new_owner* does not belong to
                the object's group.
        """

        if not dirty:
            self.check_contributor(new_owner)
            self.check_in_group(new_owner)
            if new_owner.username == settings.COMPANY:
                if self.is_editable:
                    raise ValueError("The company cannot own an editable object.")

        links = models.PLMObjectUserLink.objects.now().filter(plmobject=self.object,
                role="owner")
        links.end()
        models.PLMObjectUserLink.objects.create(user=new_owner,
               plmobject=self.object, role="owner")
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

        .. versionchanged:: 1.0.1

        :raise: :exc:`.PermissionError` if *new_notified* does not belong to
                the object's group.
        """
        if new_notified != self._user:
            self.check_permission("owner")
        if not new_notified.is_active:
            raise PermissionError(u"%s's account is inactive" % new_notified)
        self.check_in_group(new_notified)
        models.PLMObjectUserLink.objects.create(plmobject=self.object,
            user=new_notified, role="notified")
        details = u"user: %s to be notified" % new_notified
        self._save_histo("added new notification right", details)

    def add_reader(self, new_reader):
        if not self.is_official:
            raise ValueError("Object is not official")
        if not new_reader.profile.restricted:
            raise ValueError("Not a restricted account")
        if not new_reader.is_active:
            raise PermissionError(u"%s's account is inactive" % new_reader)
        self.check_in_group(self._user)
        models.PLMObjectUserLink.objects.create(plmobject=self.object,
            user=new_reader, role=models.ROLE_READER)
        details = "user: %s is a reader" % new_reader
        self._save_histo("added new reader", details)

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
        :raise: :exc:`.PermissionError` if *user* is not in the object's group
        :raise: :exc:`ValueError` if *role* is not a valid signer role according to
                the object's lifecycle
        """
        self.check_contributor(user)
        self.check_in_group(user)
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
        models.PLMObjectUserLink.objects.create(plmobject=self.object,
            user=new_signer, role=role)
        details = u"user: %s 's signature is necessary" % new_signer
        self._save_histo("added new %s" % role, details, roles=(role,))

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
        link = models.PLMObjectUserLink.current_objects.get(plmobject=self.object,
                user=notified, role="notified")
        link.end()
        details = u"user: %s is no longer notified" % notified
        self._save_histo("removed notification right", details)

    def remove_reader(self, reader):
        """
        Removes *reader* to the list of restricted readers when :attr:`object`
        changes.

        :param reader: the user who would be no more reader
        :type reader: :class:`~django.contrib.auth.models.User`
        :raise: :exc:`ObjectDoesNotExist` if *reader* is not reader
        """

        self.check_in_group(self._user)
        link = models.PLMObjectUserLink.current_objects.get(plmobject=self.object,
                user=reader, role=models.ROLE_READER)
        link.end()
        details = u"user: %s is no longer a reader" % reader
        self._save_histo("removed reader", details)

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
        link = models.PLMObjectUserLink.current_objects.get(plmobject=self.object,
                user=signer, role=role)
        link.end()
        details = u"user: %s 's signature is no longer necessary" % signer
        self._save_histo("removed %s" % role, details, roles=(role,))

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
        :raise: :exc:`.PermissionError` if *new_signer* does not belong to
                the object's group.
        :raise: :exc:`.ValueError` if *role* is invalid (level to high)
        """

        self.check_edit_signer()
        self.check_signer(new_signer, role)

        # remove old signer
        try:
            link = self.users.now().get(user=old_signer,
               role=role)
        except models.PLMObjectUserLink.DoesNotExist:
            raise ValueError("Invalid old signer")
        link.end()
        # add new signer
        models.PLMObjectUserLink.objects.create(plmobject=self.object,
                                                user=new_signer, role=role)
        details = u"user : %s " % old_signer
        details += u"is replaced by user : %s" % new_signer
        self._save_histo("changed %s" % role, details, roles=(role,))

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
        if self.users.now().filter(user=user, role=role).exists():
            raise ValueError(_("%(username)s has already this role.") % dict(username=user.username))
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
        if not self.group.user_set.filter(id=self._user.id).exists():
            if raise_:
                raise PermissionError("action not allowed for %s" % self._user)
            else:
                return False
        return super(PLMObjectController, self).check_permission(role, raise_)

    def check_readable(self, raise_=True):
        """
        Returns ``True`` if the user can read (is allowed to) this object.

        Raises a :exc:`.PermissionError` if the user cannot read the object
        and *raise_* is ``True`` (the default).
        """
        if not self._user.is_active:
            raise PermissionError(u"%s's account is inactive" % self._user)
        if not self._user.profile.restricted:
            if self.is_official or self.is_deprecated or self.is_cancelled:
                return True
            if self._user.username == settings.COMPANY:
                # the company is like a super user
                return True
            if self.owner_id == self._user.id:
                return True
            if self.group.user_set.filter(id=self._user.id).exists():
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
        return super(PLMObjectController, self).check_permission(models.ROLE_READER, raise_)

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
        self._clear_approvals()
        self.save(with_history=False)
        self._save_histo("cancelled", "%s (%s//%s//%s) cancelled"%(self.object.name, self.object.type, self.object.reference, self.object.revision))
        self._update_state_history()

    def check_publish(self, raise_=True):
        """
        .. versionadded:: 1.1

        Checks that an object can be published.

        If *raise_* is True:

            :raise: :exc:`.PermissionError` if the object is not official
            :raise: :exc:`.PermissionError` if the user is not allowed to publish
                an object (see :attr:`.UserProfile.can_publish`)
            :raise: :exc:`.PermissionError` if the user does not belong to
                the object's group
            :raise: :exc:`.ValueError` if the object is already published

        If *raise_* is False:

            Returns True if all previous tests has been succesfully passed,
            False otherwise.
        """
        res = self.is_official
        if (not res) and raise_:
            raise PermissionError("Invalid state: the object is not official")
        res = res and self._user.profile.can_publish
        if (not res) and raise_:
            raise PermissionError("You are not allowed to publish an object")
        res = res and self.check_in_group(self._user, raise_=raise_)
        res = res and not self.published
        if (not res) and raise_:
            raise ValueError("Object already published")
        return res

    def can_publish(self):
        """
        .. versionadded:: 1.1

        Returns True if the user can publish this object.
        """
        return self.check_publish(raise_=False)

    def publish(self):
        """
        .. versionadded:: 1.1

        Publish the object.

        A published object can be accessed by anonymous users.

        :raise: all exceptions raised by :meth:`check_publish`
        """
        self.check_publish()
        self.object.published = True
        self.object.save()
        details = u"%s (%s//%s//%s) published by %s (%s)" % (self.object.name, self.object.type, self.object.reference, self.object.revision, self._user.get_full_name(), self._user.username)
        self._save_histo("published", details)

    def check_unpublish(self, raise_=True):
        """
        .. versionadded:: 1.1

        Checks that an object can be unpublished.

        If *raise_* is True:

            :raise: :exc:`.PermissionError` if the user is not allowed to unpublish
                    an object (see :attr:`.UserProfile.can_publish`)
            :raise: :exc:`.PermissionError` if the user does not belong to
                    the object's group
            :raise: :exc:`.ValueError` if the object is unpublished

        If *raise_* is False:

            Returns True if all previous tests has been succesfully passed,
            False otherwise.
        """

        res = self._user.profile.can_publish
        if (not res) and raise_:
            raise PermissionError("You are not allowed to unpublish an object")
        res = res and self.check_in_group(self._user, raise_=raise_)
        res = res and self.published
        if (not res) and raise_:
            raise ValueError("Object not published")
        return res

    def can_unpublish(self):
        """
        .. versionadded:: 1.1

        Returns True if the user can unpublish this object.
        """
        return self.check_unpublish(raise_=False)

    def unpublish(self):
        """
        .. versionadded:: 1.1

        Unpublish the object.

        :raise: all exceptions raised by :meth:`check_unpublish`
        """
        self.check_unpublish()
        self.object.published = False
        self.object.save()
        details = u"%s (%s//%s//%s) unpublished by %s (%s)" % (self.object.name, self.object.type, self.object.reference, self.object.revision, self._user.get_full_name(), self._user.username)
        self._save_histo("unpublished", details)

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
        res = res and len(self.get_all_revisions())==1
        if (not res) and raise_:
            raise PermissionError("This object has more than 1 revision")
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
        res = self.check_readable(raise_=False)
        if (not res) and raise_:
            raise PermissionError("You can not clone this object : you shouldn't see it.")
        res = res and self._user.profile.is_contributor
        if (not res) and raise_:
            raise PermissionError("You can not clone this object since you are not a contributor.")
        res = res and self.is_cloneable
        if (not res) and raise_:
            raise PermissionError("This object can not be cloned")
        return res

    def can_clone(self):
        """
        .. versionadded:: 1.1

        Returns True if the user can clone this object.
        """
        return self.check_clone(raise_=False)

    def clone(self,form, user, block_mails=False, no_index=False):
        """
        .. versionadded:: 1.1

        Clone this object and return the related controller.

        :param form: the form sent from clone view
        :param user: the user who is cloning the object
        """
        self.check_clone()
        type_= self.object.type
        ctrl_cls = get_controller(type_)
        if form.is_valid():
            creation_fields = self.get_creation_fields()
            data = {}
            for field in form.cleaned_data :
                if field in creation_fields:
                    data[field]=form.cleaned_data[field]
            ref = form.cleaned_data["reference"]
            rev = form.cleaned_data["revision"]
            new_ctrl = ctrl_cls.create(ref, type_ , rev, user, data,
                    block_mails, no_index)
            return new_ctrl
        else:
            raise ValueError("form is invalid")

    @property
    def histories(self):
        objects = [o.id for o in self.get_all_revisions()]
        return self.HISTORY.objects.filter(plmobject__in=objects).\
                order_by('-date').select_related("user", "plmobject__revision")

