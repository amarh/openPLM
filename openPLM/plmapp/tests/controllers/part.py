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

import datetime

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
        self.controller = self.CONTROLLER.create("aPart1", self.TYPE, "a",
                                                 self.user, self.DATA)
        self.controller2 = self.CONTROLLER.create("aPart2", self.TYPE, "a",
                                                  self.user, self.DATA)
        self.controller3 = self.CONTROLLER.create("aPart3", self.TYPE, "a",
                                                  self.user, self.DATA)
        self.document = DocumentController.create("Doc1", "Document", "a",
                self.user, self.DATA)
        self.document.add_file(self.get_file())
        self.document.state = self.document.lifecycle.official_state
        self.document.object.save()
        for ctrl in (self.controller, self.controller2):
            ctrl.attach_to_document(self.document)

    def test_add_child(self):
        children = self.controller.get_children()
        self.assertEqual(len(children), 0)
        self.controller.add_child(self.controller2, 10, 15)
        children = self.controller.get_children()
        self.assertEqual(len(children), 1)
        level, link = children[0]
        self.assertEqual(level, 1)
        self.assertEqual(link.child.pk, self.controller2.object.pk)
        self.assertEqual(link.parent.pk, self.controller.object.pk)
        self.assertEqual(link.quantity, 10)
        self.assertEqual(link.order, 15)

    def test_add_child_error1(self):
        def fail():
            # bad quantity
            self.controller.add_child(self.controller2, -10, 15)
        self.assertRaises(ValueError, fail)

    def test_add_child_error2(self):
        def fail():
            # bad order
            self.controller.add_child(self.controller2, 10, -15)
        self.assertRaises(ValueError, fail)
    
    def test_add_child_error3(self):
        def fail():
            # bad child : parent
            self.controller2.add_child(self.controller, 10, 15)
            self.controller.add_child(self.controller2, 10, 15)
        self.assertRaises(ValueError, fail)
    
    def test_add_child_error4(self):
        def fail():
            # bad child : already a child
            self.controller.add_child(self.controller2, 10, 15)
            self.controller.add_child(self.controller2, 10, 15)
        self.assertRaises(ValueError, fail)
    
    def test_add_child_error5(self):
        def fail():
            # bad child type
            doc = PLMObjectController.create("e", "PLMObject", "1", self.user)
            self.controller.add_child(doc, 10, 15)
        self.assertRaises(ValueError, fail)

    def test_add_child_error6(self):
        def fail():
            # bad child : add self
            self.controller.add_child(self.controller, 10, 15)
        self.assertRaises(ValueError, fail)

    def test_modify_child(self):
        self.controller.add_child(self.controller2, 10, 15, "-")
        self.controller.modify_child(self.controller2, 3, 5, "kg")
        children = self.controller.get_children()
        level, link = children[0]
        self.assertEqual(link.quantity, 3)
        self.assertEqual(link.order, 5)
        self.assertEqual(link.unit, "kg")

    def test_delete_child(self):
        self.controller.add_child(self.controller2, 10, 15)
        self.controller.delete_child(self.controller2)
        self.assertEqual(self.controller.get_children(), [])

    def test_get_children(self):
        controller4 = self.CONTROLLER.create("aPart4", self.TYPE, "a",
                                                  self.user, self.DATA)
        self.controller.add_child(self.controller2, 10, 15)
        date = datetime.datetime.now()
        self.controller2.add_child(self.controller3, 10, 15)
        self.controller.add_child(controller4, 10, 15)
        wanted = [(1, self.controller2.object.pk),
                  (2, self.controller3.object.pk),
                  (1, controller4.object.pk)]
        children = [(lvl, lk.child.pk) for lvl, lk in self.controller.get_children(-1)]
        self.assertEqual(children, wanted)
        wanted = [(1, self.controller2.object.pk),
                  (1, controller4.object.pk)]
        # first level
        children = [(lvl, lk.child.pk) for lvl, lk in self.controller.get_children(1)]
        self.assertEqual(children, wanted)
        # date
        wanted = [(1, self.controller2.object.pk)]
        children = [(lvl, lk.child.pk) for lvl, lk in self.controller.get_children(date=date)]
        self.assertEqual(children, wanted)

    def test_get_parents(self):
        controller4 = self.CONTROLLER.create("aPart4", self.TYPE, "a",
                                                  self.user, self.DATA)
        self.controller.add_child(self.controller2, 10, 15)
        date = datetime.datetime.now()
        self.controller2.add_child(self.controller3, 10, 15)
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

    def test_is_promotable1(self):
        """Tests promotion from draft state, an official document is attached."""
        self.failUnless(self.controller.is_promotable())

    def test_is_promotable2(self):
        """Tests promotion from official state."""
        self.controller.promote()
        self.failUnless(self.controller.is_promotable())
    
    def test_is_promotable3(self):
        """Tests promotions with an official child."""
        self.controller2.promote()
        self.controller.add_child(self.controller2, 10, 15)
        self.failUnless(self.controller.is_promotable())
        
    def test_is_promotable4(self):
        """Tests promotion from official state, with a deprecated child."""
        self.controller2.promote()
        self.controller2.promote()
        self.controller.add_child(self.controller2, 10, 15)
        self.failUnless(self.controller.is_promotable())

    def test_is_promotable_no_document(self):
        "Tests that a part with no document attached is not promotable."""
        self.failIf(self.controller3.is_promotable())

    def test_is_promotable_no_official_document(self):
        "Tests that a part with no official document attached is not promotable."
        doc = DocumentController.create("doc_2", "Document", "a", self.user,
                self.DATA)
        self.controller3.attach_to_document(doc)
        self.failIf(self.controller3.is_promotable())

    def test_is_promotable_one_official_document(self):
        """Tests that a part with one official document attached and another
        not official is promotable."""
        doc = DocumentController.create("doc_2", "Document", "a", self.user,
                self.DATA)
        self.controller3.attach_to_document(self.document)
        self.controller3.attach_to_document(doc)
        self.failUnless(self.controller3.is_promotable())

    def test_promote(self):
        controller = self.controller
        self.assertEqual(controller.state.name, "draft")
        controller.promote()
        self.assertEqual(controller.state.name, "official")
        self.failIf(controller.is_editable)
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
        self.failUnless(controller.is_editable)


