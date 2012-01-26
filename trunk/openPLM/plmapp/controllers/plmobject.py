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
"""

import re

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

import openPLM.plmapp.models as models
from openPLM.plmapp.exceptions import RevisionError, PermissionError,\
    PromotionError
from openPLM.plmapp.utils import level_to_sign_str
from openPLM.plmapp.controllers.base import Controller, permission_required

rx_bad_ref = re.compile(r"[?/#\n\t\r\f]|\.\.")
class PLMObjectController(Controller):
    u"""
    Object used to manage a :class:`~plmapp.models.PLMObject` and store his 
    modification in an history
    
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
        
        profile = user.get_profile()
        if not (profile.is_contributor or profile.is_administrator):
            raise PermissionError("%s is not a contributor" % user)
        if not reference or not type or not revision:
            raise ValueError("Empty value not permitted for reference/type/revision")
        if rx_bad_ref.search(reference) or rx_bad_ref.search(revision):
            raise ValueError("Reference or revision contains a '/' or a '..'")
        try:
            class_ = models.get_all_plmobjects()[type]
        except KeyError:
            raise ValueError("Incorrect type")
        # create an object
        obj = class_(reference=reference, type=type, revision=revision,
                     owner=user, creator=user)
        if no_index:
            obj.no_index = True
        if data:
            for key, value in data.iteritems():
                if key not in ["reference", "type", "revision"]:
                    setattr(obj, key, value)
        obj.state = models.get_default_state(obj.lifecycle)
        obj.save()
        res = cls(obj, user)
        if block_mails:
            res.block_mails()
        # record creation in history
        infos = {"type" : type, "reference" : reference, "revision" : revision}
        infos.update(data)
        details = u",".join(u"%s : %s" % (k, v) for k, v in infos.items())
        res._save_histo("Create", details)
        # add links
        models.PLMObjectUserLink.objects.create(plmobject=obj, user=user, role="owner")
        try:
            l = models.DelegationLink.objects.get(delegatee=user,
                    role=models.ROLE_SPONSOR)
            sponsor = l.delegator
            if sponsor.username == settings.COMPANY:
                sponsor = user
        except models.DelegationLink.DoesNotExist:
            sponsor = user
        # the user can promote to the next state
        models.PLMObjectUserLink.objects.create(plmobject=obj, user=user,
                                                 role=level_to_sign_str(0))
        # from the next state, only the sponsor can promote this object
        for i in range(1, obj.lifecycle.nb_states - 1):
            models.PLMObjectUserLink.objects.create(plmobject=obj, user=sponsor,
                                                    role=level_to_sign_str(i))
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
    
    def promote(self):
        u"""
        Promotes :attr:`object` in his lifecycle and writes his promotion in
        the history
        
        :raise: :exc:`.PromotionError` if :attr:`object` is not promotable
        :raise: :exc:`.PermissionError` if the use can not sign :attr:`object`
        """
        if self.object.is_promotable():
            state = self.object.state
            lifecycle = self.object.lifecycle
            lcl = lifecycle.to_states_list()
            self.check_permission(level_to_sign_str(lcl.index(state.name)))
            try:
                new_state = lcl.next_state(state.name)
                self.object.state = models.State.objects.get_or_create(name=new_state)[0]
                self.object.save()
                details = "change state from %(first)s to %(second)s" % \
                                     {"first" :state.name, "second" : new_state}
                self._save_histo("Promote", details, roles=["sign_"])
                if self.object.state == lifecycle.official_state:
                    cie = models.User.objects.get(username=settings.COMPANY)
                    self.set_owner(cie)
            except IndexError:
                # FIXME raises it ?
                pass
        else:
            raise PromotionError()

    def demote(self):
        u"""
        Demotes :attr:`object` in his lifecycle and writes his demotion in the
        history
        
        :raise: :exc:`.PermissionError` if the use can not sign :attr:`object`
        """
        if not self.is_editable:
            raise PromotionError()
        state = self.object.state
        lifecycle = self.object.lifecycle
        lcl = lifecycle.to_states_list()
        try:
            new_state = lcl.previous_state(state.name)
            self.check_permission(level_to_sign_str(lcl.index(new_state)))
            self.object.state = models.State.objects.get_or_create(name=new_state)[0]
            self.object.save()
            details = "change state from %(first)s to %(second)s" % \
                    {"first" :state.name, "second" : new_state}
            self._save_histo("Demote", details, roles=["sign_"])
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
        if role == models.ROLE_OWNER and self.owner == self._user:
            return True
        if self.plmobjectuserlink_plmobject.filter(user=self._user, role=role).exists():
            return True

        users = models.DelegationLink.get_delegators(self._user, role)
        qset = self.plmobjectuserlink_plmobject.filter(user__in=users,
                                                          role=role)
        return bool(qset)

    def check_editable(self):
        """
        Raises a :exc:`.PermissionError` if :attr:`object` is not editable.
        """
        if not self.object.is_editable:
            raise PermissionError("The object is not editable")

    def revise(self, new_revision):
        u"""
        Makes a new revision: duplicates :attr:`object`. The duplicated 
        object's revision is *new_revision*.

        Returns a controller of the new object.
        """
        self.check_readable() 
        if not new_revision or new_revision == self.revision or \
           rx_bad_ref.search(new_revision):
            raise RevisionError("Bad value for new_revision")
        if models.RevisionLink.objects.filter(old=self.object.pk):
            raise RevisionError("a revision already exists for %s" % self.object)
        data = {}
        fields = self.get_modification_fields() + self.get_creation_fields()
        for attr in fields:
            if attr not in ("reference", "type", "revision"):
                data[attr] = getattr(self.object, attr)
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
        see the objects.
        """
        # objects.get fails if a link does not exist
        # we can revise if any links exist
        try:
            models.RevisionLink.objects.get(old=self.object.pk)
            return False
        except ObjectDoesNotExist:
            return self.check_readable(False)
    
    def get_previous_revisions(self):
        try:
            link = models.RevisionLink.objects.get(new=self.object.pk)
            controller = type(self)(link.old, self._user)
            return controller.get_previous_revisions() + [link.old]
        except ObjectDoesNotExist:
            return []

    def get_next_revisions(self):
        try:
            link = models.RevisionLink.objects.get(old=self.object.pk)
            controller = type(self)(link.new, self._user)
            return [link.new] + controller.get_next_revisions()
        except ObjectDoesNotExist:
            return []

    def get_all_revisions(self):
        """
        Returns a list of all revisions, ordered from less recent to most recent
        
        :rtype: list of :class:`.PLMObject`
        """
        return self.get_previous_revisions() + [self.object] +\
               self.get_next_revisions()

    def set_owner(self, new_owner):
        """
        Sets *new_owner* as current owner.
        
        :param new_owner: the new owner
        :type new_owner: :class:`~django.contrib.auth.models.User`
        :raise: :exc:`.PermissionError` if *new_owner* is not a contributor
        """

        self.check_contributor(new_owner)
        links = models.PLMObjectUserLink.objects.filter(plmobject=self.object,
                role="owner")
        for link in links:
            link.delete()
        link = models.PLMObjectUserLink.objects.get_or_create(user=self.owner,
               plmobject=self.object, role="owner")[0]
        self.owner = new_owner
        link.user = new_owner
        link.save()
        self.save()
        # we do not need to write this event in an history since save() has
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
        models.PLMObjectUserLink.objects.create(plmobject=self.object,
            user=new_notified, role="notified")
        details = "user: %s" % new_notified
        self._save_histo("New notified", details) 

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
        link = models.PLMObjectUserLink.objects.get(plmobject=self.object,
                user=notified, role="notified")
        link.delete()
        details = "user: %s" % notified
        self._save_histo("Notified removed", details) 

    def set_signer(self, signer, role):
        """
        Sets *signer* as current signer for *role*. *role* must be a valid
        sign role (see :func:`.level_to_sign_str` to get a role from a
        sign level (int))
        
        :param signer: the new signer
        :type signer: :class:`~django.contrib.auth.models.User`
        :param str role: the sign role
        :raise: :exc:`.PermissionError` if *signer* is not a contributor
        :raise: :exc:`.PermissionError` if *role* is invalid (level to high)
        """
        self.check_contributor(signer)
        # remove old signer
        old_signer = None
        try:
            link = models.PLMObjectUserLink.objects.get(plmobject=self.object,
               role=role)
            old_signer = link.user
            link.delete()
        except ObjectDoesNotExist:
            pass
        # check if the role is valid
        max_level = self.lifecycle.nb_states - 1
        level = int(re.search(r"\d+", role).group(0))
        if level > max_level:
            # TODO better exception ?
            raise PermissionError("bad role")
        # add new signer
        models.PLMObjectUserLink.objects.create(plmobject=self.object,
                                                user=signer, role=role)
        details = "signer: %s, level : %d" % (signer, level)
        if old_signer:
            details += ", old signer: %s" % old_signer
        self._save_histo("New signer", details) 

    def set_role(self, user, role):
        """
        Sets role *role* (like `owner` or `notified`) for *user*

        .. note::
            If *role* is `owner` or a sign role, the old user who had
            this role will lose it.

            If *role* is notified, others roles are preserved.
        
        :raise: :exc:`ValueError` if *role* is invalid
        :raise: :exc:`.PermissionError` if *user* is not allowed to has role
            *role*
        """
        if role == "owner":
            self.set_owner(user)
        elif role == "notified":
            self.add_notified(user)
        elif role.startswith("sign"):
            self.set_signer(user, role)
        else:
            raise ValueError("bad value for role")

    def check_permission(self, role, raise_=True):
        if not bool(self.group.user_set.filter(id=self._user.id)):
            if raise_:
                raise PermissionError("action not allowed for %s" % self._user)
            else:
                return False
        return super(PLMObjectController, self).check_permission(role, raise_)

    def check_readable(self, raise_=True):
        if not self.is_editable:
            return True
        if bool(self.group.user_set.filter(id=self._user.id)):
            return True
        if raise_:
            raise PermissionError("You can not see this object.")
        return False

