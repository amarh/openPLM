
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


from django.contrib.auth.models import User
from django.test import TestCase
from django.core.files.base import File
import datetime

import lxml.html

from openPLM.plmapp.utils import level_to_sign_str
import openPLM.plmapp.models as m
from openPLM.plmapp.controllers import DocumentController, PartController
from openPLM.plmapp.lifecycle import LifecycleList
from django.forms.util import from_current_timezone


from .base import CommonViewTest

class ViewTest(CommonViewTest):

    def test_home(self):
        response = self.get("/home/")

    def test_create_get(self):
        response = self.get("/object/create/", {"type" : self.TYPE})
        self.assertEqual(response.context["object_type"], self.TYPE)
        self.assertTrue(response.context["creation_form"])

    def test_create_post(self):
        data = self.DATA.copy()
        data.update({
                "type" : self.TYPE,
                "reference" : "mapart",
                "auto" : False,
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

    def test_create_redirect_get(self):
        response = self.get("/object/create/", {"type" : self.TYPE,
            "__next__" : "/home/"})
        self.assertEqual("/home/", response.context["next"])

    def test_create_redirect_post(self):
        data = self.DATA.copy()
        data.update({
                "__next__" : "/home/",
                "type" : self.TYPE,
                "reference" : "mapart",
                "auto" : False,
                "revision" : "a",
                "name" : "MaPart",
                "group" : str(self.group.id),
                "lifecycle" : m.get_default_lifecycle().pk,
                "state" : m.get_default_state().pk,
                })
        model_cls = m.get_all_plmobjects()[self.TYPE]
        page = "files" if issubclass(model_cls, m.Document) else "attributes"
        response = self.post("/object/create/", data, follow=False,
                status_code=302)
        self.assertRedirects(response, "/home/")
        obj = m.PLMObject.objects.get(type=self.TYPE, reference="mapart", revision="a")
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
                "auto" : False,
                "revision" : rev,
                "name" : "An invalid object",
                "group" : str(self.group.id),
                "lifecycle" : m.get_default_lifecycle().pk,
                "state" : m.get_default_state().pk,
                })
        model_cls = m.get_all_plmobjects()[self.TYPE]
        response = self.post("/object/create/", data)
        qset = m.PLMObject.objects.filter(type=self.TYPE,
                reference=ref, revision=rev)
        self.assertFalse(response.context["creation_form"].is_valid())
        self.assertFalse(qset.exists())

    def test_create_post_error_same_reference_and_revision(self):
        """
        Tests that the creation of an object with the same type ,
        reference and revision is forbidden when auto is not True.
        """
        data = self.DATA.copy()
        ref = self.controller.reference
        rev = self.controller.revision
        data.update({
                "type" : self.TYPE,
                "reference" : ref,
                "auto" : False,
                "revision" : rev,
                "name" : "An invalid object",
                "group" : str(self.group.id),
                "lifecycle" : m.get_default_lifecycle().pk,
                "state" : m.get_default_state().pk,
                })
        model_cls = m.get_all_plmobjects()[self.TYPE]
        response = self.post("/object/create/", data)
        qset = m.PLMObject.objects.filter(type=self.TYPE,
                reference=ref, revision=rev)
        self.assertFalse(response.context["creation_form"].is_valid())

    def test_create_post_same_reference_and_revision(self):
        """
        Tests that when auto is True and we intent to create an object with
        the same type, reference and revision:
            * a new and available reference is given to the new object
            * the object is created.
        """
        data = self.DATA.copy()
        ref = self.controller.reference
        rev = self.controller.revision
        data.update({
                "type" : self.TYPE,
                "reference" : ref,
                "auto" : True,
                "revision" : rev,
                "name" : "A valid object",
                "group" : str(self.group.id),
                "lifecycle" : m.get_default_lifecycle().pk,
                "state" : m.get_default_state().pk,
                })
        model_cls = m.get_all_plmobjects()[self.TYPE]
        response = self.post("/object/create/", data)
        obj = m.PLMObject.objects.get(type=self.TYPE,
                revision=rev, name="A valid object")
        self.assertNotEqual(ref, obj.reference)
        self.assertEqual(self.group.id, obj.group_id)
        self.assertEqual(self.user, obj.owner)
        self.assertEqual(self.user, obj.creator)

    def test_display_attributes(self):
        response = self.get(self.base_url + "attributes/", page="attributes")
        self.assertTrue(response.context["object_attributes"])
        attributes = dict((x.capitalize(), y) for (x, y, z) in
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

    def _remove_link_id(self, lifecycles):
        return tuple((x[0], x[1], [l.user.username for l in x[2]]) for x in lifecycles)

    def test_lifecycle(self):
        self.attach_to_official_document()
        response = self.get(self.base_url + "lifecycle/")
        lifecycles = self._remove_link_id(response.context["object_lifecycle"])
        wanted = (("draft", True, [self.user.username]),
                  ("official", False, [self.user.username]),
                  ("deprecated", False, []))
        self.assertFalse(response.context["cancelled_revisions"])
        self.assertFalse(response.context["deprecated_revisions"])
        self.assertEqual(lifecycles, wanted)
        # promote
        self.assertTrue(self.controller.is_promotable())
        response = self.post(self.base_url + "lifecycle/apply/",
                {"promote" : "on", "password" : "password"})
        lifecycles = self._remove_link_id(response.context["object_lifecycle"])
        wanted = (("draft", False, [self.user.username]),
                  ("official", True, [self.user.username]),
                  ("deprecated", False, []))
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
                {"demote" : "on", "password":"password"})
        lifecycles = self._remove_link_id(response.context["object_lifecycle"])
        wanted = (("draft", True, [self.user.username]),
                  ("issue1", False, [self.user.username]),
                  ("official", False, []),
                  ("deprecated", False, []))
        self.assertEqual(lifecycles, wanted)

    def test_lifecycle_warn_previous_revisions(self):
        """
        Tests that warnings about previous revisions are correctly set
        when a newer revision is revised.
        """
        doc = self.attach_to_official_document()
        revb = self.controller.revise("b")
        revc = revb.revise("c")
        if self.controller.is_part:
            revb.attach_to_document(doc)
            revc.attach_to_document(doc)
        self.controller.object.state = m.State.objects.get(name="official")
        self.controller.object.save()
        # rev ai -> no previous revisions
        response = self.get(self.base_url + "lifecycle/")
        self.assertFalse(response.context["cancelled_revisions"])
        self.assertFalse(response.context["deprecated_revisions"])

        # rev b -> a is deprecated
        response = self.get(revb.plmobject_url + "lifecycle/")
        self.assertFalse(response.context["cancelled_revisions"])
        self.assertEqual([self.controller.object.plmobject_ptr],
                response.context["deprecated_revisions"])

        # rev c -> a is deprecated, b is cancelled
        response = self.get(revc.plmobject_url + "lifecycle/")
        self.assertEqual([revb.object.plmobject_ptr],
                response.context["cancelled_revisions"])
        self.assertEqual([self.controller.object.plmobject_ptr],
                response.context["deprecated_revisions"])
        # rev c, nothing if c is official
        revc.object.state = revc.lifecycle.official_state
        revc.object.save()
        response = self.get(revc.plmobject_url + "lifecycle/")
        self.assertFalse(response.context["cancelled_revisions"])
        self.assertFalse(response.context["deprecated_revisions"])


    def test_lifecycle_bad_password(self):
        self.attach_to_official_document()
        response = self.get(self.base_url + "lifecycle/")
        lifecycles = self._remove_link_id(response.context["object_lifecycle"])
        wanted = (("draft", True, [self.user.username]),
                  ("official", False, [self.user.username]),
                  ("deprecated", False, []))
        self.assertEqual(lifecycles, wanted)
        # try to promote
        response = self.post(self.base_url + "lifecycle/apply/",
                {"promote" : "on", "password":"wrong_password"})
        lifecycles = self._remove_link_id(response.context["object_lifecycle"])
        self.assertEqual(lifecycles, wanted)
        self.assertFalse(response.context["password_form"].is_valid())

    def test_lifecycle_deprecated(self):
        """ Tests the lifecycle page of a deprecated object."""
        self.controller.promote(checked=True)
        self.controller.promote(checked=True)
        self.assertTrue(self.controller.is_deprecated)
        response = self.get(self.base_url +  "lifecycle/")
        root = lxml.html.fromstring(response.content.decode("utf-8"))
        self.assertFalse(root.xpath('//input[@name="promote"]'))
        self.assertFalse(root.xpath('//input[@name="demote"]'))

    def test_revisions_get(self):
        response = self.get(self.base_url + "revisions/")
        revisions = response.context["revisions"]
        self.assertEqual(revisions, [self.controller.plmobject_ptr])
        self.assertTrue(response.context["add_revision_form"] is not None)
        # add a new revision
        rev = self.controller.revise("jf")
        response = self.get(self.base_url + "revisions/")
        revisions = response.context["revisions"]
        self.assertEqual(revisions, [self.controller.plmobject_ptr, rev.plmobject_ptr])
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
        self.assertTrue(len(history2) > len(history))
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
        
        # Test for history's form
        #date + number days valid. User entered in done_by field does not exists
        response = self.get(self.base_url +"history/"  , {"date_history_begin":"2013-06-07","number_days":"30","done_by":"efzgfezf"})
        history5 = response.context["object_history"]
        messages = response.context['messages']
        self.assertTrue(len(history5) == 0)
        self.assertEqual(1, len(messages))
        
    def test_timeline(self):
        #Test for timeline's form

        date_begin = from_current_timezone(datetime.datetime.today() + datetime.timedelta(days = 1))
        date_end = from_current_timezone(datetime.datetime.today() - datetime.timedelta(days = 30))
        
        # document + part selected + no date specified
        response = self.get("/timeline/", {"part":"on","document":"on"})
        history = response.context["object_history"]
        self.assertEqual(list(history), list(m.History.objects.filter(date__gte = date_end, date__lt = date_begin)))
        # Only document selected + no date specified
        response = self.get("/timeline/", {"document":"on"})
        history2 = response.context["object_history"]
        self.assertEqual(list(history2), list(m.History.objects.filter(date__gte = date_end, date__lt = date_begin, plmobject__type__in = m.document.get_all_documents().keys())))
        # Only part selected + no date specified
        response = self.get("/timeline/", {"part":"on"})
        history3 = response.context["object_history"]
        self.assertEqual(list(history3), list(m.History.objects.filter(date__gte = date_end, date__lt = date_begin, plmobject__type__in = m.part.get_all_parts().keys())))
        # part + document selected and date specified / done_by not informed 
        response = self.get("/timeline/", {"part":"on", "document":"on", "date_history_begin":"2013-06-8", "number_days": "15"})
        history4 = response.context["object_history"]
        date_begin = from_current_timezone(datetime.datetime(2013,6,9))
        date_end = from_current_timezone(date_begin - datetime.timedelta(days = 15))
        self.assertEqual(list(history4), list(m.History.objects.filter(date__gte = date_end, date__lt = date_begin)))
        # part + document selected and date specified + done_by informed 
        response = self.get("/timeline/" , {"part":"on", "document":"on", "date_history_begin":"2013-06-8", "number_days": "15", "done_by": "company"})
        history5 = response.context["object_history"]
        self.assertEqual(list(history5), list(m.History.objects.filter(date__gte = date_end, date__lt = date_begin, user__username="company")))
        # only group selected
        response = self.get("/timeline/" , {"group":"on","date_history_begin":"2013-06-8", "number_days": "15", "done_by": "company"})
        history6 = response.context["object_history"]
        self.assertEqual(list(history6), list(m.GroupHistory.objects.filter(date__gte = date_end, date__lt = date_begin, user__username="company")))
        
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
        response = self.get(self.base_url + "lifecycle/", page="lifecycle")
        self.brian.groups.add(self.group)
        self.controller.set_owner(self.brian)
        response = self.get(self.base_url + "lifecycle/")
        self.assertFalse(response.context["is_notified"])
        form = response.context["notify_self_form"]
        self.assertEqual("User", form.initial["type"])
        self.assertEqual(self.user.username, form.initial["username"])

    def do_test_management_add_get(self, url, role):
        response = self.get(url, link=True, page="lifecycle")
        attach = response.context["attach"]
        self.assertEqual(self.controller.id, attach[0].id)
        self.assertEqual("add_" + role, attach[1])

    def do_test_management_add_post(self, url, role):
        data = dict(type="User", username=self.brian.username)
        self.brian.groups.add(self.group)
        response = self.post(url, data)
        self.assertTrue(m.PLMObjectUserLink.current_objects.filter(plmobject=self.controller.object,
            user=self.brian, role=role).exists())

    def test_management_add_notified_get(self):
        self.do_test_management_add_get(self.base_url + "management/add/", m.ROLE_NOTIFIED)

    def test_management_add_reader_get(self):
        self.brian.profile.restricted = True
        self.brian.profile.save()
        self.controller.promote(checked=True)
        self.do_test_management_add_get(self.base_url + "management/add-reader/", m.ROLE_READER)

    def test_management_add_signer0_get(self):
        self.do_test_management_add_get(self.base_url + "management/add-signer0/",
                level_to_sign_str(0))

    def test_management_add_signer1_get(self):
        self.do_test_management_add_get(self.base_url + "management/add-signer1/",
                level_to_sign_str(1))

    def test_management_add_reader_post(self):
        self.brian.profile.restricted = True
        self.brian.profile.save()
        self.controller.promote(checked=True)
        self.do_test_management_add_post(self.base_url + "management/add-reader/", m.ROLE_READER)

    def test_management_add_signer0_post(self):
        self.do_test_management_add_post(self.base_url + "management/add-signer0/",
                level_to_sign_str(0))

    def test_management_add_signer1_post(self):
        self.do_test_management_add_post(self.base_url + "management/add-signer1/",
                level_to_sign_str(1))

    def test_management_add_notified_post(self):
        self.do_test_management_add_post(self.base_url + "management/add/", m.ROLE_NOTIFIED)

    def do_test_management_delete_post(self, url, role):
        self.brian.groups.add(self.group)
        self.controller.set_role(self.brian, role)
        link_id = self.controller.users.get(user=self.brian, role=role).id
        response = self.post(url, {"link_id" : link_id})
        self.assertFalse(m.PLMObjectUserLink.current_objects.filter(plmobject=self.controller.object,
            user=self.brian, role=role).exists())

    def test_management_delete_reader_post(self):
        self.brian.profile.restricted = True
        self.brian.profile.save()
        self.controller.promote(checked=True)
        self.do_test_management_delete_post(self.base_url + "management/delete/", m.ROLE_READER)

    def test_management_delete_signer0_post(self):
        self.do_test_management_delete_post(self.base_url + "management/delete/",
                level_to_sign_str(0))

    def test_management_delete_signer1_post(self):
        self.do_test_management_delete_post(self.base_url + "management/delete/",
                level_to_sign_str(1))

    def test_management_delete_notified_post(self):
        self.do_test_management_delete_post(self.base_url + "management/delete/", m.ROLE_NOTIFIED)

    def test_management_replace_signer_get(self):
        role = level_to_sign_str(0)
        self.brian.groups.add(self.group)
        self.controller.replace_signer(self.user, self.brian, role)
        link = m.PLMObjectUserLink.current_objects.get(plmobject=self.controller.object,
            user=self.brian, role=role)
        response = self.get(self.base_url + "management/replace/%d/" % link.id,
                link=True, page="lifecycle")
        attach = response.context["attach"]
        self.assertEqual(self.controller.id, attach[0].id)
        self.assertEqual("add_" + role, attach[1])

    def test_management_replace_signer_post(self):
        role = level_to_sign_str(0)
        self.brian.groups.add(self.group)
        self.controller.replace_signer(self.user, self.brian, role)
        link = m.PLMObjectUserLink.current_objects.get(plmobject=self.controller.object,
            user=self.brian, role=role)
        data = dict(type="User", username=self.user.username)
        response = self.post(self.base_url + "management/replace/%d/" % link.id,
                        data)
        self.assertFalse(m.PLMObjectUserLink.current_objects.filter(plmobject=self.controller.object,
            user=self.brian, role=role))
        self.assertTrue(m.PLMObjectUserLink.current_objects.filter(plmobject=self.controller.object,
            user=self.user, role=role))

    def test_publish_post(self):
        """ Tests a publication. """
        self.controller.object.state = m.State.objects.get(name="official")
        self.controller.object.save()
        self.user.profile.can_publish = True
        self.user.profile.save()
        response = self.post(self.base_url + "lifecycle/apply/",
                {"publish" : "on", "password" : "password"})
        self.assertTrue(response.context["obj"].published)
        # check that the public link is displayed
        root = lxml.html.fromstring(response.content.decode("utf-8"))
        self.assertTrue(root.xpath('//input[@name="unpublish"]'))
        self.assertFalse(root.xpath('//input[@name="publish"]'))
        self.assertTrue(root.xpath(u'//a[@href=$url]', url=self.base_url+"public/"))

    def test_publish_post_error_not_official(self):
        """ Tests a publication: error: object not official. """
        self.user.profile.can_publish = True
        self.user.profile.save()
        response = self.client.post(self.base_url + "lifecycle/apply/",
                data={"publish" : "on", "password" : "password"})
        self.assertTemplateUsed(response, "error.html")
        response2 = self.get(self.base_url + "lifecycle/apply/")
        self.assertFalse(response2.context["obj"].published)
        # check that the public link is not displayed
        root = lxml.html.fromstring(response2.content.decode("utf-8"))
        self.assertFalse(root.xpath('//input[@name="unpublish"]'))
        self.assertFalse(root.xpath('//input[@name="publish"]'))
        self.assertFalse(root.xpath(u'//a[@href=$url]', url=self.base_url+"public/"))

    def test_publish_post_error_published(self):
        """ Tests a publication: error: object is already published. """
        self.user.profile.can_publish = True
        self.user.profile.save()
        self.controller.object.state = m.State.objects.get(name="official")
        self.controller.object.published = True
        self.controller.object.save()
        response = self.client.post(self.base_url + "lifecycle/apply/",
                data={"publish" : "on", "password" : "password"})
        self.assertTemplateUsed(response, "error.html")
        response2 = self.get(self.base_url + "lifecycle/apply/")
        self.assertTrue(response2.context["obj"].published)
        # check that the publish button is not displayed
        root = lxml.html.fromstring(response2.content.decode("utf-8"))
        self.assertTrue(root.xpath('//input[@name="unpublish"]'))
        self.assertFalse(root.xpath('//input[@name="publish"]'))
        self.assertTrue(root.xpath(u'//a[@href=$url]', url=self.base_url+"public/"))

    def test_unpublish_post(self):
        """ Tests an unpublication. """
        self.controller.object.published = True
        self.controller.object.state = m.State.objects.get(name="official")
        self.controller.object.save()
        self.user.profile.can_publish = True
        self.user.profile.save()
        response = self.post(self.base_url + "lifecycle/apply/",
                {"unpublish" : "on", "password" : "password"})
        self.assertFalse(response.context["obj"].published)
        # check that the public link is not displayed
        root = lxml.html.fromstring(response.content.decode("utf-8"))
        self.assertFalse(root.xpath('//input[@name="unpublish"]'))
        self.assertTrue(root.xpath('//input[@name="publish"]'))
        self.assertFalse(root.xpath(u'//a[@href=$url]', url=self.base_url+"public/"))

    def test_unpublish_post_error_unpublished(self):
        """ Tests an unpublication: errror: object is unpublished. """
        self.controller.object.save()
        self.user.profile.can_publish = True
        self.user.profile.save()
        response = self.client.post(self.base_url + "lifecycle/apply/",
                {"unpublish" : "on", "password" : "password"})
        self.assertTemplateUsed(response, "error.html")
        response2 = self.get(self.base_url + "lifecycle/apply/")
        self.assertFalse(response2.context["obj"].published)
        # check that the unpublish button is not displayed
        root = lxml.html.fromstring(response.content.decode("utf-8"))
        self.assertFalse(root.xpath('//input[@name="unpublish"]'))
        self.assertFalse(root.xpath('//input[@name="publish"]'))
        self.assertFalse(root.xpath(u'//a[@href=$url]', url=self.base_url+"public/"))

    def test_public_get(self):
        """ Tests anonymous access to a published object. """
        self.controller.object.published = True
        self.controller.object.save()
        revb = self.controller.revise("b")
        self.assertFalse(revb.published)
        revc = revb.revise("c")
        revc.object.published = True
        revc.object.save()
        self.client.logout()
        response = self.client.get(self.base_url + "public/")
        self.assertTrue(response.context["obj"].published)
        # checks that some private data are not displayed
        root = lxml.html.fromstring(response.content.decode("utf-8"))
        self.assertNotContains(response, self.user.username)
        self.assertEqual(["a", "c"], [o.revision for o in response.context["revisions"]])
        self.assertFalse(root.xpath('//div[@id="SearchBox"]'))
        self.assertFalse(root.xpath('//div[@id="DisplayBox"]'))

    def test_public_error(self):
        """ Tests anonymous access to an unpublished object: error. """
        self.client.logout()
        response = self.client.get(self.base_url + "public/", follow=True)
        self.assertTemplateUsed(response, "login.html")



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
        response = self.get("/search/" ,
                {"type" : t, "q" : query})
        results = list(response.context["results"])
        results.sort(key=lambda r:r.object.pk)
        return [r.object for r in results]

    def test_forms(self):
        response = self.get("/user/%s/attributes/" % self.user.username)
        # check that searchform is present
        af = response.context["search_form"]

    def test_session_forms(self):
        "Tests if form field are kept between two search"
        data =  {"type" : "Part", "revision" : "c", "name" : "a name"}
        self.search(data)
        query = self.get_query(data)
        for x in range(4):
            response = self.get("/user/%s/attributes/" % self.user.username)
            af = response.context["search_form"]
            self.assertEqual(af.data["q"], query)

    def test_empty(self):
        "Test a search with an empty database"
        # clear all plmobject so results is empty
        m.PLMObject.objects.all().delete()
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

    def test_search_cancelled(self):
        c2 = self.CONTROLLER.create("part_001759", self.TYPE, "c", self.user, self.DATA)
        c2.safe_cancel()
        results = self.search("1759", self.TYPE)
        self.assertFalse(results)
        results = self.search("cancelled", self.TYPE)
        self.assertEquals([c2.object], results)
        results = self.search("", self.TYPE)
        self.assertEquals([self.controller.object], results)

    def test_search_not(self):
        self.controller.name = "abcdef"
        self.controller.save()
        results = self.search("NOT %s" % self.controller.name, self.TYPE)
        self.assertEqual([], results)
        results = self.search("NOT nothing", self.TYPE)
        self.assertEqual([self.controller.object], results)

    def test_search_invalid_type(self):
        results = self.search("NOT nothing", "InvalidType")
        self.assertEqual([], results)

    def test_search_in_file(self):
        doc = DocumentController.create("doccc", "Document", "d",
                self.user, self.DATA)
        df = doc.add_file(self.get_file(name="pppp.txt", data="monocle monocle"))
        results = self.search("monocle", "Document")
        self.assertEqual([df], results)
        results = self.search("monocl*", "Document")
        self.assertEqual([df], results)
        results = self.search("file:monocl*", "Document")
        self.assertEqual([df], results)
        results = self.search("dfdf", "Document")
        self.assertEqual([], results)
        results = self.search("pppp.txt", "Document")
        self.assertEqual([df], results)
        # ensure a delete file is not matched
        doc.delete_file(df)
        results = self.search("monocle", "Document")
        self.assertEqual([], results)

    def test_search_deprecated_file(self):
        doc = DocumentController.create("doccc", "Document", "d",
                self.user, self.DATA)
        df = doc.add_file(self.get_file(name="pppp.txt", data="monocle monocle"))
        results = self.search("monocle", "Document")
        df.deprecated = True
        df.save()
        results = self.search("monocle", "Document")
        self.assertEqual([], results)

    def test_search_in_odt(self):
        doc = DocumentController.create("doccc", "Document", "d",
                self.user, self.DATA)
        df = doc.add_file(File(open("datatests/office_a4_3p.odt", "rb")))
        results = self.search("find me", "Document")
        self.assertEqual([df], results)



class MechantUserViewTest(TestCase):
    """
    Tests when a user try an unauthorized action
    """

    TYPE = "Part"
    CONTROLLER = PartController
    DATA = {}

    def setUp(self):
        owner = User(username="owner")
        owner.set_password("password")
        owner.save()
        owner.profile.is_contributor = True
        owner.profile.save()
        self.user = User(username="user")
        self.user.set_password("password")
        self.user.save()
        self.user.profile.is_contributor = True
        self.user.profile.save()
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
        self.assertTemplateUsed(response, "error.html")


