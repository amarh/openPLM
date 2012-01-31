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

from openPLM.plmapp import forms
from openPLM.plmapp.utils import level_to_sign_str
import openPLM.plmapp.models as m
from openPLM.plmapp.controllers import DocumentController, PartController, \
        UserController
from openPLM.plmapp.lifecycle import LifecycleList

from openPLM.plmapp.tests.base import BaseTestCase
        
class CommonViewTest(BaseTestCase):
    TYPE = "Part"
    CONTROLLER = PartController
    DATA = {}
    REFERENCE = "Part1"

    def setUp(self):
        super(CommonViewTest, self).setUp()
        self.client.post("/login/", {'username' : 'user', 'password' : 'password'})
        self.controller = self.CONTROLLER.create(self.REFERENCE, self.TYPE, "a",
                                                 self.user, self.DATA)
        self.base_url = "/object/%s/%s/%s/" % (self.controller.type,
                                              self.controller.reference,
                                              self.controller.revision)
        brian = User.objects.create(username="Brian", password="life")
        brian.get_profile().is_contributor = True
        brian.get_profile().save()
        self.brian = brian

    def post(self, url, data=None, follow=True, status_code=200,
            link=False, page=""):
        return self.get_or_post(self.client.post, url, data, follow, status_code,
                link, page)

    def get(self, url, data=None, follow=True, status_code=200,
            link=False, page=""):
        return self.get_or_post(self.client.get, url, data, follow, status_code,
                link, page)
    
    def get_or_post(self, func, url, data=None, follow=True, status_code=200,
            link=False, page=""):
        response = func(url, data or {}, follow=follow)
        self.assertEqual(response.status_code, status_code)
        if status_code == 200:
            self.assertEqual(link, response.context["link_creation"])
            if page:
                self.assertEqual(page, response.context["current_page"])
        return response

    def attach_to_official_document(self):
        u""" If :attr:`controller`` is a PartController, this method attachs
        an official document to it, so that it becomes promotable.

        Does nothing if :attr:`controller` is a DocumentController.
        """
        if self.controller.is_part:
            document = DocumentController.create("doc_1", "Document", "a",
                    self.user, self.DATA)
            document.add_file(self.get_file())
            document.promote()
            self.controller.attach_to_document(document)

