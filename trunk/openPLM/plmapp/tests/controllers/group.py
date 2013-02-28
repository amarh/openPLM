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
This module contains some tests for openPLM.
"""

from django.db import IntegrityError
from django.contrib.auth.models import User

from openPLM.plmapp.models import GroupInfo, Invitation, get_all_plmobjects
from openPLM.plmapp.controllers import GroupController
from openPLM.plmapp.forms import get_creation_form, get_user_formset

from openPLM.plmapp.tests.base import BaseTestCase

class GroupControllerTestCase(BaseTestCase):
    CONTROLLER = GroupController
    TYPE = "Group"
    DATA = {}

    def test_create(self):
        controller = self.CONTROLLER.create("Grp", "description",
                                            self.user, self.DATA)
        self.assertEqual(controller.name, "Grp")
        self.assertEqual(type(controller.object), get_all_plmobjects()[self.TYPE])
        obj = get_all_plmobjects()[self.TYPE].objects.get(name=controller.name)
        self.assertEqual(obj.owner, self.user)
        self.assertEqual(obj.creator, self.user)
        self.assertTrue(self.user.groups.filter(id=obj.id))

    def test_create_error1(self):
        # empty name
        def fail():
            controller = self.CONTROLLER.create("", "a", self.user, self.DATA)
        self.assertRaises(ValueError, fail)

    def test_keys(self):
        controller = self.CONTROLLER.create("Grp1", "a", self.user, self.DATA)
        controller2 = self.CONTROLLER.create("Grp2", "a", self.user, self.DATA)
        def fail():
            controller3 = self.CONTROLLER.create("Grp1", "a", self.user, self.DATA)
        self.assertRaises(IntegrityError, fail)

    def test_getattr(self):
        controller = self.CONTROLLER.create("Grp1", "a", self.user, self.DATA)
        self.assertEqual(controller.name, "Grp1")
        self.assertTrue("name" in controller.attributes)
        self.assertRaises(AttributeError, lambda: controller.unknown_attr)

    def test_setattr(self):
        controller = self.CONTROLLER.create("Grp1", "a", self.user, self.DATA)
        self.assertEqual(controller.description, "a")
        controller.description = "a description"
        self.assertEqual(controller.description, "a description")
        controller.save()
        self.assertEqual(controller.description, "a description")

    def test_setattr_errors(self):
        controller = self.CONTROLLER.create("Grp1", "a", self.user, self.DATA)
        self.assertRaises(ValueError, setattr, controller, "owner", "error")

    def test_add_user_accepted(self):
        user = User.objects.create(username="dede", email="dede@test")
        controller = self.CONTROLLER.create("Grp1", "a", self.user, self.DATA)
        controller.add_user(user)
        inv = Invitation.objects.get(guest=user, owner=self.user,
                                     group=controller.object)
        self.assertEquals(inv.state, Invitation.PENDING)
        self.assertFalse(inv.guest_asked)
        c2 = GroupController(controller.object, user)
        c2.accept_invitation(inv)
        self.assertTrue(user.groups.filter(id=controller.id))
        self.assertEqual(inv.state, Invitation.ACCEPTED)

    def test_add_user_refused(self):
        user = User.objects.create(username="dede", email="dede@test")
        controller = self.CONTROLLER.create("Grp1", "a", self.user, self.DATA)
        controller.add_user(user)
        inv = Invitation.objects.get(guest=user, owner=self.user,
                                     group=controller.object)
        self.assertEquals(inv.state, Invitation.PENDING)
        self.assertFalse(inv.guest_asked)
        c2 = GroupController(controller.object, user)
        c2.refuse_invitation(inv)
        self.assertFalse(user.groups.filter(id=c2.id))
        self.assertEqual(inv.state, Invitation.REFUSED)

    def test_create_from_form(self):
        form = get_creation_form(self.user, GroupInfo,
                {"name" : "grname", "description" :"desc" })
        gr = self.CONTROLLER.create_from_form(form, self.user)
        self.assertEqual(self.user.username, gr.owner.username)
        self.assertEqual("grname", gr.name)
        self.assertTrue(self.user.groups.get(id=gr.id))

    def test_update_users(self):
        controller = self.CONTROLLER.create("Grp1", "a", self.user, self.DATA)
        user = User.objects.create(username="dede", email="dede@test")
        user.groups.add(controller.object)
        user2 = User.objects.create(username="dede2", email="dede2@test")
        user2.groups.add(controller.object)
        controller.save()
        for u in (self.user, user, user2):
            u.save()
            self.assertTrue(u.groups.filter(id=controller.id))
        data = {
                'form-0-group': controller.id,
                'form-0-user': user.id,
                'form-0-delete' : 'on',
                'form-0-ORDER': '0',
                'form-1-group': controller.id,
                'form-1-user': user2.id,
                'form-1-ORDER': '1',
                'form-MAX_NUM_FORMS': '',
                'form-TOTAL_FORMS': 2, 
                'form-INITIAL_FORMS': 2,
                }
        formset = get_user_formset(controller, data)
        controller.update_users(formset)
        self.assertFalse(user.groups.filter(id=controller.id))
        self.assertTrue(user2.groups.filter(id=controller.id))
        self.assertTrue(self.user.groups.filter(id=controller.id))


