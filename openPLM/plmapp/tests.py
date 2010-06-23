"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

import datetime
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.test import TestCase

from utils import *
from controllers import *
from lifecycle import *
from openPLM.plmapp.models import *

class ViewTest(TestCase):
    TYPE = "Part"
    def setUp(self):
        self.user = User(username="user")
        self.user.set_password("password")
        self.user.save()

        self.controller = PartController.create("Part1", self.TYPE, "a", self.user)
        self.base_url = "/object/%s/%s/%s/" % (self.controller.type,
                                              self.controller.reference,
                                              self.controller.revision)
    def test_home(self):
        response = self.client.get("/home/")
        self.failUnlessEqual(response.status_code, 200)
        
    def test_create(self):
        response = self.client.get("/object/create/", {"type" : self.TYPE})
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(response.context["object_type"], self.TYPE)
        self.failUnless(response.context["creation_form"])
   
    def test_create2(self):
        response = self.client.get("/object/create/",
                                   {"type" : self.TYPE, "reference" : "mapart",
                                    "revision" : "a", "name" : "MaPart"})

        self.failUnlessEqual(response.status_code, 200)

    def test_display_attributes(self):
        response = self.client.get(self.base_url)
        self.failUnlessEqual(response.status_code, 200)
        self.failUnless(response.context["object_attributes"])
        attributes = dict(response.context["object_attributes"])
        self.failUnlessEqual(attributes["name"], "")

    def test_lifecycle(self):
        response = self.client.get(self.base_url + "lifecycle/")
        self.failUnlessEqual(response.status_code, 200)
        lifecycles = tuple(response.context["object_lifecycle"])
        wanted = (("draft", True), ("official", False), ("deprecated", False))
        self.failUnlessEqual(lifecycles, wanted)
        # promote
        response = self.client.post(self.base_url + "lifecycle/", 
                                    {"action" : "PROMOTE"})
        self.failUnlessEqual(response.status_code, 200)
        lifecycles = tuple(response.context["object_lifecycle"])
        wanted = (("draft", False), ("official", True), ("deprecated", False))
        self.failUnlessEqual(lifecycles, wanted)
        # demote
        response = self.client.post(self.base_url + "lifecycle/", 
                                    {"action" : "DEMOTE"})
        self.failUnlessEqual(response.status_code, 200)
        lifecycles = tuple(response.context["object_lifecycle"])
        wanted = (("draft", True), ("official", False), ("deprecated", False))
        self.failUnlessEqual(lifecycles, wanted)

    def test_revisions(self):
        response = self.client.get(self.base_url + "revisions/")
        self.failUnlessEqual(response.status_code, 200)
        revisions = response.context["revisions"]
        self.failUnlessEqual(revisions, [self.controller.object])
        # check add_revision_form
        add_revision_form = response.context["add_revision_form"]
        self.failUnlessEqual(add_revision_form.data, {"revision": "b"})


