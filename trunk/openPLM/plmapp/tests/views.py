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

from openPLM.plmapp.tests.base import BaseTestCase
        
class CommonViewTest(BaseTestCase):
    TYPE = "Part"
    CONTROLLER = PartController
    DATA = {}

    def setUp(self):
        super(CommonViewTest, self).setUp()
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
                                    "revision" : "a", "name" : "MaPart",
                                    "group" : str(self.group.id)})

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
        lcl = LifecycleList("diop", "official", "draft", 
                "issue1", "official", "deprecated")
        lc = Lifecycle.from_lifecyclelist(lcl)
        self.controller.lifecycle = lc
        self.controller.state = State.objects.get(name="draft")
        self.controller.save()
        self.controller.promote()
        self.assertEqual(self.controller.state.name, "issue1")
        response = self.client.post(self.base_url + "lifecycle/", 
                                    {"action" : "DEMOTE"})
        self.assertEqual(response.status_code, 200)
        lifecycles = tuple(response.context["object_lifecycle"])
        wanted = (("draft", True), ("issue1", False), ("official", False),
                ("deprecated", False))
        self.assertEqual(lifecycles, wanted)

    def test_revisions(self):
        response = self.client.get(self.base_url + "revisions/")
        self.assertEqual(response.status_code, 200)
        revisions = response.context["revisions"]
        self.assertEqual(revisions, [self.controller.object])
        # check add_revision_form
        add_revision_form = response.context["add_revision_form"]
        self.assertEqual(add_revision_form.data, {"revision": "b"})
        response = self.client.post(self.base_url + "revisions/", {"revision" :"b"})
        self.assertEqual(response.status_code, 200)
        get_all_plmobjects()[self.TYPE].objects.get(reference=self.controller.reference,
                revision="b")
    
    def test_history(self):
        response = self.client.get(self.base_url + "history/")
        self.assertEqual(response.status_code,  200)

    def test_navigate(self):
        response = self.client.get(self.base_url + "navigate/")
        self.assertEqual(response.status_code,  200)

