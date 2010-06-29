"""
This module contains some tests for openPLM.
"""

import os
import datetime
from django.conf import settings
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.files.base import ContentFile


from openPLM.plmapp.utils import *
from openPLM.plmapp.controllers import *
from openPLM.plmapp.lifecycle import *
from openPLM.plmapp.models import *
from openPLM.plmapp.customized_models.computer import *

class LifecycleTest(TestCase):
    def test_get_default(self):
        lifecycle = get_default_lifecycle()
    
    def test_to_list(self):
        lifecycle = get_default_lifecycle()
        lc_list = lifecycle.to_states_list()
        self.assertEqual(lc_list.name, lifecycle.name)
        lcs = LifecycleStates.objects.filter(lifecycle=lifecycle).order_by("rank")
        self.assertEqual(len(lcs), len(lc_list))

    def test_from_list(self):
        cycle = LifecycleList("cycle_name", "a", "b", "c")
        lifecycle = Lifecycle.from_lifecyclelist(cycle)
        self.assertEqual(cycle.name, lifecycle.name)

    def test_iteration(self):
        cycle = LifecycleList("cycle_name", "a", "b", "c")
        lifecycle = Lifecycle.from_lifecyclelist(cycle)
        for i, state in enumerate(lifecycle):
            self.assertEqual(state, cycle[i])

    def test_get_default_state(self):
        state = get_default_state()
        self.assertEqual(state.name, "draft")
        
