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
"""

import re
import difflib
import itertools
from functools import wraps
from collections import deque

from django.db.models.fields import FieldDoesNotExist

import openPLM.plmapp.models as models
from openPLM.plmapp.exceptions import PermissionError
from openPLM.plmapp.mail import send_histories_mail

_controller_rx = re.compile(r"(?P<type>\w+)Controller")

class MetaController(type):
    """
    Metaclass used to register a controller and get a controller associated
    to a type (see :meth:`get_controller`).

    See :ref:`how-to-add-a-controller` for more explanations.
    """
    #: dict<type_name(str) : Controller(like :class:`PLMObjectController`)>
    controllers_dict = {}

    def __new__(mcs, name, bases, attrs):
        # sets a __slots__ attributes to reduce memory consumption
        if name != "Controller" and "__slots__" not in attrs:
            attrs["__slots__"] = Controller.__slots__
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
        Returns the controller (subclass of :class:`.PLMObjectController`)
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
                from openPLM.plmapp.controllers.plmobject import PLMObjectController
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

class Controller(object):
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

    __metaclass__ = MetaController
    __slots__ = ("object", "_user", "_histo", "_pending_mails", "_mail_blocked",
            "__permissions", "__histo")

    HISTORY = models.AbstractHistory

    def __init__(self, obj, user, block_mails=False, no_index=False):
        self._mail_blocked = block_mails
        self._pending_mails = deque()
        self._user = user
        # variable to store attribute changes
        self._histo = ""
        # cache for permissions (dict(role->bool))
        self.__permissions = {}
        self.object = obj
        if no_index:
            obj.no_index = True

    @classmethod
    def load(cls, type, reference, revision, user):
        raise NotImplemented

    def __setattr__(self, attr, value):
        # we override this method to make it to modify *object* directly
        # if we modify *object*, we records the modification in **_histo*
        if hasattr(self, "object") and hasattr(self.object, attr) and \
           not attr in type(self).__slots__:
            obj = object.__getattribute__(self, "object")
            old_value = getattr(obj, attr)
            setattr(obj, attr, value)
            mfield = obj._meta.get_field(attr)
            field = mfield.verbose_name.capitalize()
            if old_value != value:
                if getattr(mfield, "richtext", False):
                    # store a unified diff (shorter than storing both values)
                    message = u"{field}:\n".format(field=field)
                    diff = difflib.unified_diff(old_value.splitlines(), value.splitlines())
                    # skip the ---/+++ lines
                    message += u"\n".join(itertools.islice(diff, 3, None))
                else:
                    message = u"%(field)s : changes from '%(old)s' to '%(new)s'" % \
                        {"field" : field, "old" : old_value, "new" : value}
                self._histo += message + "\n"
        else:
            super(Controller, self).__setattr__(attr, value)

    def __getattr__(self, attr):
        # we override this method to get attributes from *object* directly
        if attr in type(self).__slots__:
            return object.__getattribute__(self, attr)
        else:
            obj = object.__getattribute__(self, "object")
            return getattr(obj, attr)

    def save(self, with_history=True):
        u"""
        Saves :attr:`object` and records its history in the database.
        If *with_history* is False, the history is not recorded.
        """
        self.object.save()
        if self._histo and with_history:
            self._save_histo("Modify", self._histo)
            self._histo = ""

    def _save_histo(self, action, details, blacklist=(), roles=(), users=()):
        """
        Records *action* with details *details* made by :attr:`_user` in
        on :attr:`object` in the user histories table.
        """
        h = self.HISTORY.objects.create(plmobject=self.object, action=action,
                                     details=details, user=self._user)
        if self._user not in users:
            blacklist += (self._user.email,)
        roles = [models.ROLE_OWNER] + list(roles)
        self._send_mail(send_histories_mail, self.object, roles, action, [h],
                self._user, blacklist, users)

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

        If the check succeeds, **True** is returned. Otherwise, if *raise_* is
        **True** (the default), a :exc:`.PermissionError` is raised and if
        *raise_* is **False**, **False** is returned.

        .. admonition:: Implementation details

            This method keeps a cache, so that you dont have to worry about
            multiple calls to this method.
        """

        if role in self.__permissions:
            ok = self.__permissions[role]
        else:
            ok = self.has_permission(role)
            self.__permissions[role] = ok
        if not ok and raise_:
            raise PermissionError("action not allowed for %s" % self._user)
        return ok

    def clear_permissions_cache(self):
        self.__permissions.clear()

    def has_permission(self, role):
        return False

    def check_contributor(self, user=None):
        """
        This method checks if *user* is a contributor. If not, it raises
        :exc:`.PermissionError`.

        If *user* is None (the default), :attr:`_user` is used.
        """

        if not user:
            user = self._user
        if not user.is_active:
            raise PermissionError(u"%s's account is inactive" % user)
        profile = user.profile
        if not (profile.is_contributor or profile.is_administrator):
            raise PermissionError(u"%s is not a contributor" % user)
        if profile.restricted:
            # should not be possible, but an admin may have done a mistake
            raise PermissionError(u"%s is not a contributor" % user)

    def check_editable(self):
        return True

    def block_mails(self):
        """
        Blocks mails sending. Call :meth:`unblock_mails` to send blocked mails.
        """
        self._mail_blocked = True

    def unblock_mails(self):
        """
        Unblock mails sending. This sends all previously blocked mails.
        """
        while self._pending_mails:
            mail = self._pending_mails.popleft()
            mail[0](*mail[1:])
        self._mail_blocked = False

    def _send_mail(self, func, *args):
        if self._mail_blocked:
            mail = (func,) + args
            self._pending_mails.append(mail)
        else:
            func(*args)

    @property
    def histories(self):
        return self.HISTORY.objects.filter(plmobject=self.object).\
                order_by("-date").select_related("user")