class ViewTest(CommonViewTest):

    def test_home(self):
        response = self.get("/home/")
        
    def test_create_get(self):
        response = self.get("/object/create/", {"type" : self.TYPE})
        self.assertEqual(response.context["object_type"], self.TYPE)
        self.failUnless(response.context["creation_form"])
   
    def test_create_post(self):
        data = self.DATA.copy()
        data.update({
                "type" : self.TYPE,
                "reference" : "mapart",
                "revision" : "a",
                "name" : "MaPart",
                "group" : str(self.group.id),
                "lifecycle" : m.get_default_lifecycle().pk,
                "state" : m.get_default_state().pk,
                })
        model_cls = m.get_all_plmobjects()[self.TYPE]
        page = "files" if issubclass(model_cls, m.Document) else "attributes"
        response = self.post("/object/create/", data, page=page)
        obj = m.PLMObject.objects.get(type=self.TYPE, reference="mapart", revision="a")
        self.assertEqual(obj.id, response.context["obj"].id)
        self.assertEqual("MaPart", obj.name)
        self.assertEqual(self.user, obj.owner)
        self.assertEqual(self.user, obj.creator)

    def test_display_attributes(self):
        response = self.get(self.base_url + "attributes/", page="attributes")
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
        response = self.post(self.base_url + "modify/", data)
        obj = m.get_all_plmobjects()[self.TYPE].objects.all()[0]
        self.assertEqual(obj.name, data["name"])

    def test_lifecycle(self):
        self.attach_to_official_document()
        response = self.get(self.base_url + "lifecycle/")
        lifecycles = tuple(response.context["object_lifecycle"])
        wanted = (("draft", True, u'user'),
                  ("official", False, u'user'),
                  ("deprecated", False, None))
        self.assertEqual(lifecycles, wanted)
        # promote
        response = self.post(self.base_url + "lifecycle/", 
                            {"action" : "PROMOTE"})
        lifecycles = tuple(response.context["object_lifecycle"])
        wanted = (("draft", False, u'user'),
                  ("official", True, u'user'),
                  ("deprecated", False, None))
        self.assertEqual(lifecycles, wanted)
        # demote
        lcl = LifecycleList("diop", "official", "draft", 
                "issue1", "official", "deprecated")
        lc = m.Lifecycle.from_lifecyclelist(lcl)
        self.controller.lifecycle = lc
        self.controller.state = m.State.objects.get(name="draft")
        self.controller.save()
        self.controller.promote()
        self.assertEqual(self.controller.state.name, "issue1")
        response = self.post(self.base_url + "lifecycle/", 
                                    {"action" : "DEMOTE"})
        lifecycles = tuple(response.context["object_lifecycle"])
        wanted = (("draft", True, u'user'),
                  ("issue1", False, u'user'),
                  ("official", False, None),
                  ("deprecated", False, None))
        self.assertEqual(lifecycles, wanted)

    def test_revisions(self):
        response = self.get(self.base_url + "revisions/")
        revisions = response.context["revisions"]
        self.assertEqual(revisions, [self.controller.object])
        # check add_revision_form
        add_revision_form = response.context["add_revision_form"]
        self.assertEqual(add_revision_form.data, {"revision": "b"})
        response = self.post(self.base_url + "revisions/", {"revision" :"b"})
        m.get_all_plmobjects()[self.TYPE].objects.get(reference=self.controller.reference,
                revision="b")
    
    def test_history(self):
        response = self.get(self.base_url + "history/")

    def test_navigate_get(self):
        response = self.get(self.base_url + "navigate/")
        self.assertTrue(response.context["filter_object_form"])
        self.assertTrue(response.context["navigate_bool"])
        
    def test_navigate_post(self):
        data = dict.fromkeys(("child", "parents",
            "doc", "parents", "owner", "signer", "notified", "part",
            "ownede", "to_sign", "request_notification_from"), True)
        data["prog"] = "neato"
        response = self.post(self.base_url + "navigate/", data)
        self.assertTrue(response.context["filter_object_form"])
       
    def test_management(self):
        response = self.get(self.base_url + "management/", page="management")
        self.controller.set_owner(self.brian)
        response = self.get(self.base_url + "management/")
        self.assertFalse(response.context["is_notified"])
        form = response.context["notify_self_form"]
        self.assertEqual("User", form.initial["type"])
        self.assertEqual(self.user.username, form.initial["username"])

    def test_management_add_get(self):
        response = self.get(self.base_url + "management/add/",
               link=True, page="management")
        attach = response.context["attach"]
        self.assertEqual(self.controller.id, attach[0].id)
        self.assertEqual("delegate", attach[1])

    def test_management_add_post(self):
        data = dict(type="User", username=self.brian.username)
        response = self.post(self.base_url + "management/add/", data)
        self.assertTrue(m.PLMObjectUserLink.objects.filter(plmobject=self.controller.object,
            user=self.brian, role=m.ROLE_NOTIFIED))

    def test_management_replace_get(self):
        role = level_to_sign_str(0)
        self.controller.set_signer(self.brian, role)
        link = m.PLMObjectUserLink.objects.get(plmobject=self.controller.object,
            user=self.brian, role=role)
        response = self.get(self.base_url + "management/replace/%d/" % link.id,
                link=True, page="management")
        attach = response.context["attach"]
        self.assertEqual(self.controller.id, attach[0].id)
        self.assertEqual("delegate", attach[1])
    
    def test_management_replace_post(self):
        role = level_to_sign_str(0)
        self.controller.set_signer(self.brian, role)
        link = m.PLMObjectUserLink.objects.get(plmobject=self.controller.object,
            user=self.brian, role=role)
        data = dict(type="User", username=self.user.username)
        response = self.post(self.base_url + "management/replace/%d/" % link.id,
                        data)
        self.assertFalse(m.PLMObjectUserLink.objects.filter(plmobject=self.controller.object,
            user=self.brian, role=role))
        self.assertTrue(m.PLMObjectUserLink.objects.filter(plmobject=self.controller.object,
            user=self.user, role=role))

    def test_management_delete(self):
        self.controller.add_notified(self.brian)
        link = m.PLMObjectUserLink.objects.get(plmobject=self.controller.object,
            user=self.brian, role=m.ROLE_NOTIFIED)
        data = {"link_id" : link.id }
        response = self.post(self.base_url + "management/delete/", data)
        self.assertFalse(m.PLMObjectUserLink.objects.filter(plmobject=self.controller.object,
            user=self.brian, role=m.ROLE_NOTIFIED))


