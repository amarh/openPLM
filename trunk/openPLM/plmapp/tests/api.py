from json import JSONDecoder
from django.core.files.base import ContentFile

from openPLM.plmapp.tests.views import CommonViewTest
from openPLM.plmapp.controllers import DocumentController, PartController

class ApiTestCase(CommonViewTest):

    def get(self, url, **get):
        return JSONDecoder().decode(self.client.get(url, get,
                HTTP_USER_AGENT="openplm").content)

    def post(self, url, **post):
        return JSONDecoder().decode(self.client.post(url, post,
            HTTP_USER_AGENT="openplm").content)

    def test_login(self):
        data = self.post("/api/login/", username=self.user.username, password="password")
        self.assertEqual("ok", data["result"])
        self.assertEqual(self.user.username, data["username"])

    def test_login_error(self):
        data = self.post("/api/login/", username=self.user.username, password="fail")
        self.assertEqual("error", data["result"])

    def test_get_all_types(self):
        data = self.get("/api/types/")
        self.assertEqual("ok", data["result"])
        self.assertTrue("Part" in data["types"])
        self.assertTrue("Document" in data["types"])

    def test_get_all_docs(self):
        data = self.get("/api/docs/")
        self.assertEqual("ok", data["result"])
        self.assertFalse("Part" in data["types"])
        self.assertTrue("Document" in data["types"])
        self.assertTrue("OfficeDocument" in data["types"])

    def test_get_all_parts(self):
        data = self.get("/api/parts/")
        self.assertEqual("ok", data["result"])
        self.assertTrue("Part" in data["types"])
        self.assertFalse("Document" in data["types"])
        self.assertTrue("SinglePart" in data["types"])

    def test_test_login(self):
        data = self.get("/api/testlogin/")
        self.assertEqual("ok", data["result"])

    def test_search(self):
        for url in ("/api/search/", "/api/search/false/",
                "/api/search/false/false/"):
            data = self.get(url, type="Part", q="reference=Pa*")
            self.assertEqual("ok", data["result"])
            self.assertEqual(1, len(data["objects"]))
            part = data["objects"][0]
            self.assertEqual(self.controller.name, part["name"])
            self.assertEqual(self.controller.id, part["id"])
            self.assertEqual(self.controller.revision, part["revision"])

    def test_search_editable_only(self):
        self.attach_to_official_document()
        self.controller.promote()
        data = self.get("/api/search/true/", type="Part", q="reference=Pa*")
        self.assertEqual("ok", data["result"])
        self.assertEqual(0, len(data["objects"]))

    def test_search_error_missing_type(self):
        data = self.get("/api/search/")
        self.assertEqual("error", data["result"])

    def test_search_with_file_only(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.get("/api/search/true/true/", type="Document")
        self.assertEqual("ok", data["result"])
        self.assertEqual(0, len(data["objects"]))

        doc.add_file(self.get_file())
        data = self.get("/api/search/true/true/", type="Document")
        self.assertEqual("ok", data["result"])
        self.assertEqual(1, len(data["objects"]))

        d = data["objects"][0]
        self.assertEqual(doc.name, d["name"])
        self.assertEqual(doc.id, d["id"])
        self.assertEqual(doc.revision, d["revision"])

    def test_get_search_fields(self):
        data = self.get("/api/search_fields/Part/")
        self.assertEqual("ok", data["result"])
        fields = data["fields"]
        reference_field = [f for f in fields if f["name"] == "q"][0]
        self.assertEqual("text", reference_field["type"])

    def test_get_creation_fields_part(self):
        data = self.get("/api/creation_fields/Part/")
        self.assertEqual("ok", data["result"])
        fields = data["fields"]
        name_field = [f for f in fields if f["name"] == "name"][0]
        self.assertEqual("text", name_field["type"])
        reference_field = [f for f in fields if f["name"] == "reference"][0]
        self.assertEqual("text", reference_field["type"])
        group_field = [f for f in fields if f["name"] == "group"][0]
        self.assertTrue(group_field["choices"])

    def test_get_creation_fields_harddisk(self):
        data = self.get("/api/creation_fields/HardDisk/")
        self.assertEqual("ok", data["result"])
        fields = data["fields"]
        name_field = [f for f in fields if f["name"] == "name"][0]
        self.assertEqual("text", name_field["type"])
        capacity_field = [f for f in fields if f["name"] == "capacity_in_go"][0]
        self.assertEqual("int", capacity_field["type"])

    def test_get_creation_fields_unknown_type(self):
        data = self.get("/api/creation_fields/UnknownType/")
        self.assertEqual("error", data["result"])

    def test_create(self):
        data = self.post("/api/create/", type="Document", name="docu",
                reference="DocRef", revision="0", group=self.group.id,
                lifecycle="draft_official_deprecated")
        self.assertEqual("ok", data["result"])
        obj = data["object"]
        self.assertEqual("DocRef", obj["reference"])

    def test_create_error_missing_lifecycle(self):
        data = self.post("/api/create/", type="Document", name="docu",
                reference="DocRef", revision="0", group=self.group.id)
        self.assertEqual("error", data["result"])

    def test_next_revision(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.get("/api/object/%d/next_revision/" % doc.id)
        self.assertEqual("ok", data["result"])
        self.assertEqual("b", data["revision"])

    def test_is_revisable(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.get("/api/object/%d/is_revisable/" % doc.id)
        self.assertEqual("ok", data["result"])
        self.assertEqual(True, data["revisable"])

        doc.revise("b")
        data = self.get("/api/object/%d/is_revisable/" % doc.id)
        self.assertEqual("ok", data["result"])
        self.assertEqual(False, data["revisable"])

    def test_revise(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.post("/api/object/%d/revise/" % doc.id, revision="b")
        self.assertEqual("ok", data["result"])
        new_doc = data["doc"]
        revb = doc.get_next_revisions()[0]
        self.assertEqual("b", new_doc["revision"])
        self.assertEqual("b", revb.revision)
        self.assertEqual(revb.id, new_doc["id"])

    def test_revise_error_not_revisable(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        rev = doc.revise("n")
        data = self.post("/api/object/%d/revise/" % doc.id, revision="b")
        self.assertEqual("error", data["result"])
        self.assertEqual([rev.id], [o.id for o in doc.get_next_revisions()])

    def test_revise_error_missing_revision(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.post("/api/object/%d/revise/" % doc.id)
        self.assertEqual("error", data["result"])

    def test_get_files_empty(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.get("/api/object/%d/files/" % doc.id)
        self.assertEqual("ok", data["result"])
        self.assertEqual([], data["files"])

    def test_get_files(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        df = doc.add_file(self.get_file())
        data = self.get("/api/object/%d/files/" % doc.id)
        self.assertEqual("ok", data["result"])
        self.assertEqual([df.id], [f["id"] for f in data["files"]])

    def test_get_files_all(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        df = doc.add_file(self.get_file())
        doc.lock(df)
        data = self.get("/api/object/%d/files/" % doc.id)
        self.assertEqual("ok", data["result"])
        self.assertEqual([], data["files"])

        data = self.get("/api/object/%d/files/all/" % doc.id)
        self.assertEqual("ok", data["result"])
        self.assertEqual([df.id], [f["id"] for f in data["files"]])

    def test_add_file(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        mock_file = self.get_file()
        data = self.post("/api/object/%d/add_file/" % doc.id,
                filename=mock_file)
        self.assertEqual("ok", data["result"])
        self.assertTrue(doc.files)
        self.assertEqual(mock_file.name, data["doc_file"]["filename"])
        self.assertEqual(doc.files[0].id, data["doc_file"]["id"])

    def test_add_file_error_missing_file(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.post("/api/object/%d/add_file/" % doc.id)
        self.assertEqual("error", data["result"])
        self.assertFalse(doc.files)

    def test_attach_to_part(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.get("/api/object/%d/attach_to_part/%d/" %
                (doc.id, self.controller.id))
        self.assertEqual("ok", data["result"])
        self.assertEqual(self.controller.id, doc.get_attached_parts()[0].id)

    def test_is_locked(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        df = doc.add_file(self.get_file())
        data = self.get("/api/object/%d/is_locked/%d/" % (doc.id, df.id))
        self.assertEqual("ok", data["result"])
        self.assertFalse(data["locked"])

        doc.lock(df)
        data = self.get("/api/object/%d/is_locked/%d/" % (doc.id, df.id))
        self.assertEqual("ok", data["result"])
        self.assertTrue(data["locked"])

    def test_lock(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        df = doc.add_file(self.get_file())
        data = self.get("/api/object/%d/lock/%d/" % (doc.id, df.id))
        self.assertEqual("ok", data["result"])
        self.assertTrue(doc.files[0].locked)

    def test_unlock(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        df = doc.add_file(self.get_file())
        doc.lock(df)
        data = self.get("/api/object/%d/unlock/%d/" % (doc.id, df.id))
        self.assertEqual("ok", data["result"])
        self.assertFalse(doc.files[0].locked)

    def test_checkin(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        df = doc.add_file(self.get_file())
        mock_file = self.get_file(data="robert")
        data = self.post("/api/object/%d/checkin/%d/" % (doc.id, df.id),
                filename=mock_file)
        self.assertEqual("ok", data["result"])
        self.assertEqual("robert", doc.files[0].file.read())

    def test_add_thumbnail(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        df = doc.add_file(self.get_file())
        thumbnail = ContentFile(file("datatests/thumbnail.png").read())
        thumbnail.name = "Thumbnail.png"
        data = self.post("/api/object/%d/add_thumbnail/%d/" % (doc.id, df.id),
                filename=thumbnail)
        self.assertEqual("ok", data["result"])
        self.assertNotEqual(None, doc.files[0].thumbnail)

    def test_get(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.get("/api/get/%d/" % doc.id)
        wanted = {
            "id": doc.id,
            "reference": "Doc",
            "type": "Document",
            "revision": "a",
            "name": doc.name,
            }
        self.assertEqual("ok", data["result"])
        self.assertEqual(data["object"], wanted)

    def test_attached_parts_empty(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        url = "/api/object/%d/attached_parts/" % doc.id
        data = self.get(url)
        self.assertEqual(data["parts"], [])

    def test_attached_parts_one_part(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        doc.attach_to_part(self.controller)
        url = "/api/object/%d/attached_parts/" % doc.id
        data = self.get(url)
        wanted = [{
            "id": self.controller.id,
            "reference": self.controller.reference,
            "type": self.controller.type,
            "revision": self.controller.revision,
            "name": self.controller.name,
            }]
        self.assertEqual(data["parts"], wanted)

    def test_attached_parts_two_parts(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        doc.attach_to_part(self.controller)
        part2 = PartController.create("Part2", "Part", "a", self.user, self.DATA)
        doc.attach_to_part(part2)
        wanted = [
            {
                "id": self.controller.id,
                "reference": self.controller.reference,
                "type": self.controller.type,
                "revision": self.controller.revision,
                "name": self.controller.name,
            },
            {
                "id": part2.id,
                "reference": part2.reference,
                "type": part2.type,
                "revision": part2.revision,
                "name": part2.name,
            },
        ]
        key = lambda x: x["id"]
        url = "/api/object/%d/attached_parts/" % doc.id
        data = self.get(url)
        self.assertEqual(sorted(data["parts"], key=key), sorted(wanted, key=key))

    def test_attached_documents_empty(self):
        url = "/api/object/%d/attached_documents/" % self.controller.id
        data = self.get(url)
        self.assertEqual(data["documents"], [])

    def test_attached_documents_one_part(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        doc.attach_to_part(self.controller)
        url = "/api/object/%d/attached_documents/" % self.controller.id
        data = self.get(url)
        wanted = [{
            "id": doc.id,
            "reference": doc.reference,
            "type": doc.type,
            "revision": doc.revision,
            "name": doc.name,
            }]
        self.assertEqual(data["documents"], wanted)

    def test_attached_documents_two_parts(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        doc.attach_to_part(self.controller)
        doc2 = DocumentController.create("Doc2", "Document", "a", self.user,
                self.DATA)
        doc2.attach_to_part(self.controller)
        wanted = [
            {
                "id": doc.id,
                "reference": doc.reference,
                "type": doc.type,
                "revision": doc.revision,
                "name": doc.name,
            },
            {
                "id": doc2.id,
                "reference": doc2.reference,
                "type": doc2.type,
                "revision": doc2.revision,
                "name": doc2.name,
            },
        ]
        key = lambda x: x["id"]
        url = "/api/object/%d/attached_documents/" % self.controller.id
        data = self.get(url)
        self.assertEqual(sorted(data["documents"], key=key), sorted(wanted, key=key))


