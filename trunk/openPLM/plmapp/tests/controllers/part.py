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

from openPLM.plmapp.utils import *
from openPLM.plmapp.exceptions import *
from openPLM.plmapp.models import *
from openPLM.plmapp.controllers import *
from openPLM.plmapp.lifecycle import *
from openPLM.computer.models import *
from openPLM.office.models import *
from openPLM.cad.models import *

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
        self.controller4 = self.CONTROLLER.create("aPart4", self.TYPE, "a",
                                                  self.user, self.DATA)

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
        self.controller.add_child(self.controller2, 10, 15)
        self.controller.modify_child(self.controller2, 3, 5)
        children = self.controller.get_children()
        level, link = children[0]
        self.assertEqual(link.quantity, 3)
        self.assertEqual(link.order, 5)

    def test_delete_child(self):
        self.controller.add_child(self.controller2, 10, 15)
        self.controller.delete_child(self.controller2)
        self.assertEqual(self.controller.get_children(), [])

    def test_get_children(self):
        self.controller.add_child(self.controller2, 10, 15)
        date = datetime.datetime.now()
        self.controller2.add_child(self.controller3, 10, 15)
        self.controller.add_child(self.controller4, 10, 15)
        wanted = [(1, self.controller2.object.pk),
                  (2, self.controller3.object.pk),
                  (1, self.controller4.object.pk)]
        children = [(lvl, lk.child.pk) for lvl, lk in self.controller.get_children(-1)]
        self.assertEqual(children, wanted)
        wanted = [(1, self.controller2.object.pk),
                  (1, self.controller4.object.pk)]
        # first level
        children = [(lvl, lk.child.pk) for lvl, lk in self.controller.get_children(1)]
        self.assertEqual(children, wanted)
        # date
        wanted = [(1, self.controller2.object.pk)]
        children = [(lvl, lk.child.pk) for lvl, lk in self.controller.get_children(date=date)]
        self.assertEqual(children, wanted)

    def test_get_parents(self):
        self.controller.add_child(self.controller2, 10, 15)
        date = datetime.datetime.now()
        self.controller2.add_child(self.controller3, 10, 15)
        self.controller.add_child(self.controller4, 10, 15)
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
        self.failUnless(self.controller.is_promotable())

    def test_is_promotable2(self):
        self.controller.promote()
        self.failUnless(self.controller.is_promotable())
    
    def test_is_promotable3(self):
        self.controller.add_child(self.controller2, 10, 15)
        self.failUnless(self.controller.is_promotable())
        
    def test_is_promotable4(self):
        self.controller2.promote()
        self.controller.add_child(self.controller2, 10, 15)
        self.failUnless(self.controller.is_promotable())

    def test_is_promotable5(self):
        self.controller.add_child(self.controller2, 10, 15)
        self.controller.promote()
        self.failIf(self.controller.is_promotable())


class HardDiskControllerTest(PartControllerTest):
    TYPE = "HardDisk"
    CONTROLLER = SinglePartController
    DATA = {"capacity_in_go" : 500}


