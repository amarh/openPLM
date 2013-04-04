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
from django.utils import timezone

from openPLM.plmapp.utils import level_to_sign_str
import openPLM.plmapp.exceptions as exc
import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PLMObjectController, UserController

from openPLM.plmapp.tests.base import BaseTestCase

class ControllerTest(BaseTestCase):
    CONTROLLER = PLMObjectController
    TYPE = "Part"
    DATA = {}

    def promote_to_official(self, ctrl):
        ctrl.object.state = ctrl.lifecycle.official_state
        ctrl.set_owner(self.cie, True)
        self.assertTrue(ctrl.is_official)

    def promote_to_deprecated(self, ctrl):
        ctrl.object.state = ctrl.lifecycle.last_state
        ctrl.set_owner(self.cie, True)
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
        models.PLMObjectUserLink.current_objects.get(plmobject=obj, user=self.user,
                role=models.ROLE_OWNER)
        self.assertTrue(obj.is_editable)

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
        self.user.profile.is_contributor = False
        self.user.profile.save()
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
        self.assertTrue("name" in controller.attributes)
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
        self.promote_to_official(ctrl)
        self.assertTrue(ctrl.is_revisable())
        rev = ctrl.revise("b")
        self.assertEqual(self.user, rev.owner)

    def test_revise_same_group(self):
        """
        Test that a user can revise an object if it belongs to its group.
        """
        controller = self.create("Part1")
        user = self.get_contributor()
        self.group.user_set.add(user)
        self.group.save()
        ctrl = self.CONTROLLER(controller.object, user)
        self.assertTrue(ctrl.is_revisable())
        rev = ctrl.revise("b")
        self.assertEqual(user, rev.owner)

    def assertOneRevision(self, ctrl):
        count = models.PLMObject.objects.filter(reference=ctrl.reference).count()
        self.assertEqual(1, count)

    def test_revise_error_other_group(self):
        """
        Tests that a user who does not belong to the group cannot revise
        the object.
        """
        controller = self.create("Part1")
        user = self.get_contributor()
        user.groups.remove(self.group)
        ctrl = self.CONTROLLER(controller.object, user)
        self.assertFalse(ctrl.is_revisable())
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
        self.promote_to_deprecated(controller)
        self.assertFalse(controller.is_revisable())
        self.assertRaises(exc.RevisionError, controller.revise, "n")
        self.assertOneRevision(controller)

    def test_promote_to_official_revision_previous_is_official(self):
        """
        Tests that the promotion to the official status deprecates a
        previous official revision.
        """
        ctrl = self.create("Part1")
        self.promote_to_official(ctrl)
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

    def test_set_owner_error_not_in_group(self):
        controller = self.create("Part1")
        user = self.get_contributor()
        user.groups.remove(self.group)
        self.assertRaises(exc.PermissionError, controller.set_owner, user)

    def test_add_signer(self):
        controller = self.create("Part1")
        user = self.get_contributor()
        controller.add_signer(user, level_to_sign_str(0))
        self.assertEqual(2, len(controller.get_current_signers()))

    def test_add_sign_error1(self):
        """Test sign error : bad level"""
        controller = self.create("Part1")
        user = self.get_contributor()
        for i in (2, 3, 1664):
            self.assertRaises(ValueError, controller.add_signer, user,
                          level_to_sign_str(i))

    def test_add_sign_error_already_signer(self):
        """Test sign error : bad level"""
        controller = self.create("Part1")
        user = self.get_contributor()
        self.assertRaises(IntegrityError, controller.add_signer, self.user,
                          level_to_sign_str(0))

    def test_replace_sign_error1(self):
        """Test replace signer error : bad level"""
        controller = self.create("Part1")
        user = self.get_contributor()
        self.assertRaises(ValueError, controller.replace_signer,
                self.user, user, level_to_sign_str(1789))

    def test_set_sign_error2(self):
        """Test sign error : user is not a contributor"""
        controller = self.create("Part1")
        user = User(username="user2")
        user.save()
        user.groups.add(controller.group)
        self.assertRaises(exc.PermissionError, controller.set_role, user,
                          level_to_sign_str(0))

    def test_add_signer_error_approved(self):
        controller = self.create("Part1")
        user = self.get_contributor()
        controller.add_signer(user, level_to_sign_str(0))
        controller.object.is_promotable = lambda: True
        controller.approve_promotion()
        user2 = self.get_contributor("toto")
        self.assertRaises(exc.PermissionError, controller.add_signer,
                user2, level_to_sign_str(0))
        self.assertFalse(controller.users.filter(user=user2))

    def test_remove_signer_error_approved(self):
        controller = self.create("Part1")
        user = self.get_contributor()
        controller.add_signer(user, level_to_sign_str(0))
        controller.object.is_promotable = lambda: True
        controller.approve_promotion()
        self.assertRaises(exc.PermissionError, controller.remove_signer,
                user, level_to_sign_str(0))
        self.assertTrue(controller.users.now().filter(user=user).exists())

    def test_remove_signer_error_one_signer(self):
        controller = self.create("Part1")
        self.assertRaises(exc.PermissionError, controller.remove_signer,
                self.user, level_to_sign_str(0))
        self.assertTrue(controller.users.now().filter(user=self.user).exists())

    def test_remove_signer(self):
        controller = self.create("Part1")
        user = self.get_contributor()
        controller.add_signer(user, level_to_sign_str(0))
        controller.remove_signer(self.user, level_to_sign_str(0))
        controller.object.is_promotable = lambda: True
        self.assertRaises(exc.PermissionError, controller.approve_promotion)

    def test_replace_signer_error_approved(self):
        controller = self.create("Part1")
        user = self.get_contributor()
        controller.add_signer(user, level_to_sign_str(0))
        controller.object.is_promotable = lambda: True
        controller.approve_promotion()
        user2 = self.get_contributor("toto")
        self.assertRaises(exc.PermissionError, controller.replace_signer,
                user, user2, level_to_sign_str(0))
        self.assertRaises(exc.PermissionError, controller.replace_signer,
                self.user, user2, level_to_sign_str(0))
        self.assertFalse(controller.users.filter(user=user2))
        self.assertFalse(controller.users.filter(user=user2))

    def test_replace_signer(self):
        controller = self.create("Part1")
        user = self.get_contributor()
        controller.replace_signer(self.user, user, level_to_sign_str(0))
        controller.object.is_promotable = lambda: True
        self.assertEqual(list(controller.get_current_signers()), [user.id])
        self.assertRaises(exc.PermissionError, controller.approve_promotion)
        ctrl2 = self.CONTROLLER(controller.object, user)
        ctrl2.approve_promotion()
        self.assertEqual("official", controller.object.state.name)

    def test_add_signer_error_not_in_group(self):
        controller = self.create("Part1")
        user = self.get_contributor()
        user.groups.remove(self.group)
        self.assertRaises(exc.PermissionError, controller.set_role, user,
                          level_to_sign_str(0))

    def test_add_notified(self):
        controller = self.create("Part1")
        user = User(username="user2")
        user.save()
        user.groups.add(controller.group)
        controller.add_notified(user)
        models.PLMObjectUserLink.current_objects.get(user=user, plmobject=controller.object,
                                      role="notified")

    def test_add_notified_error_not_in_group(self):
        controller = self.create("Part1")
        user = self.get_contributor()
        user.groups.remove(self.group)
        self.assertRaises(exc.PermissionError, controller.add_notified, user)

    def test_remove_notified(self):
        controller = self.create("Part1")
        controller.add_notified(self.user)
        link = models.PLMObjectUserLink.current_objects.get(user=self.user, plmobject=controller.object,
                                      role="notified")
        ids = [link.id]
        t = timezone.now()
        controller.remove_notified(self.user)
        self.assertEqual(0, len(models.PLMObjectUserLink.current_objects.filter(
            plmobject=controller.object, role="notified")))
        self.assertNotEqual(None, models.PLMObjectUserLink.objects.get(id=link.id).end_time)
        # check it can again add self.user
        controller.add_notified(self.user)
        link = models.PLMObjectUserLink.current_objects.get(user=self.user, plmobject=controller.object,
                role="notified")
        self.assertNotEqual(ids[0], link.id)
        ids.append(link.id)
        self.assertEqual(set(ids), set(controller.users.filter(user=self.user,
             role="notified").values_list("id", flat=True)))
        # get the old link
        link = models.PLMObjectUserLink.objects.at(t).get(user=self.user, plmobject=controller.object,
                role="notified")
        self.assertEqual(ids[0], link.id)

    def test_set_role(self):
        controller = self.create("Part1")
        user = self.get_contributor()
        controller.set_role(user, "owner")
        self.assertEqual(controller.owner, user)
        controller.set_role(self.user, "notified")
        models.PLMObjectUserLink.current_objects.get(user=self.user, plmobject=controller.object,
                                      role="notified")
        controller.set_role(user, level_to_sign_str(0))
        users = models.PLMObjectUserLink.current_objects.filter(role=level_to_sign_str(0),
                             plmobject=controller.object).values_list("user", flat=True)
        self.assertTrue(user.id in users)
        self.assertTrue(self.user.id in users)

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
        self.assertRaises(exc.PromotionError, controller.approve_promotion)

    def test_promote_to_official_status(self):
        """
        Promotes a draft object to official status and checks that its owner
        is the company.
        """
        controller = self.create("Part1")
        controller.object.is_promotable = lambda: True
        controller.approve_promotion()
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

    def test_approve_promotion_two_signers(self):
        controller = self.create("Part1")
        controller.object.is_promotable = lambda: True
        user = self.get_contributor("gege")
        models.PLMObjectUserLink.objects.create(user=user, plmobject=controller.object,
                role=level_to_sign_str(0))
        draft_state = controller.state
        self.assertFalse(controller.is_last_promoter())
        controller.approve_promotion()
        self.assertFalse(controller.can_approve_promotion())
        self.assertEqual(draft_state, controller.state)
        ctrl2 = self.CONTROLLER(controller.object, user)
        self.assertTrue(ctrl2.is_last_promoter())
        ctrl2.approve_promotion()
        obj = models.PLMObject.objects.get(id=controller.id)
        self.assertEqual(self.cie, obj.owner)
        self.assertEqual("official", obj.state.name)

    def test_approve_promotion_delegator(self):
        controller = self.create("Part1")
        controller.object.is_promotable = lambda: True
        user = self.get_contributor("gege")
        UserController(self.user, self.user).delegate(user, level_to_sign_str(0))
        ctrl2 = self.CONTROLLER(controller.object, user)
        self.assertTrue(ctrl2.is_last_promoter())
        ctrl2.approve_promotion()
        obj = models.PLMObject.objects.get(id=controller.id)
        self.assertEqual(self.cie, obj.owner)
        self.assertEqual("official", obj.state.name)

    def test_approve_promotion_delegator_and_signer(self):
        controller = self.create("Part1")
        controller.object.is_promotable = lambda: True
        user = self.get_contributor("gege")
        UserController(self.user, self.user).delegate(user, level_to_sign_str(0))
        models.PLMObjectUserLink.objects.create(user=user, plmobject=controller.object,
                role=level_to_sign_str(0))
        ctrl2 = self.CONTROLLER(controller.object, user)
        self.assertTrue(ctrl2.is_last_promoter())
        ctrl2.approve_promotion()
        obj = models.PLMObject.objects.get(id=controller.id)
        self.assertEqual(self.cie, obj.owner)
        self.assertEqual("official", obj.state.name)

    def test_approve_promotion_signer_then_delegator(self):
        controller = self.create("Part1")
        controller.object.is_promotable = lambda: True
        user = self.get_contributor("gege")
        models.PLMObjectUserLink.objects.create(user=user, plmobject=controller.object,
                role=level_to_sign_str(0))
        ctrl2 = self.CONTROLLER(controller.object, user)
        self.assertFalse(ctrl2.is_last_promoter())
        ctrl2.approve_promotion()
        self.assertFalse(ctrl2.can_approve_promotion())
        UserController(self.user, self.user).delegate(user, level_to_sign_str(0))
        self.assertTrue(ctrl2.can_approve_promotion())
        self.assertTrue(ctrl2.is_last_promoter())
        ctrl2.approve_promotion()
        obj = models.PLMObject.objects.get(id=controller.id)
        self.assertEqual(self.cie, obj.owner)
        self.assertEqual("official", obj.state.name)

    def test_approve_promotion_two_delegators(self):
        controller = self.create("Part1")
        controller.object.is_promotable = lambda: True
        user = self.get_contributor("gege")
        UserController(self.user, self.user).delegate(user, level_to_sign_str(0))
        user2 = self.get_contributor("misterpink")
        UserController(user2, user2).delegate(user, level_to_sign_str(0))
        models.PLMObjectUserLink.objects.create(user=user2, plmobject=controller.object,
                role=level_to_sign_str(0))
        ctrl2 = self.CONTROLLER(controller.object, user)
        self.assertTrue(ctrl2.is_last_promoter())
        ctrl2.approve_promotion()
        obj = models.PLMObject.objects.get(id=controller.id)
        self.assertEqual(self.cie, obj.owner)
        self.assertEqual("official", obj.state.name)

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
        signers = ctrl.users.now().filter(role__startswith=models.ROLE_SIGN)
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
        Tests that a user who belongs to the object's group can see the
        object.
        """
        controller = self.create("P1")
        robert = models.User.objects.create_user("Robert", "pwd", "robert@p.txt")
        robert.groups.add(self.group)
        ctrl = self.CONTROLLER(controller.object, robert)
        ctrl.check_readable()

    def test_is_readable_group_invalid(self):
        """
        Tests that a user who does not belong to the object's group can not
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
        controller.object.lifecycle = models.Lifecycle.objects.get(name="draft_proposed_official_deprecated")
        controller.object.save()
        controller.add_signer(self.user, level_to_sign_str(2))
        controller.object.is_promotable = lambda: True
        robert = models.User.objects.create_user("Robert", "pwd", "robert@p.txt")
        robert.groups.add(self.group)
        ned = models.User.objects.create_user("Ned", "pwd", "ned@p.txt")

        for i in range(2):
            ctrl = self.CONTROLLER(controller.object, ned)
            self.assertRaises(exc.PermissionError, ctrl.check_readable)
            for user in (self.user, self.cie, robert):
                ctrl = self.CONTROLLER(controller.object, user)
                ctrl.check_readable()
            controller.promote()

        for i in range(2):
            # i = 0 -> official, i = 1 -> deprecated
            for user in (self.user, self.cie, robert, ned):
                ctrl = self.CONTROLLER(controller.object, user)
                ctrl.check_readable()
            if i == 0:
                controller.promote()

    # publication tests

    def assertPublish(self, ctrl):
        self.assertTrue(ctrl.check_publish())
        self.assertTrue(ctrl.can_publish())
        ctrl.publish()
        self.assertTrue(ctrl.published)

    def assertPublishError(self, ctrl):
        self.assertRaises(exc.PermissionError, ctrl.check_publish)
        self.assertFalse(ctrl.can_publish())
        self.assertRaises(exc.PermissionError, ctrl.publish)
        self.assertFalse(ctrl.published)

    def test_publish_not_official(self):
        """ Tests that a non official object can *not* be published."""
        controller = self.create("P1")
        publisher = self.get_publisher()
        ctrl = self.CONTROLLER(controller.object, publisher)
        self.assertPublishError(ctrl)

    def test_publish_official(self):
        """ Tests that an official object can be published."""
        controller = self.create("P1")
        self.promote_to_official(controller)
        publisher = self.get_publisher()
        ctrl = self.CONTROLLER(controller.object, publisher)
        self.assertPublish(ctrl)

    def test_publish_deprecated(self):
        """ Tests that a deprecated object can *not* be published."""
        controller = self.create("P1")
        self.promote_to_deprecated(controller)
        publisher = self.get_publisher()
        ctrl = self.CONTROLLER(controller.object, publisher)
        self.assertPublishError(ctrl)

    def test_publish_published(self):
        """ Tests that a published object can *not* be published."""
        controller = self.create("P1")
        self.promote_to_official(controller)
        publisher = self.get_publisher()
        ctrl = self.CONTROLLER(controller.object, publisher)
        self.assertPublish(ctrl)
        self.assertFalse(ctrl.can_publish())
        self.assertRaises(ValueError, ctrl.check_publish)
        self.assertRaises(ValueError, ctrl.publish)

    def test_publish_not_publisher(self):
        """ Tests that only a publisher can publish."""
        controller = self.create("P1")
        self.promote_to_official(controller)
        self.assertFalse(controller._user.profile.can_publish)
        self.assertPublishError(controller)

    def test_publish_not_in_group(self):
        """ Tests that only a publisher who does not belongs to the objects
        group can *not* publish."""
        controller = self.create("P1")
        self.promote_to_official(controller)
        publisher = self.get_publisher()
        publisher.groups.remove(self.group)
        ctrl = self.CONTROLLER(controller.object, publisher)
        self.assertPublishError(ctrl)

    # unpublication tests

    def get_published_ctrl(self):
        controller = self.create("P1")
        controller.object.published = True
        controller.object.save()
        return controller

    def assertUnpublish(self, ctrl):
        self.assertTrue(ctrl.check_unpublish())
        self.assertTrue(ctrl.can_unpublish())
        ctrl.unpublish()
        self.assertFalse(ctrl.published)

    def assertUnpublishError(self, ctrl):
        self.assertRaises(exc.PermissionError, ctrl.check_unpublish)
        self.assertFalse(ctrl.can_unpublish())
        self.assertRaises(exc.PermissionError, ctrl.unpublish)
        self.assertTrue(ctrl.published)

    def test_unpublish_not_official(self):
        """ Tests that a non official published object can be unpublished."""
        publisher = self.get_publisher()
        ctrl = self.CONTROLLER(self.get_published_ctrl().object, publisher)
        self.assertUnpublish(ctrl)

    def test_unpublish_official(self):
        """ Tests that an official published object can be unpublished."""
        controller = self.get_published_ctrl()
        self.promote_to_official(controller)
        publisher = self.get_publisher()
        ctrl = self.CONTROLLER(controller.object, publisher)
        self.assertUnpublish(ctrl)

    def test_unpublish_deprecated(self):
        """ Tests that a deprecated published object can be unpublished."""
        controller = self.get_published_ctrl()
        self.promote_to_deprecated(controller)
        publisher = self.get_publisher()
        ctrl = self.CONTROLLER(controller.object, publisher)
        self.assertUnpublish(ctrl)

    def test_unpublish_published(self):
        """ Tests that an unpublished object can *not* be unpublished."""
        controller = self.create("P1")
        publisher = self.get_publisher()
        ctrl = self.CONTROLLER(controller.object, publisher)
        self.assertFalse(ctrl.can_unpublish())
        self.assertRaises(ValueError, ctrl.check_unpublish)
        self.assertRaises(ValueError, ctrl.unpublish)

    def test_unpublish_not_publisher(self):
        """ Tests that only a publisher can unpublish."""
        controller = self.get_published_ctrl()
        self.assertFalse(controller._user.profile.can_publish)
        self.assertUnpublishError(controller)

    def test_unpublish_not_in_group(self):
        """ Tests that only a publisher who does not belongs to the objects
        group can *not* unpublish."""
        controller = self.get_published_ctrl()
        publisher = self.get_publisher()
        publisher.groups.remove(self.group)
        ctrl = self.CONTROLLER(controller.object, publisher)
        self.assertUnpublishError(ctrl)

    # cancel test

    def get_created_ctrl(self):
        controller = self.create("P1")
        controller.object.save()
        return controller

    def assertCancel(self,ctrl):
        self.assertTrue(ctrl.check_cancel())
        self.assertTrue(ctrl.can_cancel())
        ctrl.cancel()
        self.check_cancelled_object(ctrl)

    def assertCancelError(self, ctrl):
        self.assertRaises(exc.PermissionError, ctrl.check_cancel)
        self.assertRaises(exc.PermissionError, ctrl.check_cancel)
        self.assertRaises(exc.PermissionError, ctrl.check_cancel)
        self.assertRaises(exc.PermissionError, ctrl.check_cancel)
        self.assertRaises(exc.PermissionError, ctrl.check_cancel)
        res = not ctrl.is_draft
        res = res or len(ctrl.get_all_revisions()) > 1
        res = res or not ctrl.check_permission("owner",raise_=False)
        return res

    def test_cancel_draft(self):
        """ Tests that a draft object with only one revision can be cancelled"""
        controller = self.get_created_ctrl()
        self.assertCancel(controller)

    def test_cancel_not_draft(self):
        """ Tests that a non-draft object can *not* be cancelled"""
        controller = self.get_created_ctrl()
        state = controller.object.state
        lifecycle = controller.object.lifecycle
        lcl = lifecycle.to_states_list()
        new_state = lcl.next_state(state.name)
        controller.object.state = models.State.objects.get_or_create(name=new_state)[0]
        controller.object.save()
        self.assertFalse(controller.is_draft)
        self.assertCancelError(controller)

    def test_cancel_official(self):
        """ Tests that an official object can *not* be cancelled (even by its creator/owner)"""
        controller = self.get_created_ctrl()
        self.promote_to_official(controller)
        self.assertCancelError(controller)

    def test_cancel_deprecated(self):
        """ Tests that a deprecated object can *not* be cancelled"""
        controller = self.get_created_ctrl()
        self.promote_to_deprecated(controller)
        self.assertCancelError(controller)

    def test_cancel_cancelled(self):
        """ Tests that a cancelled object can *not* be cancelled"""
        controller = self.get_created_ctrl()
        controller.cancel()
        self.assertCancelError(controller)

    def test_cancel_not_owner(self):
        """ Tests that only a user who does not have owner rights on the object
        can not cancel it."""
        controller = self.get_created_ctrl()
        user = self.get_contributor()
        ctrl = self.CONTROLLER(controller.object, user)
        self.assertCancelError(ctrl)

    def test_cancel_owner(self):
        """ Tests that any user with owner rights on the object
        can cancel it."""
        controller = self.get_created_ctrl()
        user = self.get_contributor()
        controller.set_owner(user)
        ctrl = self.CONTROLLER(controller.object, user)
        self.assertCancel(ctrl)

    def test_cancel_revised(self):
        """Tests that an object (here a draft) with more than one revision can *not* be cancelled"""
        controller = self.get_created_ctrl()
        ctrl = controller.revise("b")
        self.assertCancelError(ctrl)

    # clone test
    def getDataCloning(self,ctrl, ref=None, rev=None):
        if ref is None:
            ref = "cloned_01"
        if rev is None:
            rev = "a"
        data={}
        for attr in ctrl.get_creation_fields():
            data[attr]=getattr(ctrl,attr)
        data.update({
            "reference" : ref,
            "revision" : rev,
        })
        return data

    def assertClone(self, ctrl, data):
        self.assertTrue(ctrl.can_clone())
        new_ctrl = ctrl.create(data["reference"], ctrl.object.type , data["revision"], ctrl._user,
                    data, block_mails=False, no_index=False)
        res = False
        for attr in ctrl.get_creation_fields():
            self.assertTrue(attr in new_ctrl.get_creation_fields())
            res = res or getattr(ctrl, attr) == getattr(new_ctrl, attr)
        self.assertTrue(res)
        return new_ctrl

    def test_clone_non_readable(self):
        """Tests that a user can *not* clone an object
        that he should not be able to read"""
        group = models.GroupInfo(name="new_grp", owner = self.cie, creator = self.cie, description="new_grp")
        group.save()
        self.DATA.update({"group":group})
        ctrl = self.get_created_ctrl()
        ctrl.set_owner(self.cie, True)
        self.assertRaises(exc.PermissionError, ctrl.check_readable)
        self.assertRaises(exc.PermissionError, ctrl.clone, None, ctrl._user, [],[])

    def test_clone_by_non_contributor(self):
        """ Tests that a non contributor can not clone
        an object."""
        ctrl= self.get_created_ctrl()
        ctrl._user.profile.is_contributor = False
        self.assertRaises(exc.PermissionError, ctrl.check_contributor)
        self.assertRaises(exc.PermissionError, ctrl.clone, None, ctrl._user, [],[])
