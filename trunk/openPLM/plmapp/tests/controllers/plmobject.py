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

from django.db import IntegrityError
from django.contrib.auth.models import User

from openPLM.plmapp.utils import level_to_sign_str
import openPLM.plmapp.exceptions as exc
import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PLMObjectController

from openPLM.plmapp.tests.base import BaseTestCase

class ControllerTest(BaseTestCase):
    CONTROLLER = PLMObjectController
    TYPE = "Part"
    DATA = {}


    def test_create(self):
        controller = self.create()
        self.assertEqual(controller.name, "")
        self.assertEqual(controller.type, self.TYPE)
        type_ = models.get_all_plmobjects()[self.TYPE]
        self.assertEqual(type(controller.object), type_) 
        obj = type_.objects.get(reference=controller.reference,
                revision=controller.revision, type=controller.type)
        self.assertEqual(obj.owner, self.user)
        self.assertEqual(obj.creator, self.user)
        models.PLMObjectUserLink.objects.get(plmobject=obj, user=self.user,
                role=models.ROLE_OWNER)
        self.failUnless(obj.is_editable)

    def test_create_error1(self):
        # empty reference
        self.assertRaises(ValueError, self.create, "")

    def test_create_error2(self):
        # empty revision
        def fail():
            controller = self.CONTROLLER.create("paer", self.TYPE, "",
                                            self.user, self.DATA)
        self.assertRaises(ValueError, fail)

    def test_create_error3(self):
        # empty reference
        def fail():
            controller = self.CONTROLLER.create("zeez", "", "a",
                                            self.user, self.DATA)
        self.assertRaises(ValueError, fail)

    def test_create_error4(self):
        # bad type
        def fail():
            controller = self.CONTROLLER.create("zee", "__", "a",
                                            self.user, self.DATA)
        self.assertRaises(ValueError, fail)
    
    def test_create_error5(self):
        # bad type : PLMObject
        def fail():
            controller = self.CONTROLLER.create("zee", "PLMOBject_", "a",
                                            self.user, self.DATA)
        self.assertRaises(ValueError, fail)
    
    def test_create_error6(self):
        """Create error test : user is not a contributor"""
        self.user.get_profile().is_contributor = False
        self.user.get_profile().save()
        def fail():
            controller = self.CONTROLLER.create("zee", "PLMOBject_", "a",
                                            self.user, self.DATA)
        self.assertRaises(exc.PermissionError, fail)

    def test_keys(self):
        controller = self.create("Part1")
        controller2 = self.create("Part2")
        self.assertRaises(IntegrityError, self.create, "Part1")

    def test_getattr(self):
        controller = self.create("Part1")
        self.assertEqual(controller.name, "")
        self.failUnless("name" in controller.attributes)
        self.assertEqual(controller.state.name, "draft")
        self.assertRaises(AttributeError, lambda: controller.unknown_attr)

    def test_setattr(self):
        controller = self.create("Part1")
        self.assertEqual(controller.name, "")
        controller.name = "a name"
        self.assertEqual(controller.name, "a name")
        controller.save()
        self.assertEqual(controller.name, "a name")

    def test_setattr_errors(self):
        controller = self.create("Part1")
        self.assertRaises(ValueError, setattr, controller, "owner", "error")
        self.assertRaises(ValueError, setattr, controller, "state", "error")
        self.assertRaises(ValueError, setattr, controller, "state", "draft")

    def test_revise(self):
        """
        Test :meth:`revise`
        """
        controller = self.create("Part1")
        rev = controller.revise("b")
        self.assertEqual(rev.revision, "b")
        def fail():
            controller.revise("b2")
        self.assertRaises(exc.RevisionError, fail)
        for attr in controller.get_modification_fields():
            self.assertEqual(getattr(controller, attr), getattr(rev, attr))

    def test_revise_official(self):
        ctrl = self.create("Part1")
        ctrl.state = ctrl.lifecycle.official_state
        ctrl.set_owner(self.cie)
        ctrl.save()
        self.failUnless(ctrl.is_revisable())
        rev = ctrl.revise("b")
        self.assertEqual(self.user, rev.owner)

    def test_revise_error1(self):
        "Revision : error : empty new revision"
        controller = self.create("Part1")
        self.assertRaises(exc.RevisionError, controller.revise, "")
    
    def test_revise_error2(self):
        "Revision : error : same revision name"
        controller = self.create("Part1")
        self.assertRaises(exc.RevisionError, controller.revise, "a")

    def test_set_owner(self):
        controller = self.create("Part1")
        user = User(username="user2")
        user.save()
        user.get_profile().is_contributor = True
        user.get_profile().save()
        controller.set_owner(user)
        self.assertEqual(controller.owner, user)

    def test_set_owner_error(self):
        controller = self.create("Part1")
        user = User(username="user2")
        user.save()
        self.assertRaises(exc.PermissionError, controller.set_owner, user)

    def test_set_sign1(self):
        controller = self.create("Part1")
        user = User(username="user2")
        user.save()
        user.get_profile().is_contributor = True
        user.get_profile().save()
        controller.set_signer(user, level_to_sign_str(0))
        link = models.PLMObjectUserLink.objects.get(role=level_to_sign_str(0),
                                             plmobject=controller.object)
        self.assertEqual(user, link.user)

    def test_set_sign_error1(self):
        """Test sign error : bad level"""
        controller = self.create("Part1")
        user = User(username="user2")
        user.save()
        user.get_profile().is_contributor = True
        user.get_profile().save()
        self.assertRaises(exc.PermissionError, controller.set_role, user,
                          level_to_sign_str(1664))

    def test_set_sign_error2(self):
        """Test sign error : user is not a contributor"""    
        controller = self.create("Part1")
        user = User(username="user2")
        user.save()
        self.assertRaises(exc.PermissionError, controller.set_role, user,
                          level_to_sign_str(0))

    def test_add_notified(self):
        controller = self.create("Part1")
        user = User(username="user2")
        user.save()
        controller.add_notified(user)
        models.PLMObjectUserLink.objects.get(user=user, plmobject=controller.object,
                                      role="notified")

    def test_remove_notified(self):
        controller = self.create("Part1")
        controller.add_notified(self.user)
        models.PLMObjectUserLink.objects.get(user=self.user, plmobject=controller.object,
                                      role="notified")
        controller.remove_notified(self.user)
        self.assertEqual(0, len(models.PLMObjectUserLink.objects.filter(
            plmobject=controller.object, role="notified")))

    def test_set_role(self):
        controller = self.create("Part1")
        user = User(username="user2")
        user.save()
        user.get_profile().is_contributor = True
        user.get_profile().save()
        controller.set_role(user, "owner")
        self.assertEqual(controller.owner, user)
        controller.set_role(self.user, "notified")
        models.PLMObjectUserLink.objects.get(user=self.user, plmobject=controller.object,
                                      role="notified")
        controller.set_role(user, level_to_sign_str(0))
        link = models.PLMObjectUserLink.objects.get(role=level_to_sign_str(0),
                                             plmobject=controller.object)
        self.assertEqual(user, link.user)

    def test_promote_error(self):
        """
        Tests that a :exc:`.PromotionError` is raised when 
        :meth:`.PLMObject.is_promotable` returns False.
        """
        controller = self.create("Part1")
        # fake function so that is_promotable returns False
        def always_false():
            return False
        controller.object.is_promotable = always_false
        self.assertRaises(exc.PromotionError, controller.promote)

