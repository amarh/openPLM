from django.contrib.auth.models import User
from json import JSONDecoder
from django.core.files.base import ContentFile

import openPLM.plmapp.exceptions as exc
from openPLM.plmapp import models
from openPLM.plmapp.controllers import (PartController, DocumentController,
        GroupController, UserController)
from openPLM.plmapp.tests.base import BaseTestCase


class RestrictedTestCase(BaseTestCase):

    def setUp(self):
        super(RestrictedTestCase, self).setUp()
        self.restricted_user = User(username="ru", email="ru@example.net")
        self.restricted_user.set_password("ru")
        self.restricted_user.save()
        self.restricted_user.profile.restricted = True
        self.restricted_user.profile.save()


class RestrictedPLMObjectControllerTestCase(RestrictedTestCase):

    def setUp(self):
        super(RestrictedPLMObjectControllerTestCase, self).setUp()
        self.ctrl = self.create()
        self.rctrl = self.CONTROLLER(self.ctrl.object, self.restricted_user)

    def test_set_owner_error(self):
        self.assertRaises(exc.PermissionError, self.ctrl.set_owner, self.restricted_user)

    def test_check_readable_error(self):
        self.assertRaises(exc.PermissionError, self.rctrl.check_readable)

    def test_check_restricted_readable_error(self):
        self.assertRaises(exc.PermissionError, self.rctrl.check_restricted_readable)
        self.assertFalse(self.rctrl.check_restricted_readable(False))

    def test_check_restricted_readable_ok(self):
        models.PLMObjectUserLink.objects.create(user=self.restricted_user,
                plmobject=self.rctrl.object, role=models.ROLE_READER)
        self.assertTrue(self.rctrl.check_restricted_readable())

    def test_add_notified_error(self):
        self.assertRaises(exc.PermissionError, self.ctrl.add_notified,
                self.restricted_user)
        self.assertRaises(exc.PermissionError, self.rctrl.add_notified,
                self.restricted_user)

    def test_add_remove_reader(self):
        self.ctrl.object.state = self.ctrl.lifecycle.official_state
        self.ctrl.object.save()
        self.ctrl.add_reader(self.restricted_user)
        self.assertTrue(self.rctrl.check_restricted_readable())
        self.assertTrue(self.restricted_user.plmobjectuserlink_user.now().filter(role=models.ROLE_READER,
            plmobject=self.ctrl.object).exists())
        self.ctrl.remove_reader(self.restricted_user)
        self.rctrl.clear_permissions_cache()
        self.assertFalse(self.rctrl.check_restricted_readable(raise_=False))
        self.assertFalse(self.restricted_user.plmobjectuserlink_user.now().filter(role=models.ROLE_READER,
            plmobject=self.ctrl.object).exists())

    def test_add_reader_error_not_official(self):
        self.assertRaises(ValueError, self.ctrl.add_reader, self.restricted_user)

    def test_add_reader_error_not_restricted(self):
        self.assertRaises(ValueError, self.ctrl.add_reader, self.user)
        self.assertRaises(ValueError, self.ctrl.add_reader, self.cie)

    def test_add_reader_not_in_group(self):
        self.ctrl.object.state = self.ctrl.lifecycle.official_state
        self.ctrl.object.save()
        self.user.groups.remove(self.group)
        self.assertRaises(exc.PermissionError, self.ctrl.add_reader, self.restricted_user)

    def test_add_reader_error_restricted_user(self):
        self.ctrl.object.state = self.ctrl.lifecycle.official_state
        self.ctrl.object.save()
        self.assertRaises(exc.PermissionError, self.rctrl.add_reader, self.restricted_user)

        # a reader who tries to add another reader
        self.ctrl.add_reader(self.restricted_user)
        ruser = User(username="ru2", email="ru2@example.net")
        ruser.set_password("ru")
        ruser.save()
        ruser.profile.restricted = True
        ruser.profile.save()
        self.assertRaises(exc.PermissionError, self.rctrl.add_reader, ruser)

    def test_set_role_reader(self):
        self.ctrl.object.state = self.ctrl.lifecycle.official_state
        self.ctrl.object.save()
        self.ctrl.set_role(self.restricted_user, models.ROLE_READER)
        self.assertTrue(self.rctrl.check_restricted_readable())

    def test_cancel_error(self):
        self.assertRaises(exc.PermissionError, self.rctrl.safe_cancel)

    def test_clone_error(self):
        self.assertRaises(exc.PermissionError, self.rctrl.check_clone)

