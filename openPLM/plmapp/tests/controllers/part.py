#############################################################################
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

from django.utils import timezone
import itertools

from openPLM.plmapp.controllers import PLMObjectController, PartController, \
        DocumentController
import openPLM.plmapp.exceptions as exc
import openPLM.plmapp.models as models
from openPLM.plmapp.lifecycle import LifecycleList

from openPLM.plmapp.tests.controllers.plmobject import ControllerTest


class PartControllerTest(ControllerTest):
    TYPE = "Part"
    CONTROLLER = PartController

    def setUp(self):
        super(PartControllerTest, self).setUp()
        self.controller = self.create("aPart1")
        self.controller2 = self.create("aPart2")
        self._controller3 = None
        self.document = DocumentController.create("Doc1", "Document", "a",
                self.user, self.DATA, True, True)
        self.document.state = self.document.lifecycle.official_state
        self.document.object.save()
        for ctrl in (self.controller, self.controller2):
            ctrl.attach_to_document(self.document)

    @property
    def controller3(self):
        if self._controller3 is None:
            self._controller3 = self.create("aPart3")
        return self._controller3

    def add_child(self, qty=10, order=15, unit="-"):
        """ Adds controller2 to controller."""
        return self.controller.add_child(self.controller2, qty, order, unit)

    def test_add_child(self):
        """ Tests the addition of a child and checks that the BOM is
        consistent."""

        children = self.controller.get_children()
        self.assertEqual(len(children), 0)
        self.controller.precompute_can_add_child2()
        self.assertTrue(self.controller.can_add_child2(self.controller2.object))
        self.add_child()
        children = self.controller.get_children()
        self.assertEqual(len(children), 1)
        level, link = children[0]
        self.assertEqual(level, 1)
        self.assertEqual(link.child.pk, self.controller2.object.pk)
        self.assertEqual(link.parent.pk, self.controller.object.pk)
        self.assertEqual(link.quantity, 10)
        self.assertEqual(link.order, 15)

    def test_add_child_error_invalid_quantity(self):
        """
        Tests that add_child raises a ValueError if the quantity is invalid.
        """
        def fail():
            self.add_child(qty=-10)
        self.assertRaises(ValueError, fail)
        self.assertFalse(self.controller.get_children())

    def test_add_child_error_invalid_order(self):
        """
        Tests that add_child raises a ValueError if the order is invalid.
        """
        def fail():
            self.add_child(order=-15)
        self.assertRaises(ValueError, fail)
        self.assertFalse(self.controller.get_children())

    def test_add_child_error_child_is_parent(self):
        """
        Tests that add_child raises a ValueError if the given child
        is a parent.
        """
        self.controller2.add_child(self.controller, 10, 15)
        def fail():
            self.add_child()
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(self.controller2.object))
        self.assertRaises(ValueError, fail)
        self.assertFalse(self.controller.get_children())

    def test_add_child_error_already_a_child(self):
        """
        Tests that add_child raises a ValueError if the given child
        is already a child.
        """
        self.controller.precompute_can_add_child2()
        self.assertTrue(self.controller.can_add_child2(self.controller2.object))
        self.add_child()
        def fail():
            self.add_child()
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(self.controller2.object))
        self.assertRaises(ValueError, fail)

    def test_add_child_error_child_is_document(self):
        """
        Tests that add_child raises a ValueError if the given child
        is a document.
        """
        def fail():
            doc = PLMObjectController.create("e", "Document", "1", self.user, self.DATA)
            self.controller.precompute_can_add_child2()
            self.assertFalse(self.controller.can_add_child2(doc))
            self.controller.add_child(doc, 10, 15)
        self.assertRaises(TypeError, fail)
        self.assertFalse(self.controller.get_children())

    def test_add_child_error_child_is_self(self):
        """
        Tests that add_child raises a ValueError if the given child
        is the controller.
        """
        def fail():
            self.controller.add_child(self.controller, 10, 15)
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(self.controller.object))
        self.assertRaises(ValueError, fail)
        self.assertFalse(self.controller.get_children())

    def test_add_child_error_not_owner(self):
        """
        Tests that only the owner can add a child.
        """
        user = self.get_contributor()
        user.groups.add(self.group)
        ctrl = self.CONTROLLER(self.controller.object, user)
        def fail():
            ctrl.add_child(self.controller2.object, 10, 15, "kg")
        ctrl.precompute_can_add_child2()
        self.assertFalse(ctrl.can_add_child2(self.controller2.object))
        self.assertRaises(exc.PermissionError, fail)
        self.assertFalse(self.controller.get_children())

    def test_add_child_error_official_status(self):
        """
        Tests that it is not possible to add a child to an official
        object.
        """
        self.controller.promote()
        ctrl = self.CONTROLLER(self.controller.object, self.controller.owner)
        def fail():
            ctrl.add_child(self.controller2.object, 10, 15, "m")
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(self.controller2.object))
        self.assertRaises(exc.PermissionError, fail)
        self.assertFalse(self.controller.get_children())

    def test_add_child_error_deprecated_child(self):
        """
        Tests that it is not possible to add a deprecated child.
        """
        self.controller2.promote()
        self.controller2.promote()
        def fail():
            self.add_child()
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(self.controller2.object))
        self.assertRaises(ValueError, fail)
        self.assertFalse(self.controller.get_children())

    def test_add_child_error_cancelled_child(self):
        """
        Tests that it is not possible to add a cancelled child.
        """
        self.controller.cancel()
        def fail():
            self.add_child()
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(self.controller2.object))
        self.assertRaises(exc.PermissionError, fail)
        self.assertFalse(self.controller.get_children())

    def test_add_child_error_cancelled(self):
        """
        Tests that it is not possible to add a child to a cancelled object.
        """
        self.controller.cancel()
        ctrl = self.CONTROLLER(self.controller.object, self.controller.owner)
        def fail():
            ctrl.add_child(self.controller2.object, 10, 15, "m")
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(self.controller2.object))
        self.assertRaises(exc.PermissionError, fail)
        self.assertFalse(self.controller.get_children())

    def _test_modify_child(self, new_qty, new_order, new_unit):
        self.add_child()
        self.controller.modify_child(self.controller2, new_qty, new_order,
                new_unit)
        children = self.controller.get_children()
        level, link = children[0]
        self.assertEqual(link.quantity, new_qty)
        self.assertEqual(link.order, new_order)
        self.assertEqual(link.unit, new_unit)

    def test_modify_child(self):
        """
        Tests the modification of a child link.
        """
        self._test_modify_child(3, 5, "kg")

    def test_modify_child_only_quantity(self):
        """
        Tests the modification of a child link. Only the quantity changes.
        """
        self._test_modify_child(3, 15, "-")

    def test_modify_child_only_order(self):
        """
        Tests the modification of a child link. Only the order changes.
        """
        self._test_modify_child(10, 25, "-")

    def test_modify_child_only_unit(self):
        """
        Tests the modification of a child link. Only the unit changes.
        """
        self._test_modify_child(10, 15, "m")

    def _test_modify_child_error(self, new_qty, new_order, new_unit):
        self.add_child()
        def fail():
            self.controller.modify_child(self.controller2, new_qty,
                    new_order, new_unit)
        self.assertRaises(ValueError, fail)
        children = self.controller.get_children()
        level, link = children[0]
        self.assertEqual(link.quantity, 10)
        self.assertEqual(link.order, 15)
        self.assertEqual(link.unit, "-")

    def test_modify_child_error_invalid_quantity(self):
        """
        Tests the modification of a child link. The quantity is invalid.
        """
        self._test_modify_child_error(-3, 15, "-")

    def test_modify_child_error_invalid_order(self):
        """
        Tests the modification of a child link. The order is invalid.
        """
        self._test_modify_child_error(10, -15, "-")

    def test_modify_child_error_official_status(self):
        """
        Tests that it is not possible to modify a child of an official object.
        """
        self.add_child()
        self.controller2.promote()
        self.controller.promote()
        ctrl = self.CONTROLLER(self.controller.object, self.controller.owner)
        def fail():
            ctrl.add_child(self.controller2.object, 20, 25, "mm")
        self.assertRaises(exc.PermissionError, fail)
        children = self.controller.get_children()
        level, link = children[0]
        self.assertEqual(link.quantity, 10)
        self.assertEqual(link.order, 15)
        self.assertEqual(link.unit, "-")

    def test_delete_child(self):
        """
        Tests the deletion of a child link.
        """
        self.add_child()
        self.controller.delete_child(self.controller2)
        self.assertEqual(self.controller.get_children(), [])

    def test_delete_child_error_not_owner(self):
        """
        Tests that only the owner can delete a child link.
        """
        self.add_child()
        robert = self.get_contributor()
        robert.groups.add(self.group)
        ctrl = self.CONTROLLER(self.controller.object, robert)
        self.assertRaises(exc.PermissionError, ctrl.delete_child,
                self.controller2.object)
        self.assertEqual(1, len(self.controller.get_children()))

    def test_delete_child_error_official_status(self):
        """
        Tests that it is not possible to delete a child link of an offical
        part.
        """
        self.add_child()
        self.promote_to_official(self.controller)
        self.assertRaises(exc.PermissionError, self.controller.delete_child,
                self.controller2)
        self.assertEqual(1, len(self.controller.get_children()))

    def test_delete_child_error_deprecated_status(self):
        """
        Tests that it is not possible to delete a child link of a deprecated
        part.
        """
        self.add_child()
        self.promote_to_deprecated(self.controller)
        self.assertRaises(exc.PermissionError, self.controller.delete_child,
                self.controller2)
        self.assertEqual(1, len(self.controller.get_children()))

    def test_replace_child(self):
        link = self.add_child()
        self.controller.replace_child(link, self.controller3.object)
        children = self.controller.get_children(1)
        self.assertEqual(1, len(children))
        self.assertEqual(self.controller3.object.part, children[0].link.child)

    def test_replace_child_existing_link(self):
        l1 = self.controller.add_child(self.controller2.object, 10, 15)
        l2 = self.controller.add_child(self.controller3.object, 13, 35)
        self.controller.replace_child(l1, self.controller3.object)
        children = self.controller.get_children(1)
        self.assertEqual(1, len(children))
        link = children[0].link
        self.assertEqual(self.controller3.object.part, link.child)
        self.assertEqual(15, link.order)
        self.assertEqual(23, link.quantity)

    def test_replace_child_existing_link_error_invalid_unit(self):
        l1 = self.controller.add_child(self.controller2.object, 10, 15, "-")
        l2 = self.controller.add_child(self.controller3.object, 13, 35, "m")
        self.assertRaises(ValueError, self.controller.replace_child,
                l1, self.controller3.object)

    def test_get_children(self):
        controller4 = self.create("aPart4")
        self.controller.add_child(self.controller2, 10, 15)
        date = timezone.now()
        self.controller2.add_child(self.controller3, 10, 25)
        self.controller.add_child(controller4, 10, 35)
        self.controller2.object.is_promotable = lambda *args: True
        date2 = timezone.now()
        self.controller2.promote()
        controller4.add_child(self.controller2, 28, 51)
        wanted = [(1, self.controller2.object.pk),
                  (2, self.controller3.object.pk),
                  (1, controller4.object.pk),
                  (2, self.controller2.object.pk),
                  (3, self.controller3.object.pk),
                  ]
        children = [(lvl, lk.child.pk) for lvl, lk in self.controller.get_children(-1)]
        self.assertEqual(children, wanted)
        wanted = [(1, self.controller2.object.pk),
                  (1, controller4.object.pk)]
        # first level
        children = [(lvl, lk.child.pk) for lvl, lk in self.controller.get_children(1)]
        self.assertEqual(children, wanted)
        # date
        wanted = [(1, self.controller2.object.pk)]
        children = [(lvl, lk.child.pk) for lvl, lk in self.controller.get_children(-1, date=date)]
        self.assertEqual(children, wanted)
        # only_official=True
        wanted = [(1, self.controller2.object.pk)]
        children = [(lvl, lk.child.pk) for lvl, lk in
                self.controller.get_children(-1, only_official=True)]
        self.assertEqual(children, wanted)
        children = [(lvl, lk.child.pk) for lvl, lk
                in self.controller.get_children(-1, only_official=True, date=date2)]
        self.assertEqual(children, [])
        # promote controller4 to official
        controller4.object.is_promotable = lambda *args: True
        controller4.promote()
        # -> at date2, only controller2 is official
        wanted = [(1, self.controller2.object.pk)]
        children = [(lvl, lk.child.pk) for lvl, lk in
                self.controller.get_children(-1, only_official=True,
            date=date2)]
        wanted = [(1, self.controller2.object.pk),
                  (1, controller4.object.pk),
                  (2, self.controller2.object.pk),
                  ]
        children = [(lvl, lk.child.pk) for lvl, lk in
                self.controller.get_children(-1, only_official=True)]
        self.assertEqual(children, wanted)

    def test_get_parents(self):
        controller4 = self.create("aPart4")
        self.controller.add_child(self.controller2, 10, 15)
        date = timezone.now()
        self.controller2.add_child(self.controller3, 10, 15)
        self.controller2.object.is_promotable = lambda *args: True
        date2 = timezone.now()
        self.controller2.promote()
        self.controller.add_child(controller4, 10, 15)
        wanted = [(1, self.controller2.object.pk),
                  (2, self.controller.object.pk),]
        parents = [(lvl, lk.parent.pk) for lvl, lk in self.controller3.get_parents(-1)]
        self.assertEqual(parents, wanted)
        wanted = [(1, self.controller2.object.pk)]
        # first level
        parents = [(lvl, lk.parent.pk) for lvl, lk in self.controller3.get_parents(1)]
        self.assertEqual(parents, wanted)
        # date
        parents = [(lvl, lk.parent.pk) for lvl, lk in self.controller3.get_parents(date=date)]
        self.assertEqual(parents, [])
        # only_official=True
        wanted = [(1, self.controller2.object.pk)]
        parents = [(lvl, lk.parent.pk) for lvl, lk in
                self.controller3.get_parents(-1, only_official=True)]
        self.assertEqual(parents, wanted)
        parents = [(lvl, lk.parent.pk) for lvl, lk in
                self.controller3.get_parents(-1, only_official=True, date=date2)]
        self.assertEqual(parents, [])
        # promote controller4 to official
        self.controller.object.is_promotable = lambda *args: True
        self.controller.promote()
        parents = [(lvl, lk.parent.pk) for lvl, lk in
                self.controller3.get_parents(-1, only_official=True, date=date2)]
        self.assertEqual(parents, [])
        wanted = [(1, self.controller2.object.pk),
                  (2, self.controller.object.pk),
                  ]
        parents = [(lvl, lk.parent.pk) for lvl, lk in
                self.controller3.get_parents(-1, only_official=True)]
        self.assertEqual(parents, wanted)

    def test_is_promotable1(self):
        """Tests promotion from draft state, an official document is attached."""
        self.assertTrue(self.controller.is_promotable())

    def test_is_promotable2(self):
        """Tests promotion from official state."""
        self.controller.promote()
        self.assertTrue(self.controller.is_promotable())

    def test_is_promotable3(self):
        """Tests promotions with an official child."""
        self.controller2.promote()
        self.controller.add_child(self.controller2, 10, 15)
        self.assertTrue(self.controller.is_promotable())

    def test_is_promotable4(self):
        """Tests promotion from official state, with a deprecated child."""
        self.controller.add_child(self.controller2, 10, 15)
        self.controller2.promote()
        self.controller2.promote()
        self.assertTrue(self.controller.is_promotable())

    def test_is_promotable_no_document(self):
        "Tests that a part with no document attached is not promotable."""
        self.assertFalse(self.controller3.is_promotable())

    def test_is_promotable_no_official_document(self):
        "Tests that a part with no official document attached is not promotable."
        doc = DocumentController.create("doc_2", "Document", "a", self.user,
                self.DATA)
        self.controller3.attach_to_document(doc)
        self.assertFalse(self.controller3.is_promotable())

    def test_is_promotable_one_official_document(self):
        """Tests that a part with one official document attached and another
        not official is promotable."""
        doc = DocumentController.create("doc_2", "Document", "a", self.user,
                self.DATA)
        self.controller3.attach_to_document(self.document)
        self.controller3.attach_to_document(doc)
        self.assertTrue(self.controller3.is_promotable())

    def test_is_promotable_proposed_child(self):
        lifecycle = models.Lifecycle.objects.get(name="draft_proposed_official_deprecated")
        data = self.DATA.copy()
        data["lifecycle"] = lifecycle
        p1 = PartController.create("p1", "Part", "a", self.user, data)
        p2 = PartController.create("p2", "Part", "a", self.user, data)
        p1.add_child(p2, 1, 1 , "-")
        p2.promote(checked=True)
        p1.approve_promotion()
        self.assertFalse(p1.is_promotable())
        p2.approve_promotion()
        p1.approve_promotion()

    def test_promote(self):
        controller = self.controller
        self.assertEqual(controller.state.name, "draft")
        controller.promote()
        self.assertEqual(controller.state.name, "official")
        self.assertFalse(controller.is_editable)
        self.assertRaises(exc.PromotionError, controller.demote)
        lcl = LifecycleList("diop", "official", "draft",
                "issue1", "official", "deprecated")
        lc = models.Lifecycle.from_lifecyclelist(lcl)
        controller.lifecycle = lc
        controller.state = models.State.objects.get(name="draft")
        controller.save()
        controller.promote()
        self.assertEqual(controller.state.name, "issue1")
        controller.demote()
        self.assertEqual(controller.state.name, "draft")
        self.assertTrue(controller.is_editable)

    def test_cancel(self):
        """
        Tests :meth:`.Part.cancel`.
        """
        self.assertFalse(self.controller.is_cancelled)
        self.assertEqual(1, self.controller.get_attached_documents().count())
        # builds a small bom to checks that links are removed
        self.controller.add_child(self.controller2, 10, 10, "-")
        self.controller3.add_child(self.controller, 10, 10, "-")
        # cancels the object
        self.controller.cancel()
        self.check_cancelled_object(self.controller)
        # tests the links
        self.assertEqual(0, self.controller.get_attached_documents().count())
        self.assertEqual(0, len(self.controller.get_children()))
        self.assertEqual(0, len(self.controller3.get_children()))

    def test_attach_to_document(self):
        """
        Tests :meth:`.PartController.attach_to_document`.
        """
        doc = DocumentController.create("Doc2", "Document", "a",
                self.user, self.DATA)
        part = self.controller3
        part.check_attach_document(doc)
        doc.check_attach_part(part)
        part.attach_to_document(doc)
        self.assertEqual([part.object.id],
            list(doc.get_attached_parts().values_list("part", flat=True)))
        self.assertEqual([doc.object.id],
            list(part.get_attached_documents().values_list("document", flat=True)))
        self.assertEqual(list(doc.get_attached_parts()),
                list(part.get_attached_documents()))
        self.assertFalse(part.can_attach_document(doc))
        self.assertFalse(doc.can_attach_part(part))

    def test_attach_to_document_error_not_owner(self):
        """
        Tests that only the owner can attach a draft document to a part.
        """
        doc = DocumentController.create("Doc2", "Document", "a",
                self.user, self.DATA)
        self.promote_to_official(doc)
        robert = self.get_contributor()
        robert.groups.add(self.group)
        part = self.CONTROLLER(self.controller3.object, robert)
        part.check_readable()
        self.assertFalse(part.can_attach_document(doc))
        self.assertRaises(exc.PermissionError, part.attach_to_document, doc)
        self.assertFalse(part.get_attached_documents())
        self.assertFalse(doc.get_attached_parts())

    def test_get_suggested_documents_official(self):
        # self.document is official and has not been revised
        # self.controller and self.controller2 must suggest it
        self.assertTrue(self.document.is_official)
        for ctrl in (self.controller, self.controller2):
            suggested = ctrl.get_suggested_documents()
            self.assertEqual(1, suggested.count())
            self.assertTrue(self.document.object in suggested)
        # self.controller3 has no document attached: it suggests an empty list
        suggested = self.controller3.get_suggested_documents()
        self.assertFalse(suggested)

    def test_get_suggested_documents_draft(self):
        self.document.object.state = self.document.lifecycle.first_state
        self.document.object.save()
        self.assertTrue(self.document.is_draft)
        # self.controller and self.controller2 must suggest it
        for ctrl in (self.controller, self.controller2):
            suggested = ctrl.get_suggested_documents()
            self.assertEqual(1, suggested.count())
            self.assertTrue(self.document.object in suggested)
        # self.controller3 has no document attached: it suggests an empty list
        suggested = self.controller3.get_suggested_documents()
        self.assertFalse(suggested)

    def test_get_suggested_documents_proposed(self):
        lcl = LifecycleList("dpop","official", "draft",
               "proposed", "official", "deprecated")
        lc = models.Lifecycle.from_lifecyclelist(lcl)
        self.document.object.lifecycle = lc
        self.document.object.state = models.State.objects.get(name="proposed")
        self.document.object.save()
        self.assertTrue(self.document.is_proposed)
        for ctrl in (self.controller, self.controller2, self.controller3):
            suggested = ctrl.get_suggested_documents()
            self.assertFalse(suggested)

    def test_get_suggested_documents_deprecated(self):
        self.document.promote(checked=True)
        self.assertTrue(self.document.is_deprecated)
        for ctrl in (self.controller, self.controller2, self.controller3):
            suggested = ctrl.get_suggested_documents()
            self.assertFalse(suggested)

    def test_get_suggested_documents_revision_attached(self):
        lcl = LifecycleList("dpop","official", "draft",
               "proposed", "official", "deprecated")
        lc = models.Lifecycle.from_lifecyclelist(lcl)
        self.document.object.lifecycle = lc
        self.document.object.state = lc.first_state
        self.document.object.save()
        rev = self.document.revise('b')
        self.controller.attach_to_document(rev)
        for state in lcl:
            self.document.object.state = models.State.objects.get(name=state)
            self.document.object.save()
            suggested = self.controller.get_suggested_documents()
            if state == "official":
                self.assertEqual(2, suggested.count())
                self.assertTrue(rev.object in suggested)
                self.assertTrue(self.document.object in suggested)
            else:
                self.assertEqual(1, suggested.count())
                self.assertTrue(rev.object in suggested)
                self.assertFalse(self.document.object in suggested)

    def test_get_suggested_documents_revision_not_attached(self):
        lcl = LifecycleList("dpop","official", "draft",
               "proposed", "official", "deprecated")
        lc = models.Lifecycle.from_lifecyclelist(lcl)
        self.document.object.lifecycle = lc
        self.document.object.state = lc.first_state
        self.document.object.save()
        rev = self.document.revise('b')
        for state in lcl:
            self.document.object.state = models.State.objects.get(name=state)
            self.document.object.save()
            for rev_state in lcl:
                rev.object.state = models.State.objects.get(name=rev_state)
                rev.object.save()

                suggested = self.controller.get_suggested_documents()
                if state in ("draft", "official"):
                    self.assertTrue(self.document.object in suggested)
                else:
                    self.assertFalse(self.document.object in suggested)
                if rev_state in ("draft", "official"):
                    self.assertTrue(rev.object in suggested)
                else:
                    self.assertFalse(rev.object in suggested)

    def test_get_suggested_documents_two_revisions(self):
        lcl = LifecycleList("dpop","official", "draft",
               "proposed", "official", "deprecated")
        lc = models.Lifecycle.from_lifecyclelist(lcl)
        self.document.object.lifecycle = lc
        self.document.object.state = lc.first_state
        self.document.object.save()
        revb = self.document.revise('b')
        revc = revb.revise('c')
        revb.attach_to_part(self.controller)
        for state in lcl:
            self.document.object.state = models.State.objects.get(name=state)
            self.document.object.save()
            for revb_state in lcl:
                revb.object.state = models.State.objects.get(name=revb_state)
                revb.object.save()
                for revc_state in lcl:
                    revc.object.state = models.State.objects.get(name=revc_state)
                    revc.object.save()

                    suggested = self.controller.get_suggested_documents()
                    self.assertFalse(self.document.object in suggested)
                    if revb_state in ("draft", "official"):
                        self.assertTrue(revb.object in suggested)
                    else:
                        self.assertFalse(revb.object in suggested)

                    if revc_state in ("draft", "official"):
                        self.assertTrue(revc.object in suggested)
                    else:
                        self.assertFalse(revc.object in suggested)

    def test_revise_attached_documents(self):
        """
        Revises a part with two attached documents, both are selected.
        """
        document = DocumentController.create("DocDSDS", "Document", "a",
                self.user, self.DATA)
        document.attach_to_part(self.controller)

        rev = self.controller.revise("b", documents=(self.document.object,
            document.object))
        attached1 = self.controller.get_attached_documents()
        attached2 = rev.get_attached_documents()
        for attached in (attached1, attached2):
            self.assertEqual(2, attached.count())
            docs = attached.values_list("document", flat=True)
            self.assertTrue(self.document.id in docs)
            self.assertTrue(document.id in docs)

    def test_revise_attached_documents_one_selected(self):
        """
        Revises a part with two attached documents, one is selected.
        """
        document = DocumentController.create("DocDSDS", "Document", "a",
                self.user, self.DATA)
        document.attach_to_part(self.controller)

        rev = self.controller.revise("b", documents=(self.document.object, ))

        attached1 = self.controller.get_attached_documents()
        docs = attached1.values_list("document", flat=True)

        self.assertEqual(2, attached1.count())
        self.assertTrue(self.document.id in docs)
        self.assertTrue(document.id in docs)

        attached2 = rev.get_attached_documents()
        docs = attached2.values_list("document", flat=True)
        self.assertEqual(1, attached2.count())
        self.assertTrue(self.document.id in docs)
        self.assertFalse(document.id in docs)

    def test_revise_attached_documents_none_selected(self):
        """
        Revises a part with two attached documents, none are selected.
        """
        document = DocumentController.create("DocDSDS", "Document", "a",
                self.user, self.DATA)
        document.attach_to_part(self.controller)

        rev = self.controller.revise("b", documents=())

        attached1 = self.controller.get_attached_documents()
        docs = attached1.values_list("document", flat=True)

        self.assertEqual(2, attached1.count())
        self.assertTrue(self.document.id in docs)
        self.assertTrue(document.id in docs)

        attached2 = rev.get_attached_documents()
        self.assertFalse(attached2)

    def test_revise_no_child(self):
        """
        Revises a part and chooses to not add current children.
        """
        self.add_child()
        rev = self.controller.revise("b", child_links=())
        self.assertFalse(rev.get_children())

    def test_revise_one_child(self):
        """
        Revises a part and chooses to only add one child.
        """
        self.controller.add_child(self.controller2, 10, 15, "m")
        self.controller.add_child(self.controller3, 20, 35, "kg")
        links = [c.link for c in self.controller.get_children(1)]
        rev = self.controller.revise('b', child_links=(links[0],))
        links2 = [c.link for c in rev.get_children(1)]
        self.assertEqual(1, len(links2))
        self.assertEqual(links[0].child, links2[0].child)
        self.assertEqual(links[0].quantity, links2[0].quantity)
        self.assertEqual(links[0].order, links2[0].order)
        self.assertEqual(links[0].unit, links2[0].unit)

    def test_get_suggested_parents_no_revision(self):
        lcl = LifecycleList("dpop","official", "draft",
               "proposed", "official", "deprecated")
        lc = models.Lifecycle.from_lifecyclelist(lcl)
        self.add_child()
        self.controller.object.lifecycle = lc
        for state in lcl[:-1]:
            self.controller.object.state = models.State.objects.get(name=state)
            self.controller.object.save()

            suggested = self.controller2.get_suggested_parents()
            self.assertEqual(1, len(suggested))
            link, parent = suggested[0]
            self.assertEqual(parent.id, self.controller.id)
            self.assertEqual(link, self.controller.get_children(1)[0].link)
        # deprecated state
        self.controller.object.state = models.State.objects.get(name="deprecated")
        self.controller.object.save()
        suggested = self.controller2.get_suggested_parents()
        self.assertFalse(suggested)

    def test_get_suggested_parents_revision_attached(self):
        lcl = LifecycleList("dpop","official", "draft",
               "proposed", "official", "deprecated")
        lc = models.Lifecycle.from_lifecyclelist(lcl)
        self.controller.object.lifecycle = lc
        self.controller.object.state = lc.first_state
        self.controller.object.save()
        self.add_child()
        rev = self.controller.revise('b')
        self.assertEqual(1, len(rev.get_children(1)))
        for state in lcl:
            self.controller.object.state = models.State.objects.get(name=state)
            self.controller.object.save()
            suggested = self.controller2.get_suggested_parents()
            self.assertEqual(1, len(suggested))
            link, parent = suggested[0]
            self.assertEqual(parent.id, rev.id)

    def test_get_suggested_parents_revision_not_attached(self):
        lcl = LifecycleList("dpop","official", "draft",
               "proposed", "official", "deprecated")
        lc = models.Lifecycle.from_lifecyclelist(lcl)
        self.controller.object.lifecycle = lc
        self.controller.object.state = lc.first_state
        self.controller.object.save()
        self.add_child()
        rev = self.controller.revise('b', child_links=())
        for state in lcl:
            self.controller.object.state = models.State.objects.get(name=state)
            self.controller.object.save()
            for rev_state in lcl:
                rev.object.state = models.State.objects.get(name=rev_state)
                rev.object.save()

                suggested = self.controller2.get_suggested_parents()
                parents = set(p[1].id for p in suggested)
                if state in ("draft", "official"):
                    self.assertTrue(self.controller.id in parents)
                else:
                    self.assertFalse(self.controller.id in parents)
                if rev_state in ("draft", "official"):
                    self.assertTrue(rev.id in parents)
                else:
                    self.assertFalse(rev.id in parents)

    def test_get_suggested_parents_two_revisions(self):
        lcl = LifecycleList("dpop","official", "draft",
               "proposed", "official", "deprecated")
        lc = models.Lifecycle.from_lifecyclelist(lcl)
        self.controller.object.lifecycle = lc
        self.controller.object.state = lc.first_state
        self.controller.object.save()
        self.add_child()
        revb = self.controller.revise('b')
        revc = revb.revise('c', child_links=())
        expected_link = models.ParentChildLink.objects.get(parent=revb.id,
                child=self.controller2.id)
        for state in lcl:
            self.controller.object.state = models.State.objects.get(name=state)
            self.controller.object.save()
            for revb_state in lcl:
                revb.object.state = models.State.objects.get(name=revb_state)
                revb.object.save()
                for revc_state in lcl:
                    revc.object.state = models.State.objects.get(name=revc_state)
                    revc.object.save()

                    suggested = self.controller2.get_suggested_parents()
                    parents = set(p[1].id for p in suggested)
                    self.assertFalse(self.controller.id in parents)
                    if revb_state in ("draft", "official"):
                        self.assertTrue(revb.id in parents)
                    else:
                        self.assertFalse(revb.id in parents)

                    if revc_state in ("draft", "official"):
                        self.assertTrue(revc.id in parents)
                        link = [p[0] for p in suggested if p[1].id == revc.id][0]
                        self.assertEqual(link, expected_link)
                    else:
                        self.assertFalse(revc.id in parents)

    def test_revise_no_parent(self):
        """
        Revises a part and chooses to not change parents links.
        """
        self.add_child()
        rev = self.controller2.revise("b", child_links=())
        self.assertFalse(rev.get_children())
        links = [c.link for c in self.controller.get_children(1)]
        self.assertEqual(1, len(links))
        self.assertEqual(self.controller.id, links[0].parent_id)
        self.assertEqual(self.controller2.id, links[0].child_id)

    def test_revise_one_parent(self):
        """
        Revises a part and chooses to change one parent.
        """
        self.controller.add_child(self.controller3, 10, 15, "m")
        self.controller2.add_child(self.controller3, 20, 35, "kg")
        links = [c.link for c in self.controller.get_children(1)]
        if links[0].id == self.controller.id:
            parent, other = self.controller, self.controller2
        else:
            parent, other = self.controller2, self.controller
        rev = self.controller3.revise('b', parents=((links[0], parent.object),))

        parents = [p.link for p in rev.get_parents(1)]
        self.assertEqual(1, len(parents))
        self.assertEqual(parents[0].child_id, rev.id)
        self.assertEqual(parents[0].parent_id, parent.id)

        children = [c.link for c in parent.get_children(1)]
        self.assertEqual(1, len(children))
        self.assertEqual(children[0].child_id, rev.id)

        children_o = [c.link for c in other.get_children(1)]
        self.assertEqual(1, len(children))
        self.assertEqual(children_o[0].child_id, self.controller3.id)


    def assertCancelError(self, ctrl):
        res = super(PartControllerTest, self).assertCancelError(ctrl)
        from django.db.models.query import Q
        q = Q(parent=ctrl.object) | Q(child=ctrl.object)
        res = res or models.ParentChildLink.objects.filter(q).exists()
        res = res or bool(ctrl.get_attached_documents())
        self.assertTrue(res)

    def test_cancel_has_parent(self) :
        """ Test that a part with at least one parent can *not* be cancelled. """
        self.controller.add_child(self.controller3, 10, 15, "m")
        children = self.controller.get_children()
        self.assertEqual(len(children), 1)
        self.assertCancelError(self.controller3)

    def test_cancel_has_child(self) :
        """ Tests that a part with at least one child can *not* be cancelled. """
        self.controller3.add_child(self.controller2, 10, 15, "m")
        children = self.controller3.get_children()
        self.assertEqual(len(children), 1)
        self.assertCancelError(self.controller3)

    def test_cancel_has_document_related(self):
        """ Tests that a part with a document related can *not* be cancelled. """
        self.assertEqual(len(self.controller.get_attached_documents()), 1)
        self.assertCancelError(self.controller)

    #clone test

    def assertClone(self, ctrl, data, child_links, documents):
        new_ctrl = super(PartControllerTest, self).assertClone(ctrl, data)
        for link in child_links:
            link.clone(save=True, parent=new_ctrl.object)
        for doc in documents:
            models.DocumentPartLink.objects.create(part=new_ctrl.object,
                document=doc)

        # check that all children are child of the original part
        child_cloned = True
        children = [c.link for c in ctrl.get_children(1)]
        new_children = [c.link for c in new_ctrl.get_children(1)]
        less_or_equal = len(new_children) <= len(children)
        self.assertTrue(less_or_equal)
        for link in new_children:
            child_cloned = child_cloned and ctrl.parentchildlink_parent.filter(child=link.child).exists()
        self.assertTrue(child_cloned)


        # check that all attached document are attached to the original part
        doc_cloned = True
        for doc in new_ctrl.get_suggested_documents():
            doc_cloned = doc_cloned and doc in ctrl.get_suggested_documents()
        self.assertTrue(doc_cloned)


    def test_clone_child_links(self):
        """
        Tests that a part with children can be cloned.
        """
        ctrl = self.get_created_ctrl()
        ctrl.add_child(self.controller3, 10, 15, "m")
        children = [c.link for c in ctrl.get_children(1)]
        self.assertEqual(len(children), 1)
        data = self.getDataCloning(ctrl)
        self.assertClone(ctrl, data, children, [])

    def test_clone_attached_documents(self):
        """
        Tests that a part attached to documents can be cloned.
        """
        ctrl = self.get_created_ctrl()
        ctrl.attach_to_document(self.document)
        documents = ctrl.get_suggested_documents()
        self.assertEqual(len(documents),1)
        data = self.getDataCloning(ctrl)
        self.assertClone(ctrl, data, [], documents)

    def test_clone_cancelled(self):
        """Tests that even a cancelled object is cloned """
        ctrl = self.get_created_ctrl()
        data = self.getDataCloning(ctrl)
        ctrl.cancel()
        self.assertClone(ctrl, data, [],[])

    def test_clone_official(self):
        """Tests that an offical object can be cloned ."""
        ctrl = self.get_created_ctrl()
        ctrl.attach_to_document(self.document)
        self.promote_to_official(ctrl)
        data = self.getDataCloning(ctrl)
        self.assertClone(ctrl, data, [], [])

    def test_clone_deprecated(self):
        """Tests that a deprecated object can be cloned"""
        ctrl = self.get_created_ctrl()
        self.promote_to_deprecated(ctrl)
        data = self.getDataCloning(ctrl)
        self.assertClone(ctrl, data, [], [])

    def assertAddAlternateFails(self, ctrl, part):
        is_alternate = ctrl.is_alternate(part)
        self.assertRaises(ValueError, ctrl.add_alternate, part)
        self.assertEquals(is_alternate, ctrl.is_alternate(part))

    def test_add_alternate_simple(self):
        # no children, no parents
        self.controller.add_alternate(self.controller2)
        self.controller.add_alternate(self.controller3)
        self.assertTrue(self.controller.is_alternate(self.controller2))
        self.assertTrue(self.controller.is_alternate(self.controller3))

    def test_add_alternate_error_revision(self):
        # revision of the controller
        revb = self.controller.revise("b")
        self.assertAddAlternateFails(self.controller, revb)
        self.assertFalse(self.controller.get_alternates())
        self.assertAddAlternateFails(revb, self.controller)
        self.assertFalse(self.controller.can_add_alternate(revb))
        self.assertFalse(revb.can_add_alternate(self.controller))
        # revision of an alternate part
        revb.add_alternate(self.controller2)
        rev2b = self.controller2.revise("2b")
        self.assertAddAlternateFails(revb, rev2b)
        self.assertAddAlternateFails(rev2b, revb)
        self.assertAddAlternateFails(self.controller2, self.controller)

    def test_add_alternate_error_child(self):
        self.controller.add_child(self.controller2, 1, 4)
        self.assertAddAlternateFails(self.controller, self.controller2)
        self.assertAddAlternateFails(self.controller2, self.controller)
        self.assertFalse(self.controller.get_alternates())
        self.assertFalse(self.controller2.get_alternates())

    def test_add_alternate_error_siblings(self):
        self.controller.add_child(self.controller2, 1, 4)
        self.controller.add_child(self.controller3, 4, 5)
        self.assertAddAlternateFails(self.controller2, self.controller3)
        self.assertAddAlternateFails(self.controller3, self.controller2)

    def test_add_alternate_error_siblings2(self):
        """
        Part1
        |---> Part2 (child)
        +---> Part3 (child)
              +---> Part4 (alternate)
        """
        self.controller.add_child(self.controller2, 1, 4)
        ctrl4 = self.create("aPart4")
        self.controller3.add_alternate(ctrl4)
        self.controller.add_child(self.controller3, 5, 6)
        self.assertAddAlternateFails(self.controller, ctrl4)
        self.assertAddAlternateFails(self.controller2, ctrl4)
        self.assertAddAlternateFails(self.controller3, ctrl4)
        self.assertAddAlternateFails(ctrl4, self.controller2)
        self.assertRaises(ValueError, self.controller.add_child, ctrl4, 12, 12)
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(ctrl4.object))
        self.assertTrue(self.controller2.can_add_child(ctrl4))
        self.controller2.precompute_can_add_child2()
        self.assertTrue(self.controller2.can_add_child2(ctrl4.object))
        self.controller3.precompute_can_add_child2()
        self.assertFalse(self.controller3.can_add_child2(ctrl4.object))
        self.assertRaises(ValueError, self.controller3.add_child, ctrl4, 12, 12)

    def test_add_alternate_error_ancestor(self):
        """
        Part1
        +--> Part2 (child)
             +--> Part3 (child)
        """
        self.controller.add_child(self.controller2, 1, 5)
        self.controller2.add_child(self.controller3, 1, 5)
        self.assertAddAlternateFails(self.controller3, self.controller2)
        self.assertAddAlternateFails(self.controller3, self.controller)
        self.assertAddAlternateFails(self.controller, self.controller)

    def test_add_alternate_error_ancestor_of_alternate(self):
        """
        Part1
        +--> Part2 (child)
             +--> Part3 (child)
                  |--> Part4 (alternate)
                  +--> Part5 (alternate)
        """
        self.controller.add_child(self.controller2, 1, 3)
        self.controller2.add_child(self.controller3, 7, 54)
        ctrl4 = self.create("aPart4")
        self.controller3.add_alternate(ctrl4)
        self.assertAddAlternateFails(self.controller, ctrl4.object)
        self.assertAddAlternateFails(self.controller2, ctrl4)
        ctrl5 = self.create("aPart5")
        self.controller3.add_alternate(ctrl5)
        self.assertAddAlternateFails(self.controller, ctrl5.object)
        self.assertAddAlternateFails(self.controller2, ctrl5)

    def test_add_alternate_error_ancestors(self):
        """

        Part1
        |--> Part2 (alternate)
             +--> Part5 (child)
        +--> Part3 (child)
             +--> Part4 (child)

        Valid Alternate: (3, 5) or (4, 5) (not both)
        """
        self.controller.add_alternate(self.controller2)
        self.controller.add_child(self.controller3, 44, 7)
        c4 = self.create("aPart4")
        c5 = self.create("aPart5")
        self.controller3.add_child(c4, 54, 4545)
        self.controller2.add_child(c5, 54, 4545)

        # invalid alternate links
        c1 = self.controller
        c2 = self.controller2
        c3 = self.controller3
        for x, y in ((c1, c1), (c1, c2), (c1, c3), (c1, c4), (c1, c5),
                (c2, c2), (c2, c3), (c2, c4), (c2, c5),
                (c3, c3), (c3, c4), (c4, c4), (c5, c5),):
            self.assertAddAlternateFails(x, y)
            self.assertAddAlternateFails(y, x)

        # valid links
        self.assertTrue(c3.can_add_alternate(c5))
        self.assertTrue(c4.can_add_alternate(c5))
        self.assertTrue(c5.can_add_alternate(c3))
        self.assertTrue(c5.can_add_alternate(c4))

        # assert that (c3 <-> c5) and (c4 <-> c5) is not valid
        c4.add_alternate(c5)
        self.assertAddAlternateFails(c3, c5)

        c4.delete_alternate(c5)
        c3.add_alternate(c5)
        self.assertAddAlternateFails(c4, c5)


    def test_add_alternate_error_ancestors2(self):
        """

        Part6
        +--> Part2 (child)
             |--> Part1 (alternate)
                  +--> Part3 (child)
                       +--> Part4 (child)
             +--> Part5 (child)

        Valid Alternate: (3, 5) or (4, 5) (not both)
        """
        self.controller.add_alternate(self.controller2)
        self.controller.add_child(self.controller3, 44, 7)
        c4 = self.create("aPart4")
        c5 = self.create("aPart5")
        self.controller3.add_child(c4, 54, 4545)
        self.controller2.add_child(c5, 54, 4545)
        c6 = self.create("aPart6")
        c6.add_child(self.controller2, 25, 15)

        # invalid alternate links
        c1 = self.controller
        c2 = self.controller2
        c3 = self.controller3
        for x, y in ((c1, c1), (c1, c2), (c1, c3), (c1, c4), (c1, c5), (c1, c6),
                (c2, c2), (c2, c3), (c2, c4), (c2, c5), (c2, c6),
                (c3, c3), (c3, c4), (c3, c6), (c4, c4), (c4, c6),
                (c5, c5), (c5, c6), (c6, c6)):
            self.assertAddAlternateFails(x, y)
            self.assertAddAlternateFails(y, x)

        # valid links
        self.assertTrue(c3.can_add_alternate(c5))
        self.assertTrue(c4.can_add_alternate(c5))
        self.assertTrue(c5.can_add_alternate(c3))
        self.assertTrue(c5.can_add_alternate(c4))

        # assert that (c3 <-> c5) and (c4 <-> c5) is not valid
        c4.add_alternate(c5)
        self.assertAddAlternateFails(c3, c5)

        c4.delete_alternate(c5)
        c3.add_alternate(c5)
        self.assertAddAlternateFails(c4, c5)

    def test_add_alternate_error_ancestors3(self):
        """
        P0
        +--> P1 (child)
             +--> P2 (alternate)
                  +--> P3 (child)
                       +--> ...
        """
        ctrls = []
        for i in range(10):
            ctrls.append(self.create("x%d" % i))

        for i in range(1, 8, 2):
            ctrls[i].add_alternate(ctrls[i+1])
        for i in range(0, 9, 2):
            ctrls[i].add_child(ctrls[i+1], 1, 1)

        for x, y in itertools.product(ctrls, repeat=2):
            self.assertAddAlternateFails(x, y)

    def test_add_alternate_error_two_sets(self):
        """
        Merging of two alternate sets is not yet implemented.
        """
        c4 = self.create("part4")
        self.controller.add_alternate(self.controller2)
        self.controller3.add_alternate(c4)

        self.assertAddAlternateFails(self.controller, c4)
        self.assertAddAlternateFails(self.controller3, self.controller2)

    def test_add_child_error_alternate(self):
        self.controller.add_alternate(self.controller2)
        self.assertRaises(ValueError, self.add_child)
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(self.controller2.object))

    def test_add_child_error_alternate_of_child(self):
        self.controller3.add_alternate(self.controller2)
        self.controller.add_child(self.controller3, 4, 5)
        self.assertRaises(ValueError, self.add_child)
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(self.controller2.object))

    def test_add_child_error_parent_of_alternate(self):
        self.controller2.add_child(self.controller3, 1, 12)
        self.controller.add_alternate(self.controller3)
        self.assertRaises(ValueError, self.add_child)
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(self.controller2.object))

    def test_add_child_error_ancestor_of_alternate(self):
        c4 = self.create("p4")
        self.controller2.add_child(c4, 1, 12)
        c4.add_child(self.controller3, 1, 12)
        self.controller.add_alternate(self.controller3)
        self.assertRaises(ValueError, self.add_child)
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(self.controller2.object))

    def test_add_child_error_alternate_is_parent(self):
        """
        Part3
        |--> Part2 (alternate)
        +--> Part1 (child)

        asserts that Part1 --> Part2 (child) is forbidden
        """
        self.controller3.add_child(self.controller, 4, 5)
        self.controller3.add_alternate(self.controller2)
        self.assertRaises(ValueError, self.add_child)
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(self.controller2.object))

    def test_add_child_error_alternate_is_ancestor(self):
        """
        Part3
        |--> Part2 (alternate)
        +--> Part4 (child)
             +--> Part1 (child)

        asserts that Part1 --> Part2 (child) is forbidden
        """

        c4 = self.create("p4")
        self.controller3.add_child(c4, 4, 5)
        c4.add_child(self.controller, 4, 5)
        self.controller3.add_alternate(self.controller2)
        self.assertRaises(ValueError, self.add_child)
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(self.controller2.object))

    # naming tests is painful
    def test_add_child_error_alt_of_parent_of_alt(self):
        """
        Part4
        +--> Part3 (alternate)
             +--> Part2 (child)
                  +--> Part1 (alternate)

        asserts that Part1 --> Part4 (child) is forbidden
        Part4 --> Part1 (child) is allowed
        """
        c4 = self.create("p4")
        c4.add_alternate(self.controller3)
        self.controller3.add_child(self.controller2, 1, 1)
        self.controller.add_alternate(self.controller2)

        self.assertRaises(ValueError, self.controller.add_child, c4, 2, 2)
        self.controller.precompute_can_add_child2()
        self.assertFalse(self.controller.can_add_child2(c4.object))
        self.assertTrue(c4.can_add_child(self.controller))
        c4.precompute_can_add_child2()
        self.assertTrue(c4.can_add_child2(self.controller.object))

    def test_is_promotable_with_alternate_child(self):
        """
        Test cases:

        Part1
        +--> Part2 (child, draft)
             +--> Part3 (alternate, draft)
        :- Part1 not promotable

        ----

        Part1
        +--> Part2 (child, draft)
             +--> Part3 (alternate, official)
        :- Part1 promotable

        ----

        Part1
        |--> Part2 (child, draft)
             +--> Part3 (alternate, official)
        +--> Part4 (child, draft)
        :- Part1 not promotable
        """

        self.add_child()
        self.controller3.add_alternate(self.controller2)
        self.assertFalse(self.controller.is_promotable())
        self.controller3.promote(True)
        self.assertTrue(self.controller.is_promotable())
        c4 = self.create("p4")
        self.controller.add_child(c4, 18, 155)
        self.assertFalse(self.controller.is_promotable())

    def test_is_promotable_with_alternate(self):
        """
        Test cases:

        Part3 (draft, no document)
        +--> Part2 (draft, one official document)
        :- Part3 not promotable, Part2 promotable

        Part3 (draft, no document)
        +--> Part2 (official)
        :- Part3 not promotable
        """
        self.controller3.add_alternate(self.controller2)
        self.assertFalse(self.controller3.is_promotable())
        self.controller2.promote()
        self.assertFalse(self.controller3.is_promotable())

    def test_promote_update_alternates(self):
        """
        Asserts that alternates are updated when a new revision is officialized.
        """
        self.controller.add_alternate(self.controller2)
        revb = self.controller.revise("b")
        revb.attach_to_document(self.document)
        self.assertFalse(revb.get_alternates())
        self.assertTrue(self.controller.is_alternate(self.controller2.object))

        # cancelled previous revision
        revb.promote()
        obj = self.controller.object
        self.controller.object = type(obj).objects.get(id=obj.id)
        self.assertTrue(self.controller.object.is_cancelled)
        self.assertFalse(self.controller.is_alternate(self.controller2.object))
        self.assertTrue(revb.is_alternate(self.controller2.object))

        # deprecated previous revision
        revc = revb.revise("c")
        revc.attach_to_document(self.document)
        revc.promote()
        revb.object = type(revb.object).objects.get(id=revb.id)
        self.assertTrue(revb.is_deprecated)
        self.assertFalse(revb.is_alternate(self.controller2.object))
        self.assertTrue(revc.is_alternate(self.controller2.object))

    def test_deprecate_remove_alternates(self):
        self.controller.add_alternate(self.controller2)
        self.controller.promote()
        self.controller.promote()
        self.assertTrue(self.controller.is_deprecated)
        self.assertFalse(self.controller.is_alternate(self.controller2))


