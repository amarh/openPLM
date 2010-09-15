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
from django.contrib.auth.models import User
from django.test import TestCase

from openPLM.plmapp.utils import *
from openPLM.plmapp.models import *
from openPLM.plmapp.controllers import *
from openPLM.plmapp.lifecycle import *
from openPLM.computer.models import *
from openPLM.office.models import *
from openPLM.cad.models import *
        
class CommonViewTest(TestCase):
    TYPE = "Part"
    CONTROLLER = PartController
    DATA = {}

    def setUp(self):
        self.user = User(username="user")
        self.user.set_password("password")
        self.user.save()
        self.user.get_profile().is_contributor = True
        self.user.get_profile().save()
        self.client.post("/login/", {'username' : 'user', 'password' : 'password'})
        self.controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                                 self.user, self.DATA)
        self.base_url = "/object/%s/%s/%s/" % (self.controller.type,
                                              self.controller.reference,
                                              self.controller.revision)

class ViewTest(CommonViewTest):

    def test_home(self):
        response = self.client.get("/home/", follow=True)
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
        response = self.client.get(self.base_url + "attributes/")
        self.assertEqual(response.status_code,  200)
        self.failUnless(response.context["object_attributes"])
        attributes = dict((x.capitalize(), y) for (x,y) in 
                          response.context["object_attributes"])
        # name : empty value
        self.assertEqual(attributes["Name"], "")
        # owner and creator : self.user
        self.assertEqual(attributes["Owner"], self.user)
        self.assertEqual(attributes["Creator"], self.user)

    def test_edit_attributes(self):
        data = self.DATA.copy()
        data.update(type=self.TYPE, name="new_name")
        response = self.client.post(self.base_url + "modify/", data, follow=True)
        self.assertEqual(response.status_code,  200)
        obj = get_all_plmobjects()[self.TYPE].objects.all()[0]
        self.assertEqual(obj.name, data["name"])

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
        response = self.client.get("/user/user/attributes/", request) 
        self.assertEqual(response.status_code, 200)
        results = list(response.context["results"])
        results.sort(key=lambda r:r.pk)
        return results

    def test_forms(self):
        response = self.client.get("/user/user/attributes/")
        self.assertEqual(response.status_code, 200)
        # check if searchforms are present
        af = response.context["attributes_form"]
        eaf = response.context["type_form"]
    
    def test_session_forms(self):
        "Tests if form field are kept between two search"
        response = self.client.get("/user/user/attributes/", {"type" : "Part",
                                "revision" : "c", "name" : "a name"})
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/user/user/attributes/")
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
        response = self.client.get(self.base_url + "attributes/")
        self.assertEqual(response.status_code, 200)
        self.failUnless(response.context["object_attributes"])
        attributes = dict(response.context["object_attributes"])
        self.assertEqual(attributes["capacity in go"], self.DATA["capacity_in_go"])
        self.assertEqual(attributes["supplier"], self.DATA["supplier"])
        self.assertEqual(attributes["tech details"], "")

class MechantUserViewTest(TestCase):
    """
    Tests when an user try an unauthorized action
    """

    TYPE = "Part"
    CONTROLLER = PartController
    DATA = {}
    
    def setUp(self):
        owner = User(username="owner")
        owner.set_password("password")
        owner.save()
        owner.get_profile().is_contributor = True
        owner.get_profile().save()
        self.user = User(username="user")
        self.user.set_password("password")
        self.user.save()
        self.user.get_profile().is_contributor = True
        self.user.get_profile().save()
        self.client.post("/login/", {'username' : 'user', 'password' : 'password'})
        self.controller = self.CONTROLLER.create("Part1", "Part", "a", owner)
        self.base_url = "/object/%s/%s/%s/" % (self.controller.type,
                                              self.controller.reference,
                                              self.controller.revision)
    
    def test_edit_attributes(self):
        data = self.DATA.copy()
        data.update(type=self.TYPE, name="new_name")
        response = self.client.post(self.base_url + "modify/", data, follow=True)
        self.assertEqual(response.status_code,  200)
        obj = get_all_plmobjects()[self.TYPE].objects.all()[0]
        self.assertEqual(obj.name, '')
        self.assertEqual(response.template.name, "error.html")