class RestrictedGroupControllerTestCase(RestrictedTestCase):


    def setUp(self):
        super(RestrictedGroupControllerTestCase, self).setUp()
        self.ctrl = GroupController(self.group, self.user)
        self.rctrl = GroupController(self.group, self.restricted_user)

    def test_check_readable_error(self):
        self.assertRaises(exc.PermissionError, self.rctrl.check_readable)

    def test_create_error(self):
        self.assertRaises(exc.PermissionError, GroupController.create,
                "new_group", "description", self.restricted_user)

    def test_add_user_error(self):
        self.assertRaises(ValueError, self.ctrl.add_user, self.restricted_user)
        self.assertRaises(exc.PermissionError, self.rctrl.add_user, self.restricted_user)

    def test_ask_to_join_error(self):
        self.assertRaises(ValueError, self.rctrl.ask_to_join)

class RestrictedUserControllerTestCase(RestrictedTestCase):


    def setUp(self):
        super(RestrictedUserControllerTestCase, self).setUp()
        self.ctrl = UserController(self.user, self.user)
        self.rctrl = UserController(self.user, self.restricted_user)

    def test_check_readable_error(self):
        self.assertRaises(exc.PermissionError, self.rctrl.check_readable)

    def test_delegate_error(self):
        for role in models.ROLES:
            self.assertRaises(exc.PermissionError, self.ctrl.delegate,
                    self.restricted_user, role)
            self.assertRaises(exc.PermissionError, self.rctrl.delegate,
                    self.restricted_user, role)
            self.assertRaises(exc.PermissionError, self.rctrl.delegate,
                    self.user, role)