class DocumentViewTestCase(ViewTest):

    TYPE = "Document"
    CONTROLLER = DocumentController

    def test_related_parts_get(self):
        part = PartController.create("RefPart", "Part", "a", self.user, self.DATA)
        self.controller.attach_to_part(part)
        
        response = self.get(self.base_url + "parts/", page="parts")
        self.assertEqual([part.id],
                         [p.part.id for p in response.context["object_rel_part"]])
        
    def test_add_related_part_get(self):
        response = self.get(self.base_url + "parts/add/", link=True)
        self.assertTrue(isinstance(response.context["add_rel_part_form"],
                                   forms.AddRelPartForm))
        attach = response.context["attach"]
        self.assertEqual(self.controller.id, attach[0].id)
        self.assertEqual("attach_part", attach[1])

    def test_add_related_part_post(self):
        part = PartController.create("RefPart", "Part", "a", self.user, self.DATA)
        data = {
                "reference" : part.reference,
                "type" : part.type,
                "revision" : part.revision
                }
        response = self.post(self.base_url + "parts/add/", data)
        self.assertEqual([part.id],
                         [p.part.id for p in self.controller.get_attached_parts()])

    def test_files_empty_get(self):
        response = self.get(self.base_url + "files/", page="files")
        formset = response.context["file_formset"]
        self.assertEqual(0, formset.total_form_count())

    def test_files_get(self):
        self.controller.add_file(self.get_file())
        response = self.get(self.base_url + "files/", page="files")
        formset = response.context["file_formset"]
        self.assertEqual(1, formset.total_form_count())
       
    def test_files_post(self):
        df1 = self.controller.add_file(self.get_file())
        df2 = self.controller.add_file(self.get_file())
        data = {
                'form-0-document': self.controller.id,
                'form-0-id': df1.id,
                'form-0-delete' : 'on',
                'form-0-ORDER': '0',
                'form-1-document': self.controller.id,
                'form-1-id': df2.id,
                'form-1-ORDER': '1',
                'form-MAX_NUM_FORMS': '',
                'form-TOTAL_FORMS': 2, 
                'form-INITIAL_FORMS': 2,
                }
        response = self.post(self.base_url + "files/", data)
        self.assertEqual([df2.id], [df.id for df in self.controller.files])

    def test_add_file_get(self):
        response = self.get(self.base_url + "files/add/")
        self.assertTrue(isinstance(response.context["add_file_form"],
                                   forms.AddFileForm))

    def test_add_file_post(self):
        f = self.get_file(data="crumble")
        data = { "filename" : f }
        response = self.post(self.base_url + "files/add/", data)
        df = self.controller.files[0]
        self.assertEqual(df.filename, f.name)
        self.assertEqual("crumble", df.file.read())

    def test_lifecycle(self):
        self.controller.add_file(self.get_file())
        super(DocumentViewTestCase, self).test_lifecycle()