class ControllerTest(TestCase):

    CONTROLLER = PLMObjectController
    TYPE = "Part"

    def setUp(self):
        self.user = User(username="user")
        self.user.set_password("password")
        self.user.save()

    def test_create(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a", self.user)
        self.assertEqual(controller.name, "")
        self.assertEqual(controller.type, self.TYPE)
        self.assertEqual(type(controller.object), Part)

    def test_keys(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a", self.user)
        controller2 = self.CONTROLLER.create("Part2", self.TYPE, "a", self.user)
        def fail():
            controller3 = self.CONTROLLER.create("Part1", self.TYPE, "a", self.user)
        self.assertRaises(IntegrityError, fail)

    def test_getattr(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a", self.user)
        self.assertEqual(controller.name, "")
        self.failUnless("name" in controller.attributes)
        self.assertEqual(controller.state.name, "draft")
        self.assertRaises(AttributeError, lambda: controller.unknown_attr)

    def test_setattr(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a", self.user)
        self.assertEqual(controller.name, "")
        controller.name = "a name"
        self.assertEqual(controller.name, "a name")
        controller.save()
        self.assertEqual(controller.name, "a name")

    def test_promote(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a", self.user)
        self.assertEqual(controller.state.name, "draft")
        controller.promote()
        self.assertEqual(controller.state.name, "official")
        controller.demote()
        self.assertEqual(controller.state.name, "draft")

    def test_revise(self):
        """
        Test :meth:`revise`
        """
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a", self.user)
        rev = controller.revise("b")
        self.assertEqual(rev.revision, "b")
        def fail():
            controller.revise("b2")
        self.assertRaises(RevisionError, fail)

class PartControllerTest(ControllerTest):
    CONTROLLER = PartController
   
    def setUp(self):
        super(PartControllerTest, self).setUp()
        self.controller = self.CONTROLLER.create("aPart1", self.TYPE, "a", self.user)
        self.controller2 = self.CONTROLLER.create("aPart2", self.TYPE, "a", self.user)
        self.controller3 = self.CONTROLLER.create("aPart3", self.TYPE, "a", self.user)
        self.controller4 = self.CONTROLLER.create("aPart4", self.TYPE, "a", self.user)

    def test_add_child(self):
        children = self.controller.get_children()
        self.assertEqual(len(children), 0)
        self.controller.add_child(self.controller2, 10, 15)
        children = self.controller.get_children()
        self.assertEqual(len(children), 1)
        level, link = children[0]
        self.assertEqual(level, 1)
        self.assertEqual(link.child, self.controller2.object)
        self.assertEqual(link.parent, self.controller.object)
        self.assertEqual(link.quantity, 10)
        self.assertEqual(link.order, 15)

    def test_add_child_errors(self):
        def f1():
            # bad quantity
            self.controller.add_child(self.controller2, -10, 15)
        def f2():
            # bad order
            self.controller.add_child(self.controller2, 10, -15)
        def f3():
            # bad child : parent
            self.controller2.add_child(self.controller, 10, 15)
            self.controller.add_child(self.controller2, 10, 15)
        def f4():
            # bad child : already a child
            self.controller.add_child(self.controller2, 10, 15)
            self.controller.add_child(self.controller2, 10, 15)
        self.assertRaises(ValueError, f1)
        self.assertRaises(ValueError, f2)
        self.assertRaises(ValueError, f3)
        self.assertRaises(ValueError, f4)

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
        wanted = [(1, self.controller2.object),
                  (2, self.controller3.object),
                  (1, self.controller4.object)]
        children = [(lvl, lk.child) for lvl, lk in self.controller.get_children(-1)]
        self.assertEqual(children, wanted)
        wanted = [(1, self.controller2.object),
                  (1, self.controller4.object)]
        # first level
        children = [(lvl, lk.child) for lvl, lk in self.controller.get_children(1)]
        self.assertEqual(children, wanted)
        # date
        wanted = [(1, self.controller2.object)]
        children = [(lvl, lk.child) for lvl, lk in self.controller.get_children(date=date)]
        self.assertEqual(children, wanted)

    def test_get_parents(self):
        self.controller.add_child(self.controller2, 10, 15)
        date = datetime.datetime.now()
        self.controller2.add_child(self.controller3, 10, 15)
        self.controller.add_child(self.controller4, 10, 15)
        wanted = [(1, self.controller2.object),
                  (2, self.controller.object),]
        parents = [(lvl, lk.parent) for lvl, lk in self.controller3.get_parents(-1)]
        self.assertEqual(parents, wanted)
        wanted = [(1, self.controller2.object)]
        # first level
        parents = [(lvl, lk.parent) for lvl, lk in self.controller3.get_parents(1)]
        self.assertEqual(parents, wanted)
        # date
        parents = [(lvl, lk.parent) for lvl, lk in self.controller3.get_parents(date=date)]
        self.assertEqual(parents, [])


def get_doctest(module_name):
    test_dict={}
    module = __import__(module_name,{},{},module_name.split('.')[-1])
    for obj_name,obj in module.__dict__.items():
        if '__module__' in dir(obj) and obj.__module__ == module_name:
            if obj.__doc__:
                test_dict[obj_name] = obj.__doc__
                return test_dict

__test__ = get_doctest("plmapp.utils")
__test__.update(get_doctest("plmapp.controllers"))
__test__.update(get_doctest("plmapp.lifecycle"))