class ControllerTest(TestCase):
    CONTROLLER = PLMObjectController
    TYPE = "Part"
    DATA = {}

    def setUp(self):
        self.user = User(username="user")
        self.user.set_password("password")
        self.user.save()

    def test_create(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertEqual(controller.name, "")
        self.assertEqual(controller.type, self.TYPE)
        self.assertEqual(type(controller.object), get_all_plmobjects()[self.TYPE])

    def test_create_error1(self):
        # empty reference
        def fail():
            controller = self.CONTROLLER.create("", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertRaises(ValueError, fail)

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
    
    def test_create_error(self):
        # bad type : PLMObject
        def fail():
            controller = self.CONTROLLER.create("zee", "PLMOBject_", "a",
                                            self.user, self.DATA)
        self.assertRaises(ValueError, fail)

    def test_keys(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        controller2 = self.CONTROLLER.create("Part2", self.TYPE, "a",
                                             self.user, self.DATA)
        def fail():
            controller3 = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                                 self.user, self.DATA)
        self.assertRaises(IntegrityError, fail)

    def test_getattr(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertEqual(controller.name, "")
        self.failUnless("name" in controller.attributes)
        self.assertEqual(controller.state.name, "draft")
        self.assertRaises(AttributeError, lambda: controller.unknown_attr)

    def test_setattr(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertEqual(controller.name, "")
        controller.name = "a name"
        self.assertEqual(controller.name, "a name")
        controller.save()
        self.assertEqual(controller.name, "a name")

    def test_setattr_errors(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertRaises(ValueError, setattr, controller, "owner", "error")
        self.assertRaises(ValueError, setattr, controller, "state", "error")
        self.assertRaises(ValueError, setattr, controller, "state", "draft")

    def test_promote(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertEqual(controller.state.name, "draft")
        controller.promote()
        self.assertEqual(controller.state.name, "official")
        controller.demote()
        self.assertEqual(controller.state.name, "draft")

    def test_revise(self):
        """
        Test :meth:`revise`
        """
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        rev = controller.revise("b")
        self.assertEqual(rev.revision, "b")
        def fail():
            controller.revise("b2")
        self.assertRaises(RevisionError, fail)
        for attr in controller.get_modification_fields():
            self.assertEqual(getattr(controller, attr), getattr(rev, attr))

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

class HardDiskControllerTest(PartControllerTest):
    TYPE = "HardDisk"
    CONTROLLER = SinglePartController
    DATA = {"capacity_in_go" : 500}

class DocumentControllerTest(ControllerTest):
    TYPE = "Document"
    CONTROLLER = DocumentController
    DATA = {}

    def setUp(self):
        super(DocumentControllerTest, self).setUp()
        self.controller = self.CONTROLLER.create("adoc", self.TYPE, "a",
                                                 self.user, self.DATA)
        self.part = PartController.create("mpart", "Part", "a", self.user)

    def test_initial_lock(self):
        self.assertEqual(self.controller.locked, False)
        self.assertEqual(self.controller.locker, None)

    def test_lock(self):
        self.controller.lock()
        self.assertEqual(self.controller.locked, True)
        self.assertEqual(self.controller.locker, self.user)

    def test_lock_error1(self):
        "Error : already locked"
        self.controller.lock()
        self.assertRaises(LockError, self.controller.lock)
    
    def test_unlock(self):
        self.controller.lock()
        self.controller.unlock()
        self.assertEqual(self.controller.locked, False)
        self.assertEqual(self.controller.locker, None)
    
    def test_unlock_error1(self):
        self.assertRaises(UnlockError, self.controller.unlock)

    def test_unlock_error2(self):
        user = User(username="baduser")
        user.set_password("password")
        user.save()
        controller = self.CONTROLLER(self.controller.object, user)
        self.assertRaises(UnlockError, controller.unlock)
    
    def get_file(self, name="temp.txt", data="data"):
        f = ContentFile(data)
        f.name = name
        return f

    def test_add_file(self):
        f = self.get_file()
        self.controller.add_file(f)
        files = self.controller.files.all()
        self.assertEqual(len(files), 1)
        f2 = files[0]
        self.assertEqual(f2.filename, f.name)
        self.assertEqual(f2.size, f.size)
        self.assertEqual(f2.file.read(), "data")
        self.assertEqual(file(f2.file.name).read(), "data")
        self.assertEqual(os.path.splitext(f2.file.name)[1], ".txt")
        self.failIf("temp" in f2.file.path)
        self.failUnless(f2.file.name.startswith(os.path.join(
            settings.DOCUMENTS_DIR, "txt")))
        self.failUnless(os.access(f2.file.path, os.F_OK))
        self.failUnless(os.access(f2.file.path, os.R_OK))
        self.failUnless(not os.access(f2.file.path, os.W_OK))
        self.failUnless(not os.access(f2.file.path, os.X_OK))
        # clean up
        os.chmod(f2.file.path, 0700)
        os.remove(f2.file.path)

    def test_add_several_files(self):
        nb = 5
        for i in xrange(nb):
            f = self.get_file("temp%d.txt" % i, "data%d" % i)
            self.controller.add_file(f)
        files = self.controller.files.all().order_by('filename')
        self.assertEqual(len(files), nb)
        for i, f2 in enumerate(files):
            self.assertEqual(f2.filename, "temp%d.txt" % i)
            self.assertEqual(f2.file.read(), "data%d" % i)
            os.chmod(f2.file.path, 0700)
            os.remove(f2.file.path)

    def test_add_file_error(self):
        self.controller.lock()
        self.assertRaises(AddFileError, self.controller.add_file,
                          self.get_file())

    def test_delete_file(self):
        self.controller.add_file(self.get_file())
        f2 = self.controller.files.all()[0]
        path = f2.file.path
        self.controller.delete_file(f2)
        self.assertEqual([], list(self.controller.files.all()))
        self.failIf(os.path.exists(path))

    def test_delete_file_error(self):
        self.controller.add_file(self.get_file())
        f2 = self.controller.files.all()[0]
        self.controller.lock()
        self.assertRaises(DeleteFileError, self.controller.delete_file, f2)

    def test_attach_to_part(self):
        self.controller.attach_to_part(self.part)
    
    def test_attach_to_part_error1(self):
        self.assertRaises(ValueError, self.controller.attach_to_part, None)
    
    def test_attach_to_part_error2(self):
        self.assertRaises(ValueError, self.controller.attach_to_part, self)

    def test_attach_to_part_error3(self):
        obj = PLMObject.objects.create(reference="obj", type="PLMObject",
                           revision="a", creator=self.user, owner=self.user)
        self.assertRaises(ValueError, self.controller.attach_to_part, obj)
    
    def test_attach_to_part_error4(self):
        obj = self.CONTROLLER.create("ob", self.TYPE, "a", self.user, self.DATA)
        self.assertRaises(ValueError, self.controller.attach_to_part, obj)
    
    def test_get_attached_parts(self):
        self.controller.attach_to_part(self.part)
        links = list(self.controller.get_attached_parts())
        self.assertEqual([l.part for l in links], [self.part.object])
        
    def test_get_attached_parts_empty(self):
        links = list(self.controller.get_attached_parts())
        self.assertEqual(links, [])

    def test_revise2(self):
        self.controller.attach_to_part(self.part)
        self.controller.add_file(self.get_file())
        f1 = self.controller.files.all()[0]
        rev = self.controller.revise("new_name")
        links = list(rev.get_attached_parts())
        self.assertEqual(links, [])
        self.assertEqual(len(rev.files.all()), 1)
        self.assertEqual(len(self.controller.files.all()), 1)
        f2 = rev.files.all()[0]
        self.assertEqual(f1.filename, f2.filename)
        self.assertEqual(f1.size, f2.size)
        self.assertEqual(f1.file.read(), f2.file.read())
        self.failIf(f1.file.path == f2.file.path)
        
        
class CommonViewTest(TestCase):
    TYPE = "Part"
    CONTROLLER = PartController
    DATA = {}

    def setUp(self):
        self.user = User(username="user")
        self.user.set_password("password")
        self.user.save()

        self.controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                                 self.user, self.DATA)
        self.base_url = "/object/%s/%s/%s/" % (self.controller.type,
                                              self.controller.reference,
                                              self.controller.revision)

class ViewTest(CommonViewTest):

    def test_home(self):
        response = self.client.get("/home/")
        self.assertEqual(response.status_code, 200)
        
    def test_create(self):
        response = self.client.get("/object/create/", {"type" : self.TYPE})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["object_type"], self.TYPE)
        self.failUnless(response.context["creation_form"])
   
    def test_create2(self):
        response = self.client.get("/object/create/",
                                   {"type" : self.TYPE, "reference" : "mapart",
                                    "revision" : "a", "name" : "MaPart"})

        self.assertEqual(response.status_code, 200)

    def test_display_attributes(self):
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, 200)
        self.failUnless(response.context["object_attributes"])
        attributes = dict(response.context["object_attributes"])
        # name : empty value
        self.assertEqual(attributes["name"], "")
        # owner and creator : self.user
        self.assertEqual(attributes["owner"], self.user)
        self.assertEqual(attributes["creator"], self.user)

    def test_lifecycle(self):
        response = self.client.get(self.base_url + "lifecycle/")
        self.assertEqual(response.status_code, 200)
        lifecycles = tuple(response.context["object_lifecycle"])
        wanted = (("draft", True), ("official", False), ("deprecated", False))
        self.assertEqual(lifecycles, wanted)
        # promote
        response = self.client.post(self.base_url + "lifecycle/", 
                                    {"action" : "PROMOTE"})
        self.assertEqual(response.status_code, 200)
        lifecycles = tuple(response.context["object_lifecycle"])
        wanted = (("draft", False), ("official", True), ("deprecated", False))
        self.assertEqual(lifecycles, wanted)
        # demote
        response = self.client.post(self.base_url + "lifecycle/", 
                                    {"action" : "DEMOTE"})
        self.assertEqual(response.status_code, 200)
        lifecycles = tuple(response.context["object_lifecycle"])
        wanted = (("draft", True), ("official", False), ("deprecated", False))
        self.assertEqual(lifecycles, wanted)

    def test_revisions(self):
        response = self.client.get(self.base_url + "revisions/")
        self.assertEqual(response.status_code, 200)
        revisions = response.context["revisions"]
        self.assertEqual(revisions, [self.controller.object])
        # check add_revision_form
        add_revision_form = response.context["add_revision_form"]
        self.assertEqual(add_revision_form.data, {"revision": "b"})


class SearchViewTest(CommonViewTest):

    def search(self, request):
        response = self.client.get("/home/", request) 
        self.assertEqual(response.status_code, 200)
        results = list(response.context["results"])
        results.sort(key=lambda r:r.pk)
        return results

    def test_forms(self):
        response = self.client.get("/home/")
        self.assertEqual(response.status_code, 200)
        # check if searchforms are present
        af = response.context["attributes_form"]
        eaf = response.context["extra_attributes_form"]
    
    def test_session_forms(self):
        "Tests if form field are kept between two search"
        response = self.client.get("/home/", {"revision" : "c", "name" : "a name"})
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/home/")
        self.assertEqual(response.status_code, 200)
        af = response.context["attributes_form"]
        self.assertEqual(af.data["revision"], "c")
        eaf = response.context["attributes_form"]
        self.assertEqual(af.data["name"], "a name")

    def test_empty(self):
        "Test a search with an empty database"
        # clear all plmobject so results is empty
        for obj in PLMObject.objects.all():
            obj.delete()
        results = self.search({"type" : self.TYPE}) 
        self.assertEqual(results, [])

    def test_one_result(self):
        "Test a search with one object in the database"
        results = self.search({"type" : self.TYPE}) 
        self.assertEqual(results, [self.controller.object])

    def test_plmobject(self):
        # add a plmobject : the search should return the same results
        PLMObject.objects.create(reference="aa", type="PLMObject", 
                                     revision="c", owner=self.user,
                                     creator=self.user)
        results = self.search({"type" : self.TYPE}) 
        self.assertEqual(results, [self.controller.object])
    
    def test_option_revision(self):
        # search with more options : revision
        results = self.search({"type" : self.TYPE,
                               "revision" : self.controller.revision}) 
        self.assertEqual(results, [self.controller.object])
        results = self.search({"type" : self.TYPE, "revision" : "____"}) 
        self.assertEqual(results, [])

    def test_option_name(self):
        # search with more options : name
        self.controller.name = "blabla"
        self.controller.save()
        results = self.search({"type" : self.TYPE,
                               "name" : self.controller.name}) 
        self.assertEqual(results, [self.controller.object])
        results = self.search({"type" : self.TYPE, "name" : "____"}) 
        self.assertEqual(results, [])

    def test_two_results(self):
        # add another object
        c2 = self.CONTROLLER.create("b", self.TYPE, "c", self.user, self.DATA)
        results = self.search({"type" : self.TYPE})
        c = self.controller
        wanted = [c.object, c2.object] if c.pk < c2.pk else [c2.object, c.object]
        self.assertEqual(results, wanted)

    # TODO : error cases

class HardDiskViewTest(ViewTest):
    TYPE = "HardDisk"
    DATA = {"capacity_in_go" : 500,
            "supplier" : "ASupplier"}
    
    def test_display_attributes2(self):
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, 200)
        self.failUnless(response.context["object_attributes"])
        attributes = dict(response.context["object_attributes"])
        self.assertEqual(attributes["capacity in go"], self.DATA["capacity_in_go"])
        self.assertEqual(attributes["supplier"], self.DATA["supplier"])
        self.assertEqual(attributes["tech details"], "")

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