class PartViewTestCase(ViewTest):

    def test_children(self):
        child1 = PartController.create("c1", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child1, 10 , 20)
        child2 = PartController.create("c2", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child2, 10, 20)
        response = self.get(self.base_url + "BOM-child/", page="BOM-child")
        self.assertEqual(2, len(list(response.context["children"])))
        form = response.context["display_form"]

    def test_add_child(self):
        response = self.get(self.base_url + "BOM-child/add/", link=True)
        child1 = PartController.create("c1", "Part", "a", self.user, self.DATA)
        response = self.client.post(self.base_url + "BOM-child/add/",
                {"type": "Part", "reference":"c1", "revision":"a",
                    "quantity" : 10, "order" : 10, "unit" : "m"})
        self.assertEquals(1, len(self.controller.get_children()))

    def test_edit_children(self):
        child1 = PartController.create("c1", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child1, 10 , 20)
        response = self.get(self.base_url + "BOM-child/edit/")
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
            'form-0-unit' :  'cm',
        }
        response = self.post(self.base_url + "BOM-child/edit/", data)
        link = self.controller.get_children()[0].link
        self.assertEquals(45, link.order)
        self.assertEquals(45.0, link.quantity)
        self.assertEquals('cm', link.unit)

    def test_parents_empty(self):
        response = self.get(self.base_url + "parents/", page="parents")
        self.assertEqual(0, len(list(response.context["parents"])))
        
    def test_parents(self):
        p1 = PartController.create("c1", "Part", "a", self.user, self.DATA)
        p1.add_child(self.controller, 10, 20)
        p2 = PartController.create("c2", "Part", "a", self.user, self.DATA)
        p2.add_child(self.controller, 10, 20)
        response = self.get(self.base_url + "parents/", page="parents")
        self.assertEqual(2, len(list(response.context["parents"])))

    def test_doc_cad_empty(self):
        response = self.get(self.base_url + "doc-cad/", page="doc-cad")
        self.assertEqual(0, len(list(response.context["object_doc_cad"])))
    
    def test_doc_cad(self):
        doc1 = DocumentController.create("doc1", "Document", "a", self.user,
                self.DATA)
        doc2 = DocumentController.create("doc2", "Document", "a", self.user,
                self.DATA)
        self.controller.attach_to_document(doc1)
        self.controller.attach_to_document(doc2)
        response = self.get(self.base_url + "doc-cad/", page="doc-cad")
        self.assertEqual(2, len(list(response.context["object_doc_cad"])))

    def test_doc_add_add_get(self):
        response = self.get(self.base_url + "doc-cad/add/", link=True)
        self.assertEqual("attach_doc", response.context["attach"][1])

    def test_doc_add_add_post(self):
        doc1 = DocumentController.create("doc1", "Document", "a", self.user,
                self.DATA)
        data = {"type" : doc1.type, "reference" : doc1.reference,
                "revision" : doc1.revision } 
        response = self.post(self.base_url + "doc-cad/add/", data)
        document = self.controller.get_attached_documents()[0].document
        self.assertEqual(doc1.object, document)
        

