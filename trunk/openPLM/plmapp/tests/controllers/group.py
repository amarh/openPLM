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
This module contains some tests for openPLM.
"""

import os
import datetime
from django.conf import settings
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files import File

from openPLM.plmapp.utils import *
from openPLM.plmapp.exceptions import *
from openPLM.plmapp.models import *
from openPLM.plmapp.controllers import *
from openPLM.plmapp.lifecycle import *
from openPLM.computer.models import *
from openPLM.office.models import *
from openPLM.cad.models import *

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
        self.assertTrue(obj in self.user.groupinfo_set.all())

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
        self.failUnless("name" in controller.attributes)
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
        self.failUnless(c2.object in user.groupinfo_set.all())
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
        self.failIf(c2.object in user.groupinfo_set.all())
        self.assertEqual(inv.state, Invitation.REFUSED)

