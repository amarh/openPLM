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


    def get_contributor(self, username="user2"):
        """ Returns a new contributor"""
        user = User(username="user2")
        user.save()
        user.get_profile().is_contributor = True
        user.get_profile().save()
        return user

    def promote_to_official(self, ctrl):
        ctrl.object.state = ctrl.lifecycle.official_state
        ctrl.set_owner(self.cie)
        self.assertTrue(ctrl.is_official)

    def promote_to_deprecated(self, ctrl):
        ctrl.object.state = ctrl.lifecycle.last_state
        ctrl.set_owner(self.cie)
        self.assertTrue(ctrl.is_deprecated)

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

    def test_revise_same_group(self):
        """
        Test that an user can revise an object if it belongs to its group.
        """
        controller = self.create("Part1")
        user = self.get_contributor()
        self.group.user_set.add(user)
        self.group.save()
        ctrl = self.CONTROLLER(controller.object, user)
        self.failUnless(ctrl.is_revisable())
        rev = ctrl.revise("b")
        self.assertEqual(user, rev.owner)

    def assertOneRevision(self, ctrl):
        count = models.PLMObject.objects.filter(reference=ctrl.reference).count()
        self.assertEqual(1, count)

    def test_revise_error_other_group(self):
        """
        Tests that an user who does not belong to the group cannot revise
        the object.
        """
        controller = self.create("Part1")
        user = self.get_contributor()
        ctrl = self.CONTROLLER(controller.object, user)
        self.failIf(ctrl.is_revisable())
        self.assertRaises(exc.PermissionError, ctrl.revise, "b")
        self.assertOneRevision(controller)

    def test_revise_error_empty_revision(self):
        "Revision : error : empty new revision"
        controller = self.create("Part1")
        self.assertRaises(exc.RevisionError, controller.revise, "")
        self.assertOneRevision(controller)
    
    def test_revise_error_same_revision(self):
        "Revision : error : same revision name"
        controller = self.create("Part1")
        self.assertRaises(exc.RevisionError, controller.revise, "a")
        self.assertOneRevision(controller)

    def test_revise_error_cancelled_object(self):
        """ Tests it is not possible to revise a cancelled object."""
        controller = self.create("Part1")
        controller.cancel()
        self.assertFalse(controller.is_revisable())
        self.assertRaises(exc.RevisionError, controller.revise, "n")
        self.assertOneRevision(controller)

    def test_revise_error_deprecated_object(self):
        """ Tests it is not possible to revise a deprecated object."""
        controller = self.create("Part1")
        controller.object.is_promotable = lambda: True
        controller.promote()
        controller.promote()
        self.assertFalse(controller.is_revisable())
        self.assertRaises(exc.RevisionError, controller.revise, "n")
        self.assertOneRevision(controller)

    def test_promote_to_official_revision_previous_is_official(self):
        """
        Tests that the promotion to the official status deprecates a
        previous official revision.
        """
        ctrl = self.create("Part1")
        ctrl.state = ctrl.lifecycle.official_state
        ctrl.set_owner(self.cie)
        ctrl.save()
        rev = ctrl.revise("b")
        rev.object.is_promotable = lambda: True
        self.assertEqual(self.user, rev.owner)
        rev.promote()
        self.assertTrue(rev.is_official)
        ctrl = rev.get_previous_revisions()[0]
        self.assertTrue(ctrl.is_deprecated)
        self.assertEqual(ctrl.owner, self.cie)

    def test_promote_to_official_revision_previous_is_deprecated(self):
        """
        Tests that the promotion of the official status with a
        previous deprecated revision.
        """
        ctrl = self.create("Part1")
        # deprecate ctrl after revising it
        rev = ctrl.revise("b")
        ctrl.state = ctrl.lifecycle.last_state
        ctrl.set_owner(self.cie)
        ctrl.save()
        rev.object.is_promotable = lambda: True
        self.assertEqual(self.user, rev.owner)
        rev.promote()
        self.assertTrue(rev.is_official)
        ctrl = rev.get_previous_revisions()[0]
        self.assertTrue(ctrl.is_deprecated)
        self.assertEqual(ctrl.owner, self.cie)

    def test_promote_to_official_revision_previous_is_editable(self):
        """
        Tests that the promotion to the official status cancels a
        previous editable revision.
        """
        ctrl = self.create("Part1")
        ctrl.save()
        rev = ctrl.revise("b")
        rev.object.is_promotable = lambda: True
        self.assertEqual(self.user, rev.owner)
        rev.promote()
        ctrl = rev.get_previous_revisions()[0]
        self.assertTrue(ctrl.is_cancelled)

    def test_set_owner(self):
        controller = self.create("Part1")
        user = self.get_contributor()
        controller.set_owner(user)
        self.assertEqual(controller.owner, user)

    def test_set_owner_error(self):
        """ set_owner: error: user is not a contributor"""
        controller = self.create("Part1")
        user = User(username="user2")
        user.save()
        self.assertRaises(exc.PermissionError, controller.set_owner, user)

    def test_set_owner_error2(self):
        """
        Tests that set_owner raises a ValueError if the new owner is the
        company and the object is editable.
        """
        controller = self.create("Part1")
        self.assertRaises(ValueError, controller.set_owner, self.cie)

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

    def test_promote_to_official_status(self):
        """
        Promotes a draft object to official status and checks that its owner
        is the company.
        """
        controller = self.create("Part1")
        controller.object.is_promotable = lambda: True
        controller.promote()
        self.assertEqual(self.cie, controller.owner)
        self.assertEqual("official", controller.state.name)
        self.assertTrue(controller.is_official)
        self.assertFalse(controller.is_editable)
        self.assertFalse(controller.is_deprecated)
        self.assertFalse(controller.is_cancelled)
        controller.check_readable()

    def test_promote_to_deprecated_status(self):
        """
        Promotes a draft object to deprecated status and checks that its owner
        is the company.
        """
        controller = self.create("Part1")
        controller.object.is_promotable = lambda: True
        # promote to official
        controller.promote()
        # promote to deprecated
        controller.promote()
        self.assertEqual(self.cie, controller.owner)
        self.assertEqual("deprecated", controller.state.name)
        self.assertFalse(controller.is_official)
        self.assertFalse(controller.is_editable)
        self.assertTrue(controller.is_deprecated)
        self.assertFalse(controller.is_cancelled)
        controller.check_readable()

    def check_cancelled_object(self, ctrl):
        """ Checks a cancelled plmobject."""
        self.assertTrue(ctrl.is_cancelled)
        self.assertEqual("cancelled", ctrl.state.name)
        self.assertEqual("cancelled", ctrl.lifecycle.name)
        self.assertEqual(self.cie, ctrl.owner)
        self.assertTrue(ctrl.check_readable())
        self.assertFalse(ctrl.is_revisable())
        self.assertFalse(ctrl.is_promotable())
        self.assertFalse(ctrl.is_editable)
        signers = ctrl.plmobjectuserlink_plmobject.filter(role__startswith=models.ROLE_SIGN)
        self.assertEqual(0, signers.count())

    def test_is_readable_owner(self):
        """
        Checks that the owner can read the object.
        """
        controller = self.create("P1")
        controller.check_readable()

    def test_is_readable_company(self):
        """
        Checks that the owner can read the object.
        """
        controller = self.create("P1")
        ctrl = self.CONTROLLER(controller.object, self.cie)
        ctrl.check_readable()

    def test_is_readable_group_ok(self):
        """
        Tests that an user who belongs to the object's group can see the
        object.
        """
        controller = self.create("P1")
        robert = models.User.objects.create_user("Robert", "pwd", "robert@p.txt")
        robert.groups.add(self.group)
        ctrl = self.CONTROLLER(controller.object, robert)
        ctrl.check_readable()

    def test_is_readable_group_invalid(self):
        """
        Tests that an user who does not belong to the object's group can not
        see the object.
        """
        controller = self.create("P1")
        robert = models.User.objects.create_user("Robert", "pwd", "robert@p.txt")
        ctrl = self.CONTROLLER(controller.object, robert)
        self.assertRaises(exc.PermissionError, ctrl.check_readable)

    def test_is_readable_not_editable(self):
        """
        Tests that an official or deprecated object is readable by every body.
        """
        controller = self.create("P1")
        controller.object.is_promotable = lambda: True
        robert = models.User.objects.create_user("Robert", "pwd", "robert@p.txt")
        robert.groups.add(self.group)
        ned = models.User.objects.create_user("Ned", "pwd", "ned@p.txt")
        for i in range(2):
            # i = 1 -> official, i = 2 -> deprecated
            controller.promote()
            for user in (self.user, self.cie, robert, ned):
                ctrl = self.CONTROLLER(controller.object, user)
                ctrl.check_readable()        
        