class PartViewTestCase(CommonViewTest):

    def test_children(self):
        child1 = PartController.create("c1", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child1, 10 , 20)
        child2 = PartController.create("c2", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child2, 10, 20)
        response = self.client.get(self.base_url + "BOM-child/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(2, len(list(response.context["children"])))
        self.assertEqual("BOM-child", response.context["current_page"])
        form = response.context["display_form"]

    def test_add_child(self):
        response = self.client.get(self.base_url + "BOM-child/add/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["link_creation"])
        child1 = PartController.create("c1", "Part", "a", self.user, self.DATA)
        response = self.client.post(self.base_url + "BOM-child/add/",
                {"type": "Part", "reference":"c1", "revision":"a",
                 "quantity" : 10, "order" : 10 })
        self.assertEquals(1, len(self.controller.get_children()))

    def test_edit_children(self):
        child1 = PartController.create("c1", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child1, 10 , 20)
        response = self.client.get(self.base_url + "BOM-child/edit/")
        self.assertEqual(response.status_code, 200)
        formset = response.context["children_formset"]
        data = {
            'form-TOTAL_FORMS': u'1',
            'form-INITIAL_FORMS': u'1',
            'form-MAX_NUM_FORMS': u'',
            'form-0-child' :   child1.id,
            'form-0-id'  : self.controller.get_children()[0].link.id,
            'form-0-order'  :  45,
            'form-0-parent' :  self.controller.id,
            'form-0-quantity' :  '45.0',
        }
        response = self.client.post(self.base_url + "BOM-child/edit/", data)
        link = self.controller.get_children()[0].link
        self.assertEquals(45, link.order)
        self.assertEquals(45.0, link.quantity)

    def test_parents_empty(self):
        response = self.client.get(self.base_url + "parents/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(list(response.context["parents"])))
        self.assertEqual("parents", response.context["current_page"])
        
    def test_parents(self):
        p1 = PartController.create("c1", "Part", "a", self.user, self.DATA)
        p1.add_child(self.controller, 10, 20)
        p2 = PartController.create("c2", "Part", "a", self.user, self.DATA)
        p2.add_child(self.controller, 10, 20)
        response = self.client.get(self.base_url + "parents/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(2, len(list(response.context["parents"])))
        self.assertEqual("parents", response.context["current_page"])

    def test_doc_cad_empty(self):
        response = self.client.get(self.base_url + "doc-cad/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(list(response.context["object_doc_cad"])))
        self.assertEqual("doc-cad", response.context["current_page"])
    
    def test_doc_cad(self):
        doc1 = DocumentController.create("doc1", "Document", "a", self.user,
                self.DATA)
        doc2 = DocumentController.create("doc2", "Document", "a", self.user,
                self.DATA)
        self.controller.attach_to_document(doc1)
        self.controller.attach_to_document(doc2)
        response = self.client.get(self.base_url + "doc-cad/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(2, len(list(response.context["object_doc_cad"])))
        self.assertEqual("doc-cad", response.context["current_page"])

    def test_doc_add_add_get(self):
        response = self.client.get(self.base_url + "doc-cad/add/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["link_creation"])
        self.assertEqual("attach_doc", response.context["attach"][1])

    def test_doc_add_add_post(self):
        doc1 = DocumentController.create("doc1", "Document", "a", self.user,
                self.DATA)
        data = {"type" : doc1.type, "reference" : doc1.reference,
                "revision" : doc1.revision } 
        response = self.client.post(self.base_url + "doc-cad/add/", data, follow=True)
        self.assertEqual(response.status_code, 200)
        document = self.controller.get_attached_documents()[0].document
        self.assertEqual(doc1.object, document)
        

class UserViewTestCase(CommonViewTest):
    
    def setUp(self):
        super(UserViewTestCase, self).setUp()
        self.user_url = "/user/%s/" % self.user.username

    
    def test_user_attribute(self):
        response = self.client.get(self.user_url + "attributes/")
        self.assertEqual(response.status_code,  200)
        self.failUnless(response.context["object_attributes"])
        attributes = dict((x.capitalize(), y) for (x,y) in 
                          response.context["object_attributes"])
        self.assertEqual(attributes["E-mail address"], self.user.email)
        self.assertTrue(response.context["is_owner"])

    def test_delegation(self):
        response = self.client.get(self.user_url + "delegation/")
        self.assertEqual(response.status_code,  200)
        # TODO

    def test_groups(self):
        response = self.client.get(self.user_url + "groups/")
        self.assertEqual(response.status_code,  200)
        # TODO

    def test_part_doc_cads(self):
        response = self.client.get(self.user_url + "parts-doc-cad/")
        self.assertEqual(response.status_code,  200)
        # TODO
        
    def test_history(self):
        response = self.client.get(self.user_url + "history/")
        self.assertEqual(response.status_code,  200)
        
    def test_navigate(self):
        response = self.client.get(self.user_url + "navigate/")
        self.assertEqual(response.status_code,  200)

    def test_sponsor_get(self):
        response = self.client.get(self.user_url + "delegation/sponsor/")
        self.assertEqual(response.status_code,  200)
        form = response.context["sponsor_form"]
        self.assertEquals(set(g.id for g in self.user.groupinfo_owner.all()),
                set(g.id for g in form.fields["groups"].queryset.all()))

    def test_sponsor_post(self):
        data = dict(sponsor=self.user.id, 
                    username="loser", first_name="You", last_name="Lost",
                    email="you.lost@example.com", groups=[self.group.pk])
        response = self.client.post(self.user_url + "delegation/sponsor/", data,
                follow=True)
        self.assertEqual(response.status_code,  200)
        user = User.objects.get(username=data["username"])
        for attr in ("first_name", "last_name", "email"):
            self.assertEquals(data[attr], getattr(user, attr))
        self.assertTrue(user.get_profile().is_contributor)
        self.assertFalse(user.get_profile().is_administrator)
        self.assertTrue(user.groups.filter(id=self.group.id))

    def test_modify_get(self):
        response = self.client.get(self.user_url + "modify/")
        self.assertEqual(response.status_code,  200)
        form = response.context["modification_form"]
        self.assertEqual(self.user.first_name, form.initial["first_name"])
        self.assertEqual(self.user.email, form.initial["email"])

    def test_modify_post(self):
        data = {"last_name":"Snow", "email":"user@test.com", "first_name":"John"}
        response = self.client.post(self.user_url + "modify/", data,
                follow=True)
        self.assertEqual(response.status_code,  200)
        user = User.objects.get(username=self.user.username)
        self.assertEqual("Snow", user.last_name)

from django.core.management import call_command
class SearchViewTest(CommonViewTest):

    def search(self, request):
        # rebuild the index
        call_command("rebuild_index", interactive=False)

        query = u" ".join(u"%s:%s" % q for q in request.iteritems() if q[0] != "type")
        query = query or "*"
        response = self.client.get("/user/user/attributes/", {"type" : request["type"],
                "q" : query}) 
        self.assertEqual(response.status_code, 200)
        results = list(response.context["results"])
        results.sort(key=lambda r:r.object.pk)
        return [r.object for r in results]

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
                                     creator=self.user, group=self.group)
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
        self.group = GroupInfo(name="grp", owner=self.user, creator=self.user,
                description="grp")
        self.group.save()
        self.user.groups.add(self.group)
        self.client.post("/login/", {'username' : 'user', 'password' : 'password'})
        self.controller = self.CONTROLLER.create("Part1", "Part", "a", owner,
                {"group":self.group})
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