class RestrictedApiTestCase(RestrictedTestCase):

    def setUp(self):
        super(RestrictedApiTestCase, self).setUp()
        self.ctrl = self.create()
        self.client.post("/login/", {'username' : 'ru', 'password' : 'ru'})

    def assertApiErrorGet(self, url, **get):
        response = self.client.get(url, get, follow=True, HTTP_USER_AGENT="openplm")
        data = JSONDecoder().decode(response.content)
        self.assertEquals("error", data["result"])
        self.assertEquals("user must be login", data["error"])
        self.assertTrue("api_version" in data)
        self.assertEquals(3, len(data))

    def assertApiErrorPost(self, url, **post):
        response = self.client.post(url, post, follow=True, HTTP_USER_AGENT="openplm")
        data = JSONDecoder().decode(response.content)
        self.assertEquals("error", data["result"])
        self.assertEquals("user must be login", data["error"])
        self.assertTrue("api_version" in data)
        self.assertEquals(3, len(data))

    def test_login(self):
        self.client.logout()
        response = self.client.post("/api/login/", dict(username="ru", password="ru"),
                HTTP_USER_AGENT="openplm")
        data = JSONDecoder().decode(response.content)
        self.assertEquals("error", data["result"])
        self.assertEquals("user is inactive", data["error"])
        self.assertTrue("api_version" in data)
        self.assertEquals(3, len(data))

    def test_get_all_types(self):
        self.assertApiErrorGet("/api/types/")

    def test_get_all_docs(self):
        self.assertApiErrorGet("/api/docs/")

    def test_get_all_parts(self):
        self.assertApiErrorGet("/api/parts/")

    def test_search(self):
        self.assertApiErrorGet("/api/search/", type="Part", q="*")

    def test_get_search_fields(self):
        self.assertApiErrorGet("/api/search_fields/Part/")

    def test_get_creation_fields(self):
        self.assertApiErrorGet("/api/creation_fields/Part/")

    def test_next_revision(self):
        self.assertApiErrorGet("/api/object/%d/next_revision/" % self.ctrl.id)

    def test_get_files(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        df = doc.add_file(self.get_file())
        self.assertApiErrorGet("/api/object/%d/files/" % doc.id)


    def test_create(self):
        self.assertApiErrorPost("/api/create/", type="Document", name="docu",
                reference="DocRef", revision="0", group=self.group.id,
                lifecycle="draft_official_deprecated")
        self.assertEquals(0, models.Document.objects.count())

    def test_revise(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        self.assertApiErrorPost("/api/object/%d/revise/" % doc.id, revision="b")
        self.assertEquals(1, models.Document.objects.count())

    def test_add_file(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        mock_file = self.get_file()
        self.assertApiErrorPost("/api/object/%d/add_file/" % doc.id,
                filename=mock_file)
        self.assertFalse(doc.files)

    def test_attach_to_part(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        self.assertApiErrorGet("/api/object/%d/attach_to_part/%d/" %
                (doc.id, self.ctrl.id))
        self.assertFalse(doc.get_attached_parts())

    def test_is_locked(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        df = doc.add_file(self.get_file())
        self.assertApiErrorGet("/api/object/%d/is_locked/%d/" % (doc.id, df.id))

    def test_unlock(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        df = doc.add_file(self.get_file())
        doc.lock(df)
        self.assertApiErrorGet("/api/object/%d/unlock/%d/" % (doc.id, df.id))
        self.assertTrue(doc.files[0].locked)

    def test_checkin(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        df = doc.add_file(self.get_file(data="t"))
        mock_file = self.get_file(data="robert")
        self.assertApiErrorPost("/api/object/%d/checkin/%d/" % (doc.id, df.id),
                filename=mock_file)
        self.assertEqual("t", doc.files[0].file.read())

    def test_add_thumbnail(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        df = doc.add_file(self.get_file(), thumbnail=False)
        thumbnail = ContentFile(file("datatests/thumbnail.png").read())
        thumbnail.name = "Thumbnail.png"
        self.assertApiErrorPost("/api/object/%d/add_thumbnail/%d/" % (doc.id, df.id),
                filename=thumbnail)
        self.assertFalse(doc.files[0].thumbnail.name)


class RestrictedAjaxTestCase(RestrictedTestCase):

    CONTROLLER = PartController

    def setUp(self):
        super(RestrictedAjaxTestCase, self).setUp()
        self.ctrl = self.create()
        self.client.post("/login/", {'username' : 'ru', 'password' : 'ru'})

    def assertAjaxErrorGet(self, url, **get):
        response = self.client.get(url, get, follow=True)
        self.assertTemplateUsed(response, "login.html")

    def assertAjaxErrorPost(self, url, **post):
        response = self.client.post(url, post, follow=True)
        self.assertTemplateUsed(response, "login.html")

    def test_creation_form(self):
        for t in ("Part", "Document", "Group"):
            self.assertAjaxErrorGet("/ajax/create/", type=t)

    def test_auto_complete_part(self):
        self.create("Other")
        self.assertAjaxErrorGet("/ajax/complete/Part/reference/", term="Pa")

    def test_navigate(self):
        self.assertAjaxErrorGet("/ajax/navigate/Part/Part1/a/")

    def test_can_add_child_ok(self):
        p2 = self.create("part2")
        self.assertAjaxErrorGet("/ajax/can_add_child/%d/" % self.ctrl.id,
                type=p2.type, reference=p2.reference, revision=p2.revision)

    def test_add_child_get(self):
        p2 = self.create("part2")
        self.assertAjaxErrorGet("/ajax/add_child/%d/" % self.ctrl.id,
                type=p2.type, reference=p2.reference, revision=p2.revision)

    def test_add_child_post(self):
        p2 = self.create("part2")
        self.assertAjaxErrorPost("/ajax/add_child/%d/" % self.ctrl.id,
                type=p2.type, reference=p2.reference, revision=p2.revision,
                quantity="10", order="10", unit="g")
        self.assertFalse(self.ctrl.get_children())

    def test_can_attach_part_doc(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        self.assertAjaxErrorGet("/ajax/can_attach/%d/" % self.ctrl.id,
                type=doc.type, reference=doc.reference, revision=doc.revision)

    def test_can_attach_doc_part(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        self.assertAjaxErrorGet("/ajax/can_attach/%d/" % doc.id,
                type=self.ctrl.type, reference=self.ctrl.reference,
                revision=self.ctrl.revision)

    def test_can_attach_part_part(self):
        p2 = self.create("part2")
        self.assertAjaxErrorPost("/ajax/can_attach/%d/" % self.ctrl.id,
                type=p2.type, reference=p2.reference, revision=p2.revision)

    def test_can_attach_doc_doc(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        self.assertAjaxErrorPost("/ajax/can_attach/%d/" % doc.id,
                type=doc.type, reference=doc.reference, revision=doc.revision)

    def test_attach_get(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        self.assertAjaxErrorGet("/ajax/attach/%d/" % self.ctrl.id,
                type=doc.type, reference=doc.reference, revision=doc.revision)

    def test_attach_part_doc_post(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        self.assertAjaxErrorPost("/ajax/attach/%d/" % self.ctrl.id,
                type=doc.type, reference=doc.reference, revision=doc.revision)
        self.assertFalse(self.ctrl.get_attached_documents())

    def test_attach_doc_part_post(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        self.assertAjaxErrorPost("/ajax/attach/%d/" % doc.id,
                type=self.ctrl.type, reference=self.ctrl.reference,
                revision=self.ctrl.revision)
        self.assertFalse(self.ctrl.get_attached_documents())

    def test_thumbnails(self):
        # create a document with a file
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        thumbnail = ContentFile(file("datatests/thumbnail.png").read())
        thumbnail.name = "Thumbnail.png"
        doc.add_file(self.get_file())
        f2 = doc.files.all()[0]
        doc.add_thumbnail(f2, thumbnail)

        self.assertAjaxErrorGet("/ajax/thumbnails/%s/%s/%s/" % (doc.type, doc.reference,
            doc.revision))


class RestrictedViewTestCase(RestrictedTestCase):

    CONTROLLER = PartController

    def setUp(self):
        super(RestrictedViewTestCase, self).setUp()
        self.ctrl = self.create()
        self.ctrl.object.state = self.ctrl.object.lifecycle.official_state
        self.ctrl.object.save()
        self.ctrl.add_reader(self.restricted_user)
        self.client.post("/login/", {'username' : 'ru', 'password' : 'ru'})

    def assertViewErrorGet(self, url, **get):
        response = self.client.get(url, get, follow=True)
        self.assertEqual(403, response.status_code)

    def assertViewErrorPost(self, url, **post):
        response = self.client.post(url, post, follow=True)
        self.assertEqual(403, response.status_code)

    def assert404(self, url, **get):
        response = self.client.get(url, get, follow=True)
        self.assertEqual(404, response.status_code)


    # forbidden responses

    def test_create_get(self):
        self.assertViewErrorGet("/object/create/", type="Part")

    def test_create_post(self):
        self.assertEqual(1, models.Part.objects.count())
        self.assertViewErrorPost("/object/create/", type="Part",
                reference="reff", revision="rev", name="e",
                lifecycle=models.get_default_lifecycle().pk, group=self.group.id)
        self.assertEqual(1, models.Part.objects.count())

    def test_import_csv_get(self):
        self.assertViewErrorGet("/import/csv/")

    def test_part_attributes_get(self):
        self.assert404(self.ctrl.plmobject_url + "attributes/")

    def test_part_attributes_not_reader_get(self):
        self.ctrl.remove_reader(self.restricted_user)
        self.assert404(self.ctrl.plmobject_url + "attributes/")

    def test_other_user_attributes_get(self):
        self.assert404("/user/%s/attributes/" % self.user.username)

    def test_group_attributes_get(self):
        self.assert404("/group/%s/attributes/" % self.group.name)

    def test_other_user_history_get(self):
        self.assertViewErrorGet("/user/%s/history/" % self.user.username)

    def test_self_history_get(self):
        self.assertViewErrorGet("/user/%s/history/" % self.restricted_user.username)

    def test_navigate(self):
        self.assertViewErrorGet("/user/%s/navigate/" % self.restricted_user.username)
        self.assertViewErrorGet("/user/%s/navigate/" % self.user.username)
        self.assertViewErrorGet("/group/%s/navigate/" % self.group.name)
        self.assertViewErrorGet(self.ctrl.plmobject_url + "navigate/")

    def test_lifecycle_get(self):
        self.assertViewErrorGet(self.ctrl.plmobject_url + "lifecycle/")

    def test_promote_post(self):
        state = self.ctrl.state
        self.assertViewErrorPost(self.ctrl.plmobject_url + "lifecycle/apply",
                promote="on", password="ru")
        self.assertEqual(state, models.PLMObject.objects.get(id=self.ctrl.id).state)

    def test_revise_get(self):
        self.assertViewErrorGet(self.ctrl.plmobject_url + "revisions/")

    def test_revise_post(self):
        self.assertViewErrorPost(self.ctrl.plmobject_url + "revisions/", revision="b")
        self.assertEquals(1, models.PLMObject.objects.count())
        self.assertFalse(self.ctrl.get_next_revisions())

    def test_bom(self):
        # get
        self.assertViewErrorGet(self.ctrl.plmobject_url + "BOM-child/")
        self.assertViewErrorGet(self.ctrl.plmobject_url + "BOM-child/add/")
        p2 = self.create("P2")
        # post
        response = self.assertViewErrorPost(self.ctrl.plmobject_url + "BOM-child/add/",
                **{"type": "Part", "reference":"P2", "revision":"a",
                    "quantity" : 10, "order" : 10, "unit" : "m"})
        self.assertEquals(0, models.ParentChildLink.objects.count())

    def test_parents(self):
        self.assertViewErrorGet(self.ctrl.plmobject_url + "parents/")

    def test_doc_cad(self):
        # get
        self.assertViewErrorGet(self.ctrl.plmobject_url + "doc-cad/")
        self.assertViewErrorGet(self.ctrl.plmobject_url + "doc-cad/add/")
        # post
        doc = DocumentController.create("Doc", "Document", "a", self.user, self.DATA)
        self.assertViewErrorPost(self.ctrl.plmobject_url + "doc-cad/",
                type="Document", reference="Doc", revision="a")
        self.assertEquals(0, models.DocumentPartLink.current_objects.count())

    def test_files(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user, self.DATA)
        doc.object.state =doc.object.lifecycle.official_state
        doc.object.save()
        doc.add_reader(self.restricted_user)
        self.assertViewErrorGet(doc.plmobject_url + "files/")
        self.assertViewErrorGet(doc.plmobject_url + "files/add/")

    def test_invalid_download(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user, self.DATA)
        df = doc.add_file(self.get_file("plop"))
        doc.object.state =doc.object.lifecycle.official_state
        doc.object.save()
        doc.add_reader(self.restricted_user)
        self.assertViewErrorGet("/file/%d/" % df.id)

    def test_invalid_public_download(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user, self.DATA)
        df = doc.add_file(self.get_file("plop"))
        doc.object.state =doc.object.lifecycle.official_state
        doc.object.save()
        self.assert404("/file/public/%d/" % df.id)

    def test_search(self):
        self.assertViewErrorGet("/search/", type="Part", q="*")


    # valid responses

    def test_home(self):
        response = self.client.get("/home/")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "home.html")
        self.assertRaises(KeyError, lambda: response["pending_invitations_owner"])
        self.assertRaises(KeyError, lambda: response["pending_invitations_guest"])

    def test_user_attributes(self):
        response = self.client.get("/user/%s/attributes/" % self.restricted_user.username)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "attributes.html")

    def test_user_password_get(self):
        response = self.client.get("/user/%s/password/" % self.restricted_user.username)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "users/password.html")

    def test_user_password_post(self):
        response = self.client.post("/user/%s/password/" % self.restricted_user.username,
                {"old_password": "ru", "new_password1":"ru2", "new_password2": "ru2"}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "attributes.html")

    def test_valid_download(self):
        content = "pif paf pouf"
        doc = DocumentController.create("Doc", "Document", "a", self.user, self.DATA)
        df = doc.add_file(self.get_file(data=content))
        doc.object.state =doc.object.lifecycle.official_state
        doc.object.save()
        doc.add_reader(self.restricted_user)
        response = self.client.get("/file/public/%d/" % df.id)
        self.assertEqual(content, "".join(response.streaming_content))

    def test_valid_public(self):
        response = self.client.get(self.ctrl.plmobject_url + "public/")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "public.html")
        ctx = response.context
        self.assertEquals(1, len(ctx["revisions"]))
        self.assertFalse(ctx["attached"])

    def test_valid_public_attached_doc1(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user, self.DATA)
        doc.attach_to_part(self.ctrl.object)
        doc.object.state =doc.object.lifecycle.official_state
        doc.object.save()
        doc.add_reader(self.restricted_user)
        response = self.client.get(self.ctrl.plmobject_url + "public/")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "public.html")
        ctx = response.context
        self.assertEquals(1, len(ctx["revisions"]))
        self.assertEqual(doc.id, ctx["attached"][0].id)

    def test_valid_public_attached_doc2(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user, self.DATA)
        doc.attach_to_part(self.ctrl.object)
        doc.object.state =doc.object.lifecycle.official_state
        doc.object.published = True
        doc.object.save()
        response = self.client.get(self.ctrl.plmobject_url + "public/")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "public.html")
        ctx = response.context
        self.assertEquals(1, len(ctx["revisions"]))
        self.assertEqual(doc.id, ctx["attached"][0].id)

    def test_valid_public_attached_doc3(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user, self.DATA)
        doc.attach_to_part(self.ctrl.object)
        doc.object.state =doc.object.lifecycle.official_state
        doc.object.save()
        response = self.client.get(self.ctrl.plmobject_url + "public/")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "public.html")
        ctx = response.context
        self.assertEquals(1, len(ctx["revisions"]))
        self.assertFalse(ctx["attached"])

    def test_browse(self):
        # create invisible parts
        p2 = self.create("Part2")
        p3 = self.create("Part3")
        response = self.client.get("/browse/object/")
        self.assertTrue(response.context["restricted"])
        objects = response.context["objects"]
        self.assertEquals(1, objects.paginator.count)
        self.assertEquals(self.ctrl.object, objects.object_list[0].part)

        p3.object.published = True
        p3.object.save()
        response = self.client.get("/browse/object/")
        objects = response.context["objects"]
        self.assertTrue(response.context["restricted"])
        self.assertEquals(2, objects.paginator.count)
        self.assertEquals([p3.object, self.ctrl.object],
                [p.part for p in objects.object_list])

    def test_browse_error_user(self):
        self.assert404("/browse/user/")
        self.assert404("/browse/group/")

    def test_parts_doc_cad(self):
        response = self.client.get("/user/%s/parts-doc-cad/" % self.restricted_user.username)
        self.assertEquals(200, response.status_code)
        self.assertTemplateUsed(response, "users/plmobjects.html")
        self.assertRaises(KeyError, lambda: response.context["last_edited_objects"])
        links = response.context["object_user_link"]
        self.assertEquals(1, len(links))
        link = links[0]
        self.assertEquals(models.ROLE_READER, link["role"])
        self.assertEquals(self.ctrl.reference, link["plmobject__reference"])
        self.assertEquals(self.ctrl.type, link["plmobject__type"])
        self.assertEquals(self.ctrl.reference, link["plmobject__reference"])

