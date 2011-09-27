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
from functools import wraps

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields import FieldDoesNotExist

import openPLM.plmapp.models as models
from openPLM.plmapp.mail import send_mail
from openPLM.plmapp.exceptions import RevisionError, PermissionError,\
    PromotionError
from openPLM.plmapp.utils import level_to_sign_str

_controller_rx = re.compile(r"(?P<type>\w+)Controller")

class MetaController(type):
    """
    Metaclass used to register a controller and get a controller associated
    to a type (see :meth:`get_controller`).

    See `how-to-add-a-controller`_ for more explanations.
    """
    #: dict<type_name(str) : Controller(like :class:`PLMObjectController`)>
    controllers_dict = {}

    def __new__(mcs, name, bases, attrs):
        cls = type.__new__(mcs, name, bases, attrs)
        if "MANAGED_TYPE" in attrs:
            managed = attrs["MANAGED_TYPE"].__name__
        else:
            m = _controller_rx.match(name)
            if m:
                managed = m.group("type")
            else:
                # the controller is not interresting
                return cls
        mcs.controllers_dict[managed] = cls
        return cls

    @classmethod
    def get_controller(cls, type_name):
        """
        Returns the a controller (subclass of :class:`PLMObjectController`) 
        associated to *type_name* (a string).

        For example, ``get_controller("Part")`` will return the class 
        :class:`.PartController`.
        """
        if type_name in cls.controllers_dict:
            return cls.controllers_dict[type_name]
        else:
            # get his model and return his parent controller
            if type_name == "PLMObject":
                # just a security to prevent an infinite recursion
                return PLMObjectController
            else:
                model = models.get_all_plmobjects()[type_name]
                parents = [p for p in model.__bases__ 
                                if issubclass(p, models.PLMObject)]
                return cls.get_controller(parents[0].__name__)

#: shortcut for :meth:`MetaController.get_controller`
get_controller = MetaController.get_controller