class UserViewTestCase(CommonViewTest):

    def setUp(self):
        super(UserViewTestCase, self).setUp()
        self.user_url = "/user/%s/" % self.user.username
        self.controller = UserController(self.user, self.user)
        
    def test_user_attribute(self):
        response = self.get(self.user_url + "attributes/", page="attributes")
        attributes = dict((x.capitalize(), y) for (x,y) in 
                          response.context["object_attributes"])
        self.assertEqual(attributes["E-mail address"], self.user.email)
        self.assertTrue(response.context["is_owner"])

    def test_groups(self):
        response = self.get(self.user_url + "groups/")
        # TODO

    def test_part_doc_cads(self):
        response = self.get(self.user_url + "parts-doc-cad/")
        # TODO
        
    def test_history(self):
        response = self.get(self.user_url + "history/")
        
    def test_navigate(self):
        response = self.get(self.user_url + "navigate/")

    def test_sponsor_get(self):
        response = self.get(self.user_url + "delegation/sponsor/")
        form = response.context["sponsor_form"]
        self.assertEquals(set(g.id for g in self.user.groupinfo_owner.all()),
                set(g.id for g in form.fields["groups"].queryset.all()))

    def test_sponsor_post(self):
        data = dict(sponsor=self.user.id, 
                    username="loser", first_name="You", last_name="Lost",
                    email="you.lost@example.com", groups=[self.group.pk])
        response = self.post(self.user_url + "delegation/sponsor/", data)
        user = User.objects.get(username=data["username"])
        for attr in ("first_name", "last_name", "email"):
            self.assertEquals(data[attr], getattr(user, attr))
        self.assertTrue(user.get_profile().is_contributor)
        self.assertFalse(user.get_profile().is_administrator)
        self.assertTrue(user.groups.filter(id=self.group.id))

    def test_modify_get(self):
        response = self.get(self.user_url + "modify/")
        form = response.context["modification_form"]
        self.assertEqual(self.user.first_name, form.initial["first_name"])
        self.assertEqual(self.user.email, form.initial["email"])

    def test_modify_post(self):
        data = {"last_name":"Snow", "email":"user@test.com", "first_name":"John"}
        response = self.post(self.user_url + "modify/", data)
        user = User.objects.get(username=self.user.username)
        self.assertEqual("Snow", user.last_name)

    def test_password_get(self):
        response = self.get(self.user_url + "password/")
        self.assertTrue(response.context["modification_form"])

    def test_password_post(self):
        data = dict(old_password="password", new_password1="pw",
                new_password2="pw")
        response = self.post(self.user_url + "password/", data)
        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.check_password("pw"))

    def test_password_error(self):
        data = dict(old_password="error", new_password1="pw",
                new_password2="pw")
        response = self.post(self.user_url + "password/", data)
        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.check_password("password"))
        self.assertFalse(self.user.check_password("pw"))

    def test_delegation_get(self):
        response = self.get(self.user_url + "delegation/")
        
    def test_delegation_remove(self):
        self.controller.delegate(self.brian, m.ROLE_OWNER)
        link = self.controller.get_user_delegation_links()[0]
        data = {"link_id" : link.id }
        response = self.post(self.user_url + "delegation/", data)
        self.assertFalse(self.controller.get_user_delegation_links())
       
    def test_delegate_get(self):
        for role in ("owner", "notified"):
            url = self.user_url + "delegation/delegate/%s/" % role
            response = self.get(url, link=True, page="delegation")
            self.assertEqual(role, unicode(response.context["role"]))
    
    def test_delegate_sign_get(self):
        for level in ("all", "1", "2"):
            url = self.user_url + "delegation/delegate/sign/%s/" % str(level)
            response = self.get(url, link=True, page="delegation")
            role = unicode(response.context["role"])
            self.assertTrue(role.startswith("signer"))
            self.assertTrue(level in role)

    def test_delegate_post(self):
        data = { "type" : "User", "username": self.brian.username }
        for role in ("owner", "notified"):
            url = self.user_url + "delegation/delegate/%s/" % role
            response = self.post(url, data)
            m.DelegationLink.objects.get(role=role, delegator=self.user,
                    delegatee=self.brian)

    def test_delegate_sign_post(self):
        data = { "type" : "User", "username": self.brian.username }
        for level in xrange(1, 4):
            url = self.user_url + "delegation/delegate/sign/%d/" % level
            response = self.post(url, data)
            role = level_to_sign_str(level - 1)
            m.DelegationLink.objects.get(role=role,
                delegator=self.user, delegatee=self.brian)

    def test_delegate_sign_all_post(self):
        # sign all level
        data = { "type" : "User", "username": self.brian.username }
        url = self.user_url + "delegation/delegate/sign/all/"
        response = self.post(url, data)
        for level in xrange(2):
            role = level_to_sign_str(level)
            m.DelegationLink.objects.get(role=role, delegator=self.user,
                    delegatee=self.brian)
    
def sorted_objects(l):
    return sorted(l, key=lambda x: x.id)

