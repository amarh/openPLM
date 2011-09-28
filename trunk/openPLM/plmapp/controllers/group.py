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
This module contains a class called :class:`GroupController` which
provides a controller for :class:`~django.contrib.auth.models.Group`.
This class is similar to :class:`.PLMObjectController` but some methods
from :class:`.PLMObjectController` are not defined.
"""


import openPLM.plmapp.models as models
from openPLM.plmapp.controllers.base import Controller, permission_required

class GroupController(Controller):
    u"""
    Object used to manage a :class:`~django.contrib.auth.models.Group` and store his 
    modification in an history
    
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

    def __init__(self, obj, user):
        if hasattr(obj, "groupinfo"):
            obj = obj.groupinfo
        super(GroupController, self).__init__(obj, user)
   
    @classmethod
    def create(cls, name, description, user, data={}):
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


    def has_permission(self, role):
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
                if delete:
                    users.append(user)
            for user in users:
                user.groups.remove(group)
            self._save_histo("User removed", ", ".join((u.username for u in users)))
        
    @permission_required(role=models.ROLE_OWNER)
    def add_user(self, user):
        """
        Adds *user* to the group.
        """
        user.groups.add(self.object)
        # TODO send a more relevant mail
        self._save_histo("User added", user.username, users=(user,))