def permission_required(func=None, role="owner"):
    """
    Decorator for methods of :class:`PLMObjectController` which
    raises :exc:`.PermissionError` if :attr:`PLMObjectController._user`
    has not the role *role*
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            args[0].check_permission(role)
            return f(*args, **kwargs)
        wrapper.__doc__ = "Permission required: `%s`\n%s" % (role, wrapper.__doc__)
        return wrapper
    if func:
        return decorator(func)
    return decorator

rx_bad_ref = re.compile(r"[?/#\n\t\r\f]|\.\.")
class PLMObjectController(object):
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

    __metaclass__ = MetaController

    def __init__(self, obj, user):
        self.object = obj
        self._user = user
        # variable to store attribute changes
        self.__histo = ""
        # cache for permissions (dict(role->bool)) 
        self.__permissions = {}

    @classmethod
    def create(cls, reference, type, revision, user, data={}):
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
        if data:
            for key, value in data.iteritems():
                if key not in ["reference", "type", "revision"]:
                    setattr(obj, key, value)
        obj.state = models.get_default_state(obj.lifecycle)
        obj.save()
        res = cls(obj, user)
        # record creation in history
        infos = {"type" : type, "reference" : reference, "revision" : revision}
        infos.update(data)
        details = ",".join("%s : %s" % (k, v) for k, v in infos.items())
        res._save_histo("Create", details)
        # add links
        models.PLMObjectUserLink.objects.create(plmobject=obj, user=user, role="owner")
        for i in range(len(obj.lifecycle.to_states_list()) - 1):
            models.PLMObjectUserLink.objects.create(plmobject=obj, user=user,
                                                    role=level_to_sign_str(i))
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
            ref = form.cleaned_data["reference"]
            type = form.Meta.model.__name__
            rev = form.cleaned_data["revision"]
            obj = cls.create(ref, type, rev, user, form.cleaned_data)
            return obj
        else:
            raise ValueError("form is invalid")

    def get_verbose_name(self, attr_name):
        """
        Returns a verbose name for *attr_name*.

        Example::

            >>> ctrl.get_verbose_name("ctime")
            u'date of creation'
        """
        try:
            item = self.object._meta.get_field(attr_name).verbose_name
        except FieldDoesNotExist:
            item = attr_name
        return item   
    
    def update_from_form(self, form):
        u"""
        Updates :attr:`object` from data of *form*
        
        :raises: :exc:`ValueError` if *form* is invalid.
        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
            :attr:`object`.
        :raises: :exc:`.PermissionError` if :attr:`object` is not editable.
        """
        
        self.check_permission("owner")
        self.check_editable()
        if form.is_valid():
            need_save = False
            for key, value in form.cleaned_data.iteritems():
                if key not in ["reference", "type", "revision"]:
                    setattr(self, key, value)
                    need_save = True
            if need_save:
                self.save()
        else:
            raise ValueError("form is invalid")
    
    def check_permission(self, role, raise_=True):
        """
        This method checks if :attr:`_user` has permissions implied by *role*.
        For example, *role* can be *owner* or *notified*.

        If the check succeed, **True** is returned. Otherwise, if *raise_* is
        **True** (the default), an :exc:`.PermissionError` is raised and if
        *raise_* is **False**, **False** is returned.

        .. admonition:: Implementation details

            This method keeps a cache, so that you dont have to worry about
            multiple calls to this method.
        """
        
        if role in self.__permissions:
            ok = self.__permissions[role]
        else:
            users = [self._user.id]
            users.extend(models.DelegationLink.get_delegators(self._user, role))
            qset = self.plmobjectuserlink_plmobject.filter(user__in=users,
                                                          role=role)
            ok = bool(qset)
            self.__permissions[role] = ok
        if not ok and raise_:
            raise PermissionError("action not allowed for %s" % self._user)
        return ok

    def check_contributor(self, user=None):
        """
        This method checks if *user* is a contributor. If not, it raises
        :exc:`.PermissionError`.

        If *user* is None (the default), :attr:`_user` is used.
        """
        
        if not user:
            user = self._user
        profile = user.get_profile()
        if not (profile.is_contributor or profile.is_administrator):
            raise PermissionError("%s is not a contributor" % user)
    
    def check_editable(self):
        """
        Raises a :exc:`.PermissionError` if :attr:`object` is not editable.
        """
        if not self.object.is_editable:
            raise PermissionError("The object is not editable")

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

    def __setattr__(self, attr, value):
        # we override this method to make it to modify *object* directly
        # if we modify *object*, we records the modification in **__histo*
        if hasattr(self, "object") and hasattr(self.object, attr) and \
           not attr in self.__dict__:
            old_value = getattr(self.object, attr)
            setattr(self.object, attr, value)
            field = self.object._meta.get_field(attr).verbose_name.capitalize()
            if old_value != value:
                message = "%(field)s : changes from '%(old)s' to '%(new)s'" % \
                        {"field" : field, "old" : old_value, "new" : value}
                self.__histo += message + "\n"
        else:
            super(PLMObjectController, self).__setattr__(attr, value)

    def __getattr__(self, attr):
        # we override this method to get attributes from *object* directly
        obj = object.__getattribute__(self, "object")
        if hasattr(self, "object") and hasattr(obj, attr) and \
           not attr in self.__dict__:
            return getattr(obj, attr)
        else:
            return object.__getattribute__(self, attr)

    def save(self, with_history=True):
        u"""
        Saves :attr:`object` and records its history in the database.
        If *with_history* is False, the history is not recorded.
        """
        self.object.save()
        if self.__histo and with_history:
            self._save_histo("Modify", self.__histo) 
            self.__histo = ""

    def _save_histo(self, action, details, blacklist=(), roles=()):
        """
        Records *action* with details *details* made by :attr:`_user` in
        on :attr:`object` in the histories table.

        *blacklist*, if given, should be a list of email whose no mail should
        be sent (empty by default).

        A mail is sent to all notified users. Moreover, more roles can be
        notified by settings the *roles" argument.
        """
        h = models.History.objects.create(plmobject=self.object, action=action,
                                     details=details, user=self._user)
        roles = ["notified"] + list(roles)
        send_mail(self.object, roles, action, [h], self._user, blacklist)

    @permission_required(role="owner")
    def revise(self, new_revision):
        u"""
        Makes a new revision : duplicates :attr:`object`. The duplicated 
        object's revision is *new_revision*.

        Returns a controller of the new object.
        """
        
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
        Returns True if :attr:`object` is revisable : if :meth:`revise` can be
        called safely.

        If *check_user* is True (the default), it also checks if :attr:`_user` is
        the *owner* of :attr:`object`.
        """
        # objects.get fails if a link does not exist
        # we can revise if any links exist
        try:
            models.RevisionLink.objects.get(old=self.object.pk)
            return False
        except ObjectDoesNotExist:
            return self.check_permission("owner", False)
    
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
        max_level = len(self.lifecycle.to_states_list()) - 1
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