class SearchViewTestCase(CommonViewTest):

    def get_query(self, request):
        if isinstance(request, basestring):
            return request
        query = u" ".join(u"%s:%s" % q for q in request.iteritems() if q[0] != "type")
        query = query or "*"
        return query

    def search(self, request, type=None):
        
        query = self.get_query(request)
        t = type or request["type"]
        response = self.get("/user/user/attributes/",
                {"type" : t, "q" : query}) 
        results = list(response.context["results"])
        results.sort(key=lambda r:r.object.pk)
        return [r.object for r in results]

    def test_forms(self):
        response = self.get("/user/user/attributes/")
        # check that searchform is present
        af = response.context["search_form"]
    
    def test_session_forms(self):
        "Tests if form field are kept between two search"
        data =  {"type" : "Part", "revision" : "c", "name" : "a name"}
        self.search(data)
        query = self.get_query(data)
        for x in range(4):
            response = self.get("/user/user/attributes/")
            af = response.context["search_form"]
            self.assertEqual(af.data["q"], query)

    def test_empty(self):
        "Test a search with an empty database"
        # clear all plmobject so results is empty
        for obj in m.PLMObject.objects.all():
            obj.delete()
        results = self.search({"type" : self.TYPE}) 
        self.assertEqual(results, [])

    def test_one_result(self):
        "Test a search with one object in the database"
        results = self.search({"type" : self.TYPE}) 
        self.assertEqual(results, [self.controller.object])

    def test_plmobject(self):
        # add a plmobject : the search should return the same results
        m.PLMObject.objects.create(reference="aa", type="PLMObject", 
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
        self.assertEqual(results, sorted_objects([c.object, c2.object]))

    def test_search_or(self):
        c2 = self.CONTROLLER.create("value2", self.TYPE, "c", self.user, self.DATA)
        c3 = self.CONTROLLER.create("value3", self.TYPE, "c", self.user, self.DATA)
        results = self.search("%s OR %s" % (self.controller.reference, c2.reference),
                self.TYPE)
        self.assertEqual(sorted_objects([self.controller.object, c2.object]),
                         sorted_objects(results)) 

    def test_search_and(self):
        c2 = self.CONTROLLER.create("value2", self.TYPE, "c", self.user, self.DATA)
        c3 = self.CONTROLLER.create("value3", self.TYPE, "c", self.user, self.DATA)
        results = self.search("%s AND %s" % (self.controller.reference, c2.reference),
                self.TYPE)
        self.assertEqual([], results) 
        results = self.search("value2 AND revision:c", self.TYPE)
        self.assertEqual([c2.object], results)

    def test_search_lisp_is_back(self):
        c2 = self.CONTROLLER.create("value2", self.TYPE, "c", self.user, self.DATA)
        c3 = self.CONTROLLER.create("value3", self.TYPE, "c", self.user, self.DATA)
        results = self.search("((%s) AND (%s) ) OR (*)" % (self.controller.reference,
            c2.reference), self.TYPE)
        self.assertEqual(3, len(results))

    def test_search_dash(self):
        for i in xrange(6):
            self.CONTROLLER.create("val-0%d" % i, self.TYPE, "c",
                    self.user, self.DATA)
        
        self.CONTROLLER.create("val-0i-5", self.TYPE, "c", self.user, self.DATA)
        c = self.CONTROLLER.create("0i-5", self.TYPE, "c", self.user, self.DATA)
        results = self.search("val-0*", self.TYPE)
        self.assertEqual(7, len(results))
        self.assertTrue(c.object not in results) 

    def test_search_numbers(self):
        """ Tests that 1759 matches 001759. (see ticket #69). """

        c2 = self.CONTROLLER.create("part-001759", self.TYPE, "c", self.user, self.DATA)
        results = self.search("1759", self.TYPE)
        self.assertEqual([c2.object], results) 
        c3 = self.CONTROLLER.create("part-0001759", self.TYPE, "c", self.user, self.DATA)
        results = self.search("1759", self.TYPE)
        self.assertEqual([c2.object, c3.object], results) 

    def test_search_all(self):
        for i in xrange(6):
            self.CONTROLLER.create("val-0%d" % i, self.TYPE, "c",
                    self.user, self.DATA)
        results = self.search("*", self.TYPE)
        self.assertEqual(set(m.Part.objects.all()), set(results))

    def test_search_not(self):
        self.controller.name = "abcdef"
        self.controller.save()
        results = self.search("NOT %s" % self.controller.name, self.TYPE)
        self.assertEqual([], results)
        results = self.search("NOT nothing", self.TYPE)
        self.assertEqual([self.controller.object], results)


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
        self.group = m.GroupInfo(name="grp", owner=self.user, creator=self.user,
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
        obj = m.get_all_plmobjects()[self.TYPE].objects.all()[0]
        self.assertEqual(obj.name, '')
        self.assertEqual(response.template.name, "error.html")

class SpecialCharactersPartViewTestCase(PartViewTestCase):
    REFERENCE = u"Pa *-\xc5\x93\xc3\xa9'"


class SpecialCharactersDocumentViewTestCase(DocumentViewTestCase):
    REFERENCE = u"Pa *-\xc5\x93\xc3\xa9'"

