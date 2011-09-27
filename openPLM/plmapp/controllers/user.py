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
This module contains a class called :class:`UserController` which
provides a controller for :class:`~django.contrib.auth.models.User`.
This class is similar to :class:`.PLMObjectController` but some methods
from :class:`.PLMObjectController` are not defined.
"""

from django.db.models.fields import FieldDoesNotExist
from django.utils.translation import ugettext_lazy as _

import openPLM.plmapp.models as models
from openPLM.plmapp.exceptions import PermissionError

class UserController(object):
    u"""
    Object used to manage a :class:`~django.contrib.auth.models.User` and store his 
    modification in an history
    
    :attributes:
        .. attribute:: object

            The :class:`~django.contrib.auth.models.User` managed by the controller

    :param obj: managed object
    :type obj: an instance of :class:`~django.contrib.auth.models.User`
    :param user: user who modify *obj*
    :type user: :class:`~django.contrib.auth.models.User` 

    .. note::
        This class does not inherit from :class:`.PLMObjectController`.

    """

    def __init__(self, obj, user):
        self.object = obj
        self._user = user
        self.__histo = ""
        self.creator = user
        self.owner = user
        self.mtime = obj.last_login
        self.ctime = obj.date_joined

    def get_verbose_name(self, attr_name):
        """
        Returns a verbose name for *attr_name*.

        Example::

            >>> ctrl.get_verbose_name("ctime")
            u'date of creation'
        """

        try:
            item = unicode(self.object._meta.get_field(attr_name).verbose_name)
        except FieldDoesNotExist:
            names = {"mtime" : _("date of last modification"),
                     "ctime" : _("date of creation"),
                     "rank" : _("role in PLM"),
                     "creator" : _("creator"),
                     "owner" : _("owner")}
            item = names.get(attr_name, attr_name)
        return item

    def update_from_form(self, form):
        u"""
        Updates :attr:`object` from data of *form*
        
        This method raises :exc:`ValueError` if *form* is invalid.
        """
        if form.is_valid():
            need_save = False
            for key, value in form.cleaned_data.iteritems():
                if key not in ["username"]:
                    setattr(self, key, value)
                    need_save = True
            if need_save:
                self.save()
        else:
            raise ValueError("form is invalid")

    def __setattr__(self, attr, value):
        # we override this method to make it to modify *object* directly
        # (or its profile)
        # if we modify *object*, we records the modification in **__histo*
        if hasattr(self, "object"):
            obj = object.__getattribute__(self, "object")
            profile = obj.get_profile()
        else:
            obj = None
        if obj and (hasattr(obj, attr) or hasattr(profile, attr)) and \
           not attr in self.__dict__:
            obj2 = obj if hasattr(obj, attr) else profile
            old_value = getattr(obj2, attr)
            setattr(obj2, attr, value)
            # since x.verbose_name is a proxy methods, we need to get a real
            # unicode object (with capitalize)
            field = obj2._meta.get_field(attr).verbose_name.capitalize()
            if old_value != value:
                message = "%(field)s : changes from '%(old)s' to '%(new)s'" % \
                        {"field" : field, "old" : old_value, "new" : value}
                self.__histo += message + "\n"
        else:
            super(UserController, self).__setattr__(attr, value)

    def __getattr__(self, attr):
        # we override this method to get attributes from *object* directly
        # (or its profile)
        obj = object.__getattribute__(self, "object")
        profile = obj.get_profile()
        if hasattr(self, "object") and hasattr(obj, attr) and \
           not attr in self.__dict__:
            return getattr(obj, attr)
        elif hasattr(profile, attr) and not attr in self.__dict__:
            return getattr(profile, attr)
        else:
            return object.__getattribute__(self, attr)

    def save(self, with_history=True):
        u"""
        Saves :attr:`object` and records its history in the database.
        If *with_history* is False, the history is not recorded.
        """
        self.object.save()
        self.object.get_profile().save()
        if self.__histo and with_history:
            self._save_histo("Modify", self.__histo) 
            self.__histo = ""

    def _save_histo(self, action, details):
        """
        Records *action* with details *details* made by :attr:`_user` in
        on :attr:`object` in the user histories table.
        """
        models.UserHistory.objects.create(plmobject=self.object, action=action,
                                     details=details, user=self._user)

    def get_object_user_links(self):
        """
        Returns all :class:`.Part` attached to :attr:`object`.
        """
        return self.plmobjectuserlink_user.order_by("plmobject")

    def delegate(self, user, role):
        """
        Delegates role *role* to *user*.
        
        Possible values for *role* are:
            ``'notified``
                valid for all users
            ``'owner'``
                valid only for contributors and administrators
            :samp:``'sign_{x}_level'``
                valid only for contributors and administrators
            ``'sign*'``
                valid only for contributors and administrators, means all sign
                roles that :attr:`object` has.
        
        :raise: :exc:`.PermissionError` if *user* can not have the role *role*
        :raise: :exc:`ValueError` if *user* is :attr:`object`
        """
        if user == self.object:
            raise ValueError("Bad delegatee (self)")
        if user.get_profile().is_viewer and role != 'notified':
            raise PermissionError("%s can not have role %s" % (user, role))
        if self.object.get_profile().is_viewer and role != 'notified':
            raise PermissionError("%s can not have role %s" % (self.object, role))
        if role == "sign*":
            qset = models.PLMObjectUserLink.objects.filter(user=self.object,
                        role__startswith="sign_").only("role")
            roles = set(link.role for link in qset)
        else:
            roles = [role]
        for r in roles:
            models.DelegationLink.objects.get_or_create(delegator=self.object,
                        delegatee=user, role=r)
        details = "%(delegator)s delegates the role %(role)s to %(delegatee)s"
        details = details % dict(role=role, delegator=self.object,
                                 delegatee=user)
        self._save_histo(models.DelegationLink.ACTION_NAME, details)

    def remove_delegation(self, delegation_link):
        """
        Removes a delegation (*delegation_link*). The delegator must be 
        :attr:`object`, otherwise a :exc:`ValueError` is raised.
        """
        if delegation_link.delegator != self.object:
            raise ValueError("%s is not the delegator of %s" % (self.object, ValueError))
        details = "%(delegator)s removes his delegation for the role %(role)s to %(delegatee)s"
        details = details % dict(role=delegation_link.role, delegator=self.object,
                                 delegatee=delegation_link.delegatee)
        self._save_histo(models.DelegationLink.ACTION_NAME, details)
        delegation_link.delete()
        
    def get_user_delegation_links(self):
        """
        Returns all delegatees of :attr:`object`.
        """
        return self.delegationlink_delegator.order_by("role")

