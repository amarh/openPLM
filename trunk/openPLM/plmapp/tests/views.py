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
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase

from openPLM.plmapp import forms
from openPLM.plmapp.utils import level_to_sign_str
import openPLM.plmapp.models as m
from openPLM.plmapp.controllers import DocumentController, PartController, \
        UserController, GroupController
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
        brian = User.objects.create_user(username="Brian", password="life",
                email="brian@example.net")
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

        Returns the created document (a controller) or None.
        """
        if self.controller.is_part:
            document = DocumentController.create("doc_1", "Document", "a",
                    self.user, self.DATA)
            document.add_file(self.get_file())
            document.promote()
            self.controller.attach_to_document(document)
            return document
        return None

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

    def test_create_post_error_same_reference(self):
        """
        Tests that the creation of an object with the same type and
        reference but a different revision is forbidden.
        """
        data = self.DATA.copy()
        ref = self.controller.reference
        rev = "a new revision" 
        data.update({
                "type" : self.TYPE,
                "reference" : ref, 
                "revision" : rev,
                "name" : "An invalid object",
                "group" : str(self.group.id),
                "lifecycle" : m.get_default_lifecycle().pk,
                "state" : m.get_default_state().pk,
                })
        model_cls = m.get_all_plmobjects()[self.TYPE]
        response = self.post("/object/create/", data)
        qset = m.PLMObject.objects.filter(type=self.TYPE,
                reference=ref, revision=ref)
        self.assertFalse(response.context["creation_form"].is_valid())
        self.assertFalse(qset.exists())

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

    def test_edit_attributes_get(self):
        response = self.get(self.base_url + "modify/")
        form = response.context["modification_form"]
        self.assertTrue("name" in form.fields)

    def test_edit_attributes_post(self):
        data = self.DATA.copy()
        data.update(type=self.TYPE, name="new_name")
        response = self.post(self.base_url + "modify/", data)
        obj = m.get_all_plmobjects()[self.TYPE].objects.all()[0]
        self.assertEqual(obj.name, data["name"])

    def test_edit_attributes_post_error(self):
        # the name is too looonnnnnnngggggg
        name = self.controller.name
        data = self.DATA.copy()
        data.update(type=self.TYPE, name="new_name" * 300)
        response = self.post(self.base_url + "modify/", data)
        obj = m.get_all_plmobjects()[self.TYPE].objects.all()[0]
        self.assertEqual(obj.name, name)
        form = response.context["modification_form"]
        self.assertFalse(form.is_valid())

    def test_lifecycle(self):
        self.attach_to_official_document()
        response = self.get(self.base_url + "lifecycle/")
        lifecycles = tuple(response.context["object_lifecycle"])
        wanted = (("draft", True, u'user'),
                  ("official", False, u'user'),
                  ("deprecated", False, None))
        self.assertEqual(lifecycles, wanted)
        # promote
        response = self.post(self.base_url + "lifecycle/apply/", 
                {"action" : "PROMOTE", "password":"password"})
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
        response = self.post(self.base_url + "lifecycle/apply/", 
                {"action" : "DEMOTE", "password":"password"})
        lifecycles = tuple(response.context["object_lifecycle"])
        wanted = (("draft", True, u'user'),
                  ("issue1", False, u'user'),
                  ("official", False, None),
                  ("deprecated", False, None))
        self.assertEqual(lifecycles, wanted)

    def test_lifecycle_bad_password(self):
        self.attach_to_official_document()
        response = self.get(self.base_url + "lifecycle/")
        lifecycles = tuple(response.context["object_lifecycle"])
        wanted = (("draft", True, u'user'),
                  ("official", False, u'user'),
                  ("deprecated", False, None))
        self.assertEqual(lifecycles, wanted)
        # try to promote
        response = self.post(self.base_url + "lifecycle/apply/", 
                {"action" : "PROMOTE", "password":"wrong_password"})
        lifecycles = tuple(response.context["object_lifecycle"])
        self.assertEqual(lifecycles, wanted)
        self.assertFalse(response.context["password_form"].is_valid())

    def test_revisions_get(self):
        response = self.get(self.base_url + "revisions/")
        revisions = response.context["revisions"]
        self.assertEqual(revisions, [self.controller.object])
        self.assertTrue(response.context["add_revision_form"] is not None)
        # add a new revision
        rev = self.controller.revise("jf")
        response = self.get(self.base_url + "revisions/")
        revisions = response.context["revisions"]
        self.assertEqual(revisions, [self.controller.object, rev.plmobject_ptr])
        self.assertTrue(response.context["add_revision_form"] is None)
    
    def test_history(self):
        response = self.get(self.base_url + "history/")
        history = response.context["object_history"]
        # it should contains at least one item
        self.assertTrue(history)
        # edit the controller and checks that the history grows
        self.controller.name = "new name"
        self.controller.save()
        response = self.get(self.base_url + "history/")
        history2 = response.context["object_history"]
        self.failUnless(len(history2) > len(history))
        # create a new revision: both should appear in the history 
        revb = self.controller.revise("new_revision")
        response = self.get(self.base_url + "history/")
        history3 = response.context["object_history"]
        self.assertTrue([x for x in history3 if x.plmobject.id == self.controller.id])
        self.assertTrue([x for x in history3 if x.plmobject.id == revb.id])
        # also check revb/history/ page
        response = self.get(revb.plmobject_url + "history/")
        history4 = response.context["object_history"]
        self.assertTrue([x for x in history4 if x.plmobject.id == self.controller.id])
        self.assertTrue([x for x in history4 if x.plmobject.id == revb.id])

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
                         [p.part.id for p in response.context["all_parts"]])
        self.assertEqual([part.id],
            [f.instance.part.id for f in response.context["parts_formset"].forms])
        
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

    def test_checkin_get(self):
        df1 = self.controller.add_file(self.get_file())
        self.controller.lock(df1)
        response = self.get(self.base_url + "files/checkin/%d/" % df1.id)
        form = response.context["add_file_form"]

    def test_checkin_post(self):
        df1 = self.controller.add_file(self.get_file())
        self.controller.lock(df1)
        mock_file = self.get_file(data="robert")
        # plop is here so that django see a post request
        # it's not a problem since a real browser will also send a
        # csrf token
        response = self.post(self.base_url + "files/checkin/%d/" % df1.id,
                dict(filename=mock_file, plop="m"))
        files = self.controller.files
        self.assertEqual(1, files.count())
        df = files[0]
        self.assertFalse(df.locked)
        self.assertEqual("robert", df.file.read())

    def test_checkout(self):
        df1 = self.controller.add_file(self.get_file(data="oh oh oh"))
        response = self.client.get(self.base_url + "files/checkout/%d/" % df1.id)
        files = self.controller.files
        self.assertEqual(1, files.count())
        df = files[0]
        self.assertTrue(df.locked)
        self.assertEqual("oh oh oh", response.content)

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

    def test_revise_no_attached_part_get(self):
        """
        Tests the "revisions/" page and checks that if the document has no
        attached parts, it is not necessary to confirm the form.
        """
        response = self.get(self.base_url + "revisions/")
        # checks that is not necessary to confirm the revision 
        self.assertFalse(response.context["confirmation"])

    def test_revise_no_attached_part_post(self):
        """
        Tests a post request to revise a document which has no attached parts.
        """
        response = self.post(self.base_url + "revisions/",
                {"revision" : "b"})
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0]
        self.assertEqual("b", rev.revision)

    def test_revise_one_attached_part_get(self):
        """
        Tests a get request to revise a document which has one attached part.
        This part must be suggested when the user revises the document.
        """
        part = PartController.create("RefPart", "Part", "a", self.user, self.DATA)
        self.controller.attach_to_part(part)
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertTrue(response.context["confirmation"])
        formset = response.context["part_formset"]
        self.assertEqual(1, formset.total_form_count())
        form = formset.forms[0]
        self.assertTrue(form.fields["selected"].initial)
        self.assertEqual(part.id, form.instance.id)

    def test_revise_one_attached_part_post_selected(self):
        """
        Tests a post request to revise a document with one attached part which
        is selected.
        """
        part = PartController.create("RefPart", "Part", "a", self.user, self.DATA)
        self.controller.attach_to_part(part)
        data = { "revision" : "b",
                 "form-TOTAL_FORMS" : "1",
                 "form-INITIAL_FORMS" : "1",
                 "form-0-selected" : "on",
                 "form-0-plmobject_ptr" : part.id,
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].document
        self.assertEqual("b", rev.revision)
        # ensure part is still attached to the old revision
        parts = self.controller.get_attached_parts().values_list("part", flat=True)
        self.assertEqual([part.id], list(parts))
        # ensure part is attached to the new revision
        parts = rev.documentpartlink_document.values_list("part", flat=True)
        self.assertEqual([part.id], list(parts))
        # ensure both documents are attached to the part
        self.assertEqual([self.controller.id, rev.id],
            sorted(part.get_attached_documents().values_list("document", flat=True)))

    def test_revise_one_attached_part_post_unselected(self):
        """
        Tests a post request to revise a document with one attached part which
        is not selected.
        """
        part = PartController.create("RefPart", "Part", "a", self.user, self.DATA)
        self.controller.attach_to_part(part)
        data = { "revision" : "b",
                 "form-TOTAL_FORMS" : "1",
                 "form-INITIAL_FORMS" : "1",
                 "form-0-selected" : "",
                 "form-0-plmobject_ptr" : part.id,
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].document
        self.assertEqual("b", rev.revision)
        # ensure part is still attached to the old revision
        parts = self.controller.get_attached_parts().values_list("part", flat=True)
        self.assertEqual([part.id], list(parts))
        # ensure part is not attached to the new revision
        self.assertFalse(bool(rev.documentpartlink_document.all()))
        # ensure only the old revision is attached to part 
        self.assertEqual([self.controller.id],
            list(part.get_attached_documents().values_list("document", flat=True)))

    def test_revise_two_attached_parts_get(self):
        """
        Tests a get request to revise a document with two attached parts.
        One part is a draft, the other is official.
        """
        p1 = PartController.create("RefPart", "Part", "a", self.user, self.DATA)
        self.controller.attach_to_part(p1)
        p2 = PartController.create("part_2", "Part", "a", self.user, self.DATA)
        self.controller.attach_to_part(p2)
        p2.object.is_promotable = lambda: True
        p2.promote()
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertTrue(response.context["confirmation"])
        formset = response.context["part_formset"]
        self.assertEqual(2, formset.total_form_count())
        form1, form2 = formset.forms
        self.assertTrue(form1.fields["selected"].initial)
        self.assertTrue(form2.fields["selected"].initial)
        self.assertEqual([p1.id, p2.id], sorted([form1.instance.id, form2.instance.id]))

    def test_revise_two_attached_parts_post(self):
        """
        Tests a post request to revise a document with two attached parts.
        One part is a draft and not selected, the other is official and selected.
        """
        p1 = PartController.create("RefPart", "Part", "a", self.user, self.DATA)
        self.controller.attach_to_part(p1)
        p2 = PartController.create("part_2", "Part", "a", self.user, self.DATA)
        self.controller.attach_to_part(p2)
        p2.object.is_promotable = lambda: True
        p2.promote()
        data = {
            "revision" : "b",
             "form-TOTAL_FORMS" : "2",
             "form-INITIAL_FORMS" : "2",
             "form-0-selected" : "",
             "form-0-plmobject_ptr" : p1.id,
             "form-1-selected" : "on",
             "form-1-plmobject_ptr" : p2.id,
             }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].document
        self.assertEqual("b", rev.revision)
        # ensure p1 and p2 are still attached to the old revision
        parts = self.controller.get_attached_parts().values_list("part", flat=True)
        self.assertEqual([p1.id, p2.id], sorted(parts))
        # ensure p2 is attached to the new revision
        parts = rev.documentpartlink_document.values_list("part", flat=True)
        self.assertEqual([p2.id], list(parts))
        # ensure both documents are attached to p2
        self.assertEqual([self.controller.id, rev.id],
            sorted(p2.get_attached_documents().values_list("document", flat=True)))

    def test_revise_one_deprecated_part_attached_get(self):
        """
        Tests a get request to revise a document which has one deprecated 
        attached part.
        This part must not be suggested when the user revises the document.
        """
        part = PartController.create("RefPart", "Part", "a", self.user, self.DATA)
        self.controller.attach_to_part(part)
        part.object.state = part.lifecycle.last_state
        part.object.save()
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertFalse(response.context["confirmation"])

    def test_revise_one_deprecated_part_attached_post(self):
        """
        Tests a post request to revise a document which has one deprecated 
        attached part.
        This part must not be suggested when the user revises the document.
        """
        part = PartController.create("RefPart", "Part", "a", self.user, self.DATA)
        self.controller.attach_to_part(part)
        part.object.state = part.lifecycle.last_state
        part.object.save()
        data = { "revision" : "b",
                 "form-TOTAL_FORMS" : "1",
                 "form-INITIAL_FORMS" : "1",
                 "form-0-selected" : "",
                 "form-0-plmobject_ptr" : part.id,
                 }
        response = self.post(self.base_url + "revisions/", data)
        # even if we submit a formset, it should not be parsed
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].document
        # ensure part is still attached to the old revision
        parts = self.controller.get_attached_parts().values_list("part", flat=True)
        self.assertEqual([part.id], list(parts))
        # ensure part is not attached to the new revision
        self.assertFalse(bool(rev.documentpartlink_document.all()))
        # ensure only the old revision is attached to part 
        self.assertEqual([self.controller.id],
            list(part.get_attached_documents().values_list("document", flat=True)))

    def test_revise_one_attached_revised_part_get(self):
        """
        Tests a get request to revise a document which has one attached part.
        The part has been revised and so its revision must be suggested and
        the part must not be suggested when the user revises the document.
        """
        part = PartController.create("RefPart", "Part", "a", self.user, self.DATA)
        self.controller.attach_to_part(part)
        p2 = part.revise("b")
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertTrue(response.context["confirmation"])
        formset = response.context["part_formset"]
        self.assertEqual(1, formset.total_form_count())
        form = formset.forms[0]
        self.assertTrue(form.fields["selected"].initial)
        self.assertEqual(p2.id, form.instance.id)

    def test_revise_one_attached_revised_part_post(self):
        """
        Tests a post request to revise a document which has one attached part.
        The part has been revised and its revision is selected.
        """
        part = PartController.create("RefPart", "Part", "a", self.user, self.DATA)
        self.controller.attach_to_part(part)
        p2 = part.revise("b")
        data = { "revision" : "b",
                 "form-TOTAL_FORMS" : "1",
                 "form-INITIAL_FORMS" : "1",
                 "form-0-selected" : "on",
                 "form-0-plmobject_ptr" : p2.id,
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].document
        self.assertEqual("b", rev.revision)
        # ensure part is still attached to the old revision
        parts = self.controller.get_attached_parts().values_list("part", flat=True)
        self.assertEqual([part.id], list(parts))
        # ensure p2 is attached to the new revision
        parts = rev.documentpartlink_document.values_list("part", flat=True)
        self.assertEqual([p2.id], list(parts))

    def test_revise_one_attached_revised_part_post_error(self):
        """
        Tests a post request to revise a document which has one attached part.
        The part has been revised and has been selected instead of its revision. 
        """
        part = PartController.create("RefPart", "Part", "a", self.user, self.DATA)
        self.controller.attach_to_part(part)
        p2 = part.revise("b")
        data = { "revision" : "b",
                 "form-TOTAL_FORMS" : "1",
                 "form-INITIAL_FORMS" : "1",
                 "form-0-selected" : "on",
                 "form-0-plmobject_ptr" : part.id,
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        # no revisions have been created
        self.assertEqual([], revisions)
        # ensure part is still attached to the old revision
        parts = self.controller.get_attached_parts().values_list("part", flat=True)
        self.assertEqual([part.id], list(parts))


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
        self.assertEqual(0, len(list(response.context["all_docs"])))
    
    def test_doc_cad(self):
        doc1 = DocumentController.create("doc1", "Document", "a", self.user,
                self.DATA)
        doc2 = DocumentController.create("doc2", "Document", "a", self.user,
                self.DATA)
        self.controller.attach_to_document(doc1)
        self.controller.attach_to_document(doc2)
        doc2.object.state = doc2.object.lifecycle.last_state
        doc2.object.save()
        response = self.get(self.base_url + "doc-cad/", page="doc-cad")
        self.assertEqual(2, response.context["all_docs"].count())
        forms = response.context["forms"]
        self.assertEqual([doc1.id], [f.instance.document.id for f in forms.values()]) 

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
        
    def test_revise_no_attached_document_get(self):
        """
        Tests the "revisions/" page and checks that if the part has no
        attached documents, it is not necessary to confirm the form.
        """
        response = self.get(self.base_url + "revisions/")
        # checks that is not necessary to confirm the revision 
        self.assertFalse(response.context["confirmation"])

    def test_revise_no_attached_document_post(self):
        """
        Tests a post request to revise a part which has no attached documents.
        """
        response = self.post(self.base_url + "revisions/",
                {"revision" : "b"})
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0]
        self.assertEqual("b", rev.revision)

    def test_revise_one_attached_document_get(self):
        """
        Tests a get request to revise a part which has one attached document.
        This document must be suggested when the user revises the part.
        """
        document = DocumentController.create("RefDocument", "Document", "a", self.user, self.DATA)
        self.controller.attach_to_document(document)
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertTrue(response.context["confirmation"])
        formset = response.context["doc_formset"]
        self.assertEqual(1, formset.total_form_count())
        form = formset.forms[0]
        self.assertTrue(form.fields["selected"].initial)
        self.assertEqual(document.id, form.initial["document"].id)

    def test_revise_one_attached_document_post_selected(self):
        """
        Tests a post request to revise a part with one attached document which
        is selected.
        """
        document = DocumentController.create("RefDocument", "Document", "a", self.user, self.DATA)
        self.controller.attach_to_document(document)
        data = { "revision" : "b",
                 "parents-TOTAL_FORMS" : "0",
                 "parents-INITIAL_FORMS" : "0",
                 "children-TOTAL_FORMS" : "0",
                 "children-INITIAL_FORMS" : "0",
                 "documents-TOTAL_FORMS" : "1",
                 "documents-INITIAL_FORMS" : "1",
                 "documents-0-selected" : "on",
                 "documents-0-document" : document.id,
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].part
        self.assertEqual("b", rev.revision)
        # ensure document is still attached to the old revision
        documents = self.controller.get_attached_documents().values_list("document", flat=True)
        self.assertEqual([document.id], list(documents))
        # ensure document is attached to the new revision
        documents = rev.documentpartlink_part.values_list("document", flat=True)
        self.assertEqual([document.id], list(documents))
        # ensure both documents are attached to the document
        self.assertEqual([self.controller.id, rev.id],
            sorted(document.get_attached_parts().values_list("part", flat=True)))

    def test_revise_one_attached_document_post_unselected(self):
        """
        Tests a post request to revise a part with one attached document which
        is not selected.
        """
        document = DocumentController.create("RefDocument", "Document", "a", self.user, self.DATA)
        self.controller.attach_to_document(document)
        data = { "revision" : "b",
                 "parents-TOTAL_FORMS" : "0",
                 "parents-INITIAL_FORMS" : "0",
                 "children-TOTAL_FORMS" : "0",
                 "children-INITIAL_FORMS" : "0",
                 "documents-TOTAL_FORMS" : "1",
                 "documents-INITIAL_FORMS" : "1",
                 "documents-0-selected" : "",
                 "documents-0-document" : document.id,
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].part
        self.assertEqual("b", rev.revision)
        # ensure document is still attached to the old revision
        documents = self.controller.get_attached_documents().values_list("document", flat=True)
        self.assertEqual([document.id], list(documents))
        # ensure document is not attached to the new revision
        self.assertFalse(bool(rev.documentpartlink_part.all()))
        # ensure only the old revision is attached to document 
        self.assertEqual([self.controller.id],
            list(document.get_attached_parts().values_list("part", flat=True)))

    def test_revise_two_attached_documents_get(self):
        """
        Tests a get request to revise a part with two attached documents.
        One document is a draft, the other is official.
        """
        d1 = DocumentController.create("RefDocument", "Document", "a", self.user, self.DATA)
        self.controller.attach_to_document(d1)
        d2 = DocumentController.create("document_2", "Document", "a", self.user, self.DATA)
        self.controller.attach_to_document(d2)
        d2.object.is_promotable = lambda: True
        d2.promote()
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertTrue(response.context["confirmation"])
        formset = response.context["doc_formset"]
        self.assertEqual(2, formset.total_form_count())
        form1, form2 = formset.forms
        self.assertTrue(form1.fields["selected"].initial)
        self.assertTrue(form2.fields["selected"].initial)
        self.assertEqual([d1.id, d2.id],
                sorted([form1.initial["document"].id, form2.initial["document"].id]))

    def test_revise_two_attached_documents_post(self):
        """
        Tests a post request to revise a part with two attached documents.
        One document is a draft and not selected, the other is official and selected.
        """
        d1 = DocumentController.create("RefDocument", "Document", "a", self.user, self.DATA)
        self.controller.attach_to_document(d1)
        d2 = DocumentController.create("document_2", "Document", "a", self.user, self.DATA)
        self.controller.attach_to_document(d2)
        d2.object.is_promotable = lambda: True
        d2.promote()
        data = {
            "revision" : "b",
             "parents-TOTAL_FORMS" : "0",
             "parents-INITIAL_FORMS" : "0",
             "children-TOTAL_FORMS" : "0",
             "children-INITIAL_FORMS" : "0",
             "documents-TOTAL_FORMS" : "2",
             "documents-INITIAL_FORMS" : "2",
             "documents-0-selected" : "",
             "documents-0-document" : d1.id,
             "documents-1-selected" : "on",
             "documents-1-document" : d2.id,
             }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].part
        self.assertEqual("b", rev.revision)
        # ensure d1 and d2 are still attached to the old revision
        documents = self.controller.get_attached_documents().values_list("document", flat=True)
        self.assertEqual([d1.id, d2.id], sorted(documents))
        # ensure d2 is attached to the new revision
        documents = rev.documentpartlink_part.values_list("document", flat=True)
        self.assertEqual([d2.id], list(documents))
        # ensure both documents are attached to d2
        self.assertEqual([self.controller.id, rev.id],
            sorted(d2.get_attached_parts().values_list("part", flat=True)))

    def test_revise_one_deprecated_document_attached_get(self):
        """
        Tests a get request to revise a part which has one deprecated 
        attached document.
        This document must not be suggested when the user revises the part.
        """
        document = DocumentController.create("RefDocument", "Document", "a", self.user, self.DATA)
        self.controller.attach_to_document(document)
        document.object.state = document.lifecycle.last_state
        document.object.save()
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertFalse(response.context["confirmation"])

    def test_revise_one_deprecated_document_attached_post(self):
        """
        Tests a post request to revise a part which has one deprecated 
        attached document.
        This document must not be suggested when the user revises the part.
        """
        document = DocumentController.create("RefDocument", "Document", "a", self.user, self.DATA)
        self.controller.attach_to_document(document)
        document.object.state = document.lifecycle.last_state
        document.object.save()
        data = { "revision" : "b",
                 "parents-TOTAL_FORMS" : "0",
                 "parents-INITIAL_FORMS" : "0",
                 "children-TOTAL_FORMS" : "0",
                 "children-INITIAL_FORMS" : "0",
                 "documents-TOTAL_FORMS" : "1",
                 "documents-INITIAL_FORMS" : "1",
                 "documents-0-selected" : "",
                 "documents-0-document" : document.id,
                 }
        response = self.post(self.base_url + "revisions/", data)
        # even if we submit a formset, it should not be parsed
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].part
        # ensure document is still attached to the old revision
        documents = self.controller.get_attached_documents().values_list("document", flat=True)
        self.assertEqual([document.id], list(documents))
        # ensure document is not attached to the new revision
        self.assertFalse(bool(rev.documentpartlink_part.all()))
        # ensure only the old revision is attached to document 
        self.assertEqual([self.controller.id],
            list(document.get_attached_parts().values_list("part", flat=True)))

    def test_revise_one_attached_revised_document_get(self):
        """
        Tests a get request to revise a part which has one attached document.
        The document has been revised and so its revision must be suggested and
        the document must not be suggested when the user revises the oart.
        """
        document = DocumentController.create("RefDocument", "Document", "a", self.user, self.DATA)
        self.controller.attach_to_document(document)
        d2 = document.revise("b")
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertTrue(response.context["confirmation"])
        formset = response.context["doc_formset"]
        self.assertEqual(2, formset.total_form_count())

    def test_revise_one_attached_revised_document_post(self):
        """
        Tests a post request to revise a part which has one attached document.
        The document has been revised and its revision is selected.
        """
        document = DocumentController.create("RefDocument", "Document", "a", self.user, self.DATA)
        self.controller.attach_to_document(document)
        d2 = document.revise("b")
        data = { "revision" : "b",
                 "parents-TOTAL_FORMS" : "0",
                 "parents-INITIAL_FORMS" : "0",
                 "children-TOTAL_FORMS" : "0",
                 "children-INITIAL_FORMS" : "0",
                 "documents-TOTAL_FORMS" : "1",
                 "documents-INITIAL_FORMS" : "1",
                 "documents-0-selected" : "on",
                 "documents-0-document" : d2.id,
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].part
        self.assertEqual("b", rev.revision)
        # ensure document is still attached to the old revision
        documents = self.controller.get_attached_documents().values_list("document", flat=True)
        self.assertEqual([document.id], list(documents))
        # ensure d2 is attached to the new revision
        documents = rev.documentpartlink_part.values_list("document", flat=True)
        self.assertEqual([d2.id], list(documents))

    def test_revise_one_attached_revised_document_post_error(self):
        """
        Tests a post request to revise a part which has one attached document.
        The document has been revised and has been selected instead of its revision. 
        """
        document = DocumentController.create("RefDocument", "Document", "a", self.user, self.DATA)
        self.controller.attach_to_document(document)
        d2 = document.revise("b")
        self.controller.attach_to_document(d2)
        data = { "revision" : "b",
                 "parents-TOTAL_FORMS" : "0",
                 "parents-INITIAL_FORMS" : "0",
                 "children-TOTAL_FORMS" : "0",
                 "children-INITIAL_FORMS" : "0",
                 "documents-TOTAL_FORMS" : "1",
                 "documents-INITIAL_FORMS" : "1",
                 "documents-0-selected" : "on",
                 "documents-0-document" : document.id,
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        # no revisions have been created
        self.assertEqual([], revisions)
        # ensure documents are still attached to the old revision
        documents = self.controller.get_attached_documents().values_list("document", flat=True)
        self.assertEqual(set((document.id, d2.id)), set(documents))

    def test_revise_one_child_get(self):
        """
        Tests a get request to revise a part which has one child.
        This child must be suggested when the user revises the part.
        """
        child = PartController.create("RefChild", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child, 10, 25, "-")
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertTrue(response.context["confirmation"])
        formset = response.context["children_formset"]
        self.assertEqual(1, formset.total_form_count())
        form = formset.forms[0]
        self.assertTrue(form.fields["selected"].initial)
        self.assertEqual(child.id, form.initial["link"].child_id)

    def test_revise_one_child_post_selected(self):
        """
        Tests a post request to revise a part with one child which is selected.
        """
        child = PartController.create("RefChild", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child, 10, 25, "-")
        link = self.controller.get_children(1)[0].link
        data = { "revision" : "b",
                 "parents-TOTAL_FORMS" : "0",
                 "parents-INITIAL_FORMS" : "0",
                 "children-TOTAL_FORMS" : "1",
                 "children-INITIAL_FORMS" : "1",
                 "children-0-selected" : "on",
                 "children-0-link" : link.id,
                 "documents-TOTAL_FORMS" : "0",
                 "documents-INITIAL_FORMS" : "0",
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].part
        self.assertEqual("b", rev.revision)
        # ensure the part is still a child of the old revision
        children = self.controller.get_children(1)
        self.assertEqual([(1, link)], children)
        # ensure the part is a child of the new revision
        children = PartController(rev, self.user).get_children(1)
        self.assertEqual(1, len(children))
        link2 = children[0].link
        self.assertEqual(link2.child, link.child)
        self.assertEqual(link2.order, link.order)
        self.assertEqual(link2.quantity, link.quantity)
        self.assertEqual(link2.unit, link.unit)

    def test_revise_one_child_post_unselected(self):
        """
        Tests a post request to revise a part with child which is not selected.
        """
        child = PartController.create("RefChild", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child, 10, 25, "-")
        link = self.controller.get_children(1)[0].link
        data = { "revision" : "b",
                 "parents-TOTAL_FORMS" : "0",
                 "parents-INITIAL_FORMS" : "0",
                 "children-TOTAL_FORMS" : "1",
                 "children-INITIAL_FORMS" : "1",
                 "children-0-selected" : "",
                 "children-0-link" : link.id,
                 "documents-TOTAL_FORMS" : "0",
                 "documents-INITIAL_FORMS" : "0",
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].part
        self.assertEqual("b", rev.revision)
        # ensure the part is still a child of the old revision
        children = self.controller.get_children(1)
        self.assertEqual([(1, link)], children)
        # ensure the part is not a child of the new revision
        children = PartController(rev, self.user).get_children(1)
        self.assertEqual(0, len(children))

    def test_revise_two_childrens_get(self):
        """
        Tests a get request to revise a part with two children.
        """
        child1 = PartController.create("RefChild1", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child1, 10, 25, "-")
        child2 = PartController.create("RefChild2", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child2, 10, 55, "-")

        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertTrue(response.context["confirmation"])
        formset = response.context["children_formset"]

        self.assertEqual(2, formset.total_form_count())
        form1, form2 = formset.forms
        self.assertTrue(form1.fields["selected"].initial)
        self.assertTrue(form1.initial["link"].child_id in (child1.id, child2.id))
        self.assertTrue(form2.fields["selected"].initial)
        self.assertTrue(form2.initial["link"].child_id in (child1.id, child2.id))
        self.assertNotEqual(form2.initial["link"], form1.initial["link"])

    def test_revise_two_childrens_post(self):
        """
        Tests a post request to revise a part with two children.
        Only one child is selected.
        """
        child1 = PartController.create("RefChild1", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child1, 10, 25, "-")
        child2 = PartController.create("RefChild2", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child2, 10, 55, "-")

        link1, link2 = [c.link for c in self.controller.get_children(1)]
        data = { "revision" : "b",
                 "parents-TOTAL_FORMS" : "0",
                 "parents-INITIAL_FORMS" : "0",
                 "children-TOTAL_FORMS" : "1",
                 "children-INITIAL_FORMS" : "1",
                 "children-0-selected" : "on",
                 "children-0-link" : link1.id,
                 "children-1-selected" : "",
                 "children-1-link" : link2.id,
                 "documents-TOTAL_FORMS" : "0",
                 "documents-INITIAL_FORMS" : "0",
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].part
        self.assertEqual("b", rev.revision)
        # ensure the part is still a child of the old revision
        children = self.controller.get_children(1)
        self.assertEqual(set(((1, link1), (1, link2))), set(children))
        children = PartController(rev, self.user).get_children(1)
        self.assertEqual(1, len(children))

        link = children[0].link
        self.assertEqual(link1.child, link.child)
        self.assertEqual(link1.order, link.order)
        self.assertEqual(link1.quantity, link.quantity)
        self.assertEqual(link1.unit, link.unit)


    def test_revise_one_parent_get(self):
        """
        Tests a get request to revise a part which has one parent.
        This parent must be suggested when the user revises the part.
        """
        parent = PartController.create("RefParent", "Part", "a", self.user, self.DATA)
        parent.add_child(self.controller, 10, 25, "-")
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertTrue(response.context["confirmation"])
        formset = response.context["parents_formset"]
        self.assertEqual(1, formset.total_form_count())
        form = formset.forms[0]
        self.assertFalse(form.fields["selected"].initial)
        self.assertEqual(parent.id, form.initial["link"].parent_id)
        self.assertEqual(parent.id, form.initial["new_parent"].id)
   
    def test_revise_one_parent_post_unselected(self):
        """
        Tests a post request to revise a part which has one parent.
        This parent is not selected, and so its bom should not change.
        """
        parent = PartController.create("RefParent", "Part", "a", self.user, self.DATA)
        parent.add_child(self.controller, 10, 25, "-")
        link = parent.get_children(1)[0].link
        data = { "revision" : "b",
                 "parents-TOTAL_FORMS" : "1",
                 "parents-INITIAL_FORMS" : "1",
                 "parents-0-selected" : "",
                 "parents-0-link" : link.id,
                 "parents-0-new_parent" : parent.id,
                 "children-TOTAL_FORMS" : "0",
                 "children-INITIAL_FORMS" : "0",
                 "documents-TOTAL_FORMS" : "0",
                 "documents-INITIAL_FORMS" : "0",
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].part
        self.assertEqual("b", rev.revision)
        # ensure the old revision is still a child of the parent
        children = parent.get_children(1)
        self.assertEqual([(1, link)], children)
        self.assertFalse(PartController(rev, self.user).get_parents())

    def test_revise_one_parent_post_selected(self):
        """
        Tests a post request to revise a part which has one parent.
        This parent is selected, and so its bom must be updated.
        """
        parent = PartController.create("RefParent", "Part", "a", self.user, self.DATA)
        parent.add_child(self.controller, 10, 25, "-")
        link = parent.get_children(1)[0].link
        data = { "revision" : "b",
                 "parents-TOTAL_FORMS" : "1",
                 "parents-INITIAL_FORMS" : "1",
                 "parents-0-selected" : "on",
                 "parents-0-link" : link.id,
                 "parents-0-new_parent" : parent.id,
                 "children-TOTAL_FORMS" : "0",
                 "children-INITIAL_FORMS" : "0",
                 "documents-TOTAL_FORMS" : "0",
                 "documents-INITIAL_FORMS" : "0",
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].part
        self.assertEqual("b", rev.revision)
        # ensure the old revision is still a child of the parent
        children = parent.get_children(1)
        self.assertNotEqual([(1, link)], children)
        self.assertEqual(1, len(children))
        level, link2 = children[0]
        self.assertEqual(parent.id, link2.parent_id)
        self.assertEqual(link.order, link2.order)
        self.assertEqual(link.quantity, link2.quantity)
        self.assertEqual(link.unit, link2.unit)
        self.assertEqual(rev.id, link2.child_id)
        self.assertFalse(self.controller.get_parents())

    def test_revise_one_revised_parent_get(self):
        """
        Tests a get request to revise a part which has one parent which has been
        revised.
        """
        parent = PartController.create("RefParent", "Part", "a", self.user, self.DATA)
        parent.add_child(self.controller, 10, 25, "-")
        parent2 = parent.revise("the game")
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertTrue(response.context["confirmation"])
        formset = response.context["parents_formset"]
        self.assertEqual(1, formset.total_form_count())
        form = formset.forms[0]
        self.assertFalse(form.fields["selected"].initial)
        self.assertEqual(parent2.id, form.initial["link"].parent_id)
        self.assertEqual(parent2.id, form.initial["new_parent"].id)

    def test_revise_one_revised_parent_get2(self):
        """
        Tests a get request to revise a part which has one parent which has been
        revised before the bom was built.
        """
        parent = PartController.create("RefParent", "Part", "a", self.user, self.DATA)
        parent2 = parent.revise("the game")
        parent.add_child(self.controller, 10, 25, "-")
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertTrue(response.context["confirmation"])
        formset = response.context["parents_formset"]
        self.assertEqual(2, formset.total_form_count())
        form1, form2 = formset.forms
        self.assertFalse(form1.fields["selected"].initial)
        self.assertEqual(parent.id, form1.initial["link"].parent_id)
        self.assertEqual(parent.id, form1.initial["new_parent"].id)
        self.assertFalse(form2.fields["selected"].initial)
        self.assertEqual(parent.id, form2.initial["link"].parent_id)
        self.assertEqual(parent2.id, form2.initial["new_parent"].id)

    def test_revise_one_revised_parent_post2(self):
        """
        Tests a post request to revise a part which has one parent which has been
        revised before the bom was built.
        """
        parent = PartController.create("RefParent", "Part", "a", self.user, self.DATA)
        parent2 = parent.revise("the game")
        parent.add_child(self.controller, 10, 25, "-")
        link = parent.get_children(1)[0].link
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision 
        self.assertTrue(response.context["confirmation"])
        formset = response.context["parents_formset"]
        self.assertEqual(2, formset.total_form_count())
        data = { "revision" : "b",
                 "parents-TOTAL_FORMS" : "2",
                 "parents-INITIAL_FORMS" : "2",
                 "parents-0-selected" : "",
                 "parents-0-link" : link.id,
                 "parents-0-new_parent" : parent.id,
                 "parents-1-selected" : "on",
                 "parents-1-link" : link.id,
                 "parents-1-new_parent" : parent2.id,
                 "children-TOTAL_FORMS" : "0",
                 "children-INITIAL_FORMS" : "0",
                 "documents-TOTAL_FORMS" : "0",
                 "documents-INITIAL_FORMS" : "0",
                 }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].part
        self.assertEqual("b", rev.revision)
        # ensure the old revision is still a child of the parent
        children = parent.get_children(1)
        self.assertEqual(1, len(children))
        level, link2 = children[0]
        self.assertEqual(parent.id, link2.parent_id)
        self.assertEqual(link.order, link2.order)
        self.assertEqual(link.quantity, link2.quantity)
        self.assertEqual(link.unit, link2.unit)
        self.assertEqual(self.controller.id, link2.child_id)
        # ensure the new reviison is a child of the parent
        children = parent2.get_children(1)
        self.assertEqual(1, len(children))
        level, link2 = children[0]
        self.assertEqual(parent2.id, link2.parent_id)
        self.assertEqual(link.order, link2.order)
        self.assertEqual(link.quantity, link2.quantity)
        self.assertEqual(link.unit, link2.unit)
        self.assertEqual(rev.id, link2.child_id)

    
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

    def test_resend_sponsor_mail(self):
        user = User(username="dede", email="dede@example.net")
        self.controller.sponsor(user)
        link = m.DelegationLink.objects.get(role="sponsor", delegatee=user)
        pwd = user.password
        mail.outbox = []
        self.post(self.user_url + 'delegation/sponsor/mail/',
                {"link_id" : link.id})
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(mail.outbox[0].to, [user.email])
        user = User.objects.get(username="dede")
        self.assertNotEqual(user.password, pwd)

    def test_resend_sponsor_error_user_connected(self):
        user = User(username="dede", email="dede@example.net")
        self.controller.sponsor(user)
        user.last_login = datetime.datetime.now()
        user.save()
        link = m.DelegationLink.objects.get(role="sponsor", delegatee=user)
        pwd = user.password
        mail.outbox = []
        self.post(self.user_url + 'delegation/sponsor/mail/',
                {"link_id" : link.id}, status_code=403)
        self.assertEqual(0, len(mail.outbox))
        user = User.objects.get(username="dede")
        self.assertEqual(user.password, pwd)

    def test_resend_sponsor_error_not_sponsor(self):
        user = User(username="dede", email="dede@example.net")
        UserController(self.cie, self.cie).sponsor(user)
        link = m.DelegationLink.objects.get(role="sponsor", delegatee=user)
        pwd = user.password
        mail.outbox = []
        self.post(self.user_url + 'delegation/sponsor/mail/',
                {"link_id" : link.id}, status_code=403)
        self.assertEqual(0, len(mail.outbox))
        user = User.objects.get(username="dede")
        self.assertEqual(user.password, pwd)


class GroupViewTestCase(CommonViewTest):

    def setUp(self):
        super(GroupViewTestCase, self).setUp()
        self.part_controller = self.controller
        self.group_url = "/group/%s/" % self.group.name
        self.controller = GroupController(self.group, self.user)
        
    def test_group_attributes(self):
        response = self.get(self.group_url + "attributes/", page="attributes")
        attributes = dict((x.capitalize(), y) for (x,y) in 
                          response.context["object_attributes"])
        self.assertEqual(attributes["Description"], self.group.description)
        self.assertTrue(response.context["is_owner"])

    def test_users(self):
        response = self.get(self.group_url + "users/", page="users")
        user_formset = response.context["user_formset"]
        self.assertEqual(0, user_formset.total_form_count())
        self.assertTrue(response.context["in_group"])

    def test_users_get(self):
        self.brian.groups.add(self.group)
        response = self.get(self.group_url + "users/", page="users")
        user_formset = response.context["user_formset"]
        self.assertEqual(1, user_formset.total_form_count())
        form = user_formset.forms[0]
        self.assertFalse(form.fields["delete"].initial)
        self.assertEqual(self.brian, form.initial["user"])
        self.assertEqual(self.group, form.initial["group"])

    def test_users_post(self):
        self.brian.groups.add(self.group)
        data = {
            'form-TOTAL_FORMS' : '1',
            'form-INITIAL_FORMS' : '1',
            'form-MAX_NUM_FORMS' : 1,
            'form-0-group' : self.group.id,
            'form-0-user' : self.brian.id,
            'form-0-delete' : 'on',
            }
        response = self.post(self.group_url + "users/", data)
        self.assertEqual([], list(self.brian.groups.all()))
    
    def test_users_post_nodeletetion(self):
        self.brian.groups.add(self.group)
        data = {
            'form-TOTAL_FORMS' : '1',
            'form-INITIAL_FORMS' : '1',
            'form-MAX_NUM_FORMS' : 1,
            'form-0-group' : self.group.id,
            'form-0-user' : self.brian.id,
            'form-0-delete' : '',
            }
        response = self.post(self.group_url + "users/", data)
        self.assertTrue(self.brian.groups.filter(id=self.group.id).exists())
        user_formset = response.context["user_formset"]
        self.assertEqual(1, user_formset.total_form_count())
        form = user_formset.forms[0]
        self.assertFalse(form.fields["delete"].initial)
        self.assertEqual(self.brian, form.initial["user"])
        self.assertEqual(self.group, form.initial["group"])

    def test_plmobjects(self):
        response = self.get(self.group_url + "objects/", page="objects")
        objects = response.context["objects"]
        self.assertEqual([self.part_controller.plmobject_ptr], list(objects))
        # create a new group
        group = m.GroupInfo(name="grp2", owner=self.user, creator=self.user,
                description="grp")
        group.save()
        self.user.groups.add(group)
        # create another part which bellows to another group
        p2 = PartController.create("Part2", "Part", "a", self.user,
                dict(group=group))
        response = self.get(self.group_url + "objects/", page="objects")
        objects = response.context["objects"]
        self.assertEqual([self.part_controller.plmobject_ptr], list(objects))
        
    def test_history(self):
        response = self.get(self.group_url + "history/", page="history")
        
    def test_navigate(self):
        response = self.get(self.group_url + "navigate/")

    def test_user_add_get(self):
        """
        Tests the page to add an user to the group, get version.
        """
        response = self.get(self.group_url + "users/add/", page="users",
                link=True)
        form = response.context["add_user_form"]

    def test_user_add_post(self):
        """
        Tests the page to add an user to the group, post version.
        """
        mail.outbox = []
        data = {"type" : "User", "username" : self.brian.username}
        response = self.post(self.group_url + "users/add/", data=data)
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        self.assertFalse(inv.guest_asked)
        self.assertEqual(m.Invitation.PENDING, inv.state)
        self.assertFalse(self.brian.groups.count())
        # get the users page
        response = self.get(self.group_url + "users/")
        pending = response.context["pending_invitations"]
        self.assertEqual([inv], list(pending))
        # check a mail has been sent to brian
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(mail.outbox[0].to, [self.brian.email])
    
    def test_user_join_get(self):
        """
        Tests the page to ask to join the group, get version.
        """
        authenticated = self.client.login(username="Brian", password="life")
        self.assertTrue(authenticated)
        response = self.get(self.group_url + "users/join/", page="users")
        self.assertFalse(response.context["in_group"])

    def test_user_join_post(self):
        """
        Tests the page to ask to join the group, post version.
        """
        mail.outbox = []
        self.client.login(username="Brian", password="life")
        data = {"type" : "User", "username" : self.brian.username}
        response = self.post(self.group_url + "users/join/", data=data)
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        self.assertTrue(inv.guest_asked)
        self.assertEqual(m.Invitation.PENDING, inv.state)
        self.assertFalse(self.brian.groups.count())
        # get the users page
        response = self.get(self.group_url + "users/")
        pending = response.context["pending_invitations"]
        self.assertEqual([inv], list(pending))
        # check a mail has been sent to brian
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def _do_test_accept_invitation_get(self):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        response = self.get(self.group_url + "invitation/accept/%s/" % inv.token,
                page="users")
        self.assertEqual(inv, response.context["invitation"])
        form = response.context["invitation_form"]
        self.assertEqual(form.initial["invitation"], inv)
        # check that brian does not belong to the group
        self.assertFalse(self.brian.groups.count())
        self.assertFalse(mail.outbox)
    
    def test_accept_invitation_from_guest_get(self):
        """
        Tests the page to accept an invitation, get version.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self._do_test_accept_invitation_get()

    def _do_test_accept_invitation_post(self):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        data = {"invitation" : inv.pk }
        response = self.post(self.group_url + "invitation/accept/%s/" % inv.token,
                page="users", data=data)
        # checks that brian belongs to the group
        self.assertFalse(response.context["pending_invitations"])
        form = response.context["user_formset"].forms[0]
        self.assertEqual(self.brian, form.initial["user"])
        self.assertTrue(self.brian.groups.filter(id=self.group.id).exists())
        self.assertEqual(1, len(mail.outbox))
        # a notification is sent to the owner and to the guest
        self.assertEqual(set(mail.outbox[0].to), 
                set([self.user.email, self.brian.email]))
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        self.assertEqual(m.Invitation.ACCEPTED, inv.state)

    def test_accept_invitation_from_guest_post(self):
        """
        Tests the page to accept an invitation, post version.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self._do_test_accept_invitation_post()
    
    def test_accept_invitation_from_owner_get(self):
        """
        Tests the page to accept an invitation, get version.
        """
        self.controller.add_user(self.brian)
        self.client.login(username="Brian", password="life")
        self._do_test_accept_invitation_get()

    def test_accept_invitation_from_owner_post(self):
        """
        Tests the page to accept an invitation, post version.
        """
        self.controller.add_user(self.brian)
        self.client.login(username="Brian", password="life")
        self._do_test_accept_invitation_post()

    def _do_test_refuse_invitation_get(self):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        response = self.get(self.group_url + "invitation/refuse/%s/" % inv.token,
                page="users")
        self.assertEqual(inv, response.context["invitation"])
        form = response.context["invitation_form"]
        self.assertEqual(form.initial["invitation"], inv)
        # check that brian does not belong to the group
        self.assertFalse(self.brian.groups.count())
        self.assertFalse(mail.outbox)
    
    def test_refuse_invitation_from_guest_get(self):
        """
        Tests the page to refuse an invitation, get version.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self._do_test_refuse_invitation_get()

    def _do_test_refuse_invitation_post(self):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        data = {"invitation" : inv.pk }
        response = self.post(self.group_url + "invitation/refuse/%s/" % inv.token,
                page="users", data=data)
        # checks that brian does not belong to the group
        self.assertFalse(response.context["pending_invitations"])
        self.assertFalse(response.context["user_formset"].forms)
        self.assertFalse(self.brian.groups.filter(id=self.group.id).exists())
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        self.assertEqual(m.Invitation.REFUSED, inv.state)

    def test_refuse_invitation_from_guest_post(self):
        """
        Tests the page to refuse an invitation, post version.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self._do_test_refuse_invitation_post()
    
    def test_refuse_invitation_from_owner_get(self):
        """
        Tests the page to refuse an invitation, get version.
        """
        self.controller.add_user(self.brian)
        self.client.login(username="Brian", password="life")
        self._do_test_refuse_invitation_get()

    def test_refuse_invitation_from_owner_post(self):
        """
        Tests the page to refuse an invitation, post version.
        """
        self.controller.add_user(self.brian)
        self.client.login(username="Brian", password="life")
        self._do_test_refuse_invitation_post()

    def _do_test_send_invitation_get(self):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        response = self.get(self.group_url + "invitation/send/%s/" % inv.token,
                page="users")
        # check that brian does not belong to the group
        self.assertFalse(self.brian.groups.count())
        self.assertFalse(mail.outbox)
    
    def test_send_invitation_from_guest_get(self):
        """
        Tests the page to send an invitation, get version.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self._do_test_send_invitation_get()

    def _do_test_send_invitation_post(self, from_owner):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        data = {"invitation" : inv.pk }
        response = self.post(self.group_url + "invitation/send/%s/" % inv.token,
                page="users", data=data)
        # checks that brian does not belong to the group
        self.assertEqual([inv], list(response.context["pending_invitations"]))
        self.assertFalse(response.context["user_formset"].forms)
        self.assertFalse(self.brian.groups.filter(id=self.group.id).exists())
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        self.assertEqual(m.Invitation.PENDING, inv.state)
        # check a mail has been sent to the right user
        self.assertEqual(1, len(mail.outbox))
        email = self.brian.email if from_owner else self.user.email
        self.assertEqual(mail.outbox[0].to, [email])

    def test_send_invitation_from_guest_post(self):
        """
        Tests the page to send an invitation, post version.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self._do_test_send_invitation_post(False)
    
    def test_send_invitation_from_owner_get(self):
        """
        Tests the page to send an invitation, get version.
        """
        self.controller.add_user(self.brian)
        self.client.login(username="Brian", password="life")
        self._do_test_send_invitation_get()

    def test_send_invitation_from_owner_post(self):
        """
        Tests the page to send an invitation, post version.
        """
        self.controller.add_user(self.brian)
        self.client.login(username="Brian", password="life")
        self._do_test_send_invitation_post(True)

 
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

    def test_search_numbers_separated_by_underscores(self):
        """ Tests that 1759 matches 001759. (see ticket #69)."""

        c2 = self.CONTROLLER.create("part_001759", self.TYPE, "c", self.user, self.DATA)
        results = self.search("1759", self.TYPE)
        self.assertEqual([c2.object], results) 
        c3 = self.CONTROLLER.create("part_0001759", self.TYPE, "c", self.user, self.DATA)
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

