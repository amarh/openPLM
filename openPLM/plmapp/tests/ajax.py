from json import JSONDecoder
from django.core.files.base import ContentFile

from openPLM.plmapp.tests.views import CommonViewTest
from openPLM.plmapp.controllers.document import DocumentController


class AjaxTestCase(CommonViewTest):


    def get(self, url, **get):
        return JSONDecoder().decode(self.client.get(url, get).content)

    def post(self, url, **post):
        return JSONDecoder().decode(self.client.post(url, post).content)

    def test_creation_form(self):
        for t in ("Part", "Document", "Group"):
            response = self.get("/ajax/create/", type=t)
            self.assertFalse(response["reload"])
            self.assertEqual(t, response["type"])
            form = response["form"]

    def test_creation_form_update_reference(self):
        """ Tests that references are updated when the type switches from a
        part and a document. Related ticket: #99"""
        response = self.get("/ajax/create/", type="Part")
        self.assertFalse(response["reload"])
        self.assertTrue("PART_0" in response["form"])
        response = self.get("/ajax/create/", type="Document", reference="PART_00001")
        self.assertFalse("PART_0" in response["form"])
        self.assertTrue("DOC_0" in response["form"])
        # if the type does not change, the reference must not change
        response = self.get("/ajax/create/", type="Document", reference="DOC_00150")
        self.assertFalse("PART_0" in response["form"])
        self.assertTrue("DOC_00150" in response["form"])

    def test_auto_complete_part(self):
        self.create("Other")
        completions = self.get("/ajax/complete/Part/reference/", term="Pa")
        self.assertEquals(["Part1"], completions)

    def test_auto_complete_part2(self):
        self.create("Part2")
        completions = self.get("/ajax/complete/Part/reference/", term="Pa")
        self.assertEquals(["Part1", "Part2"], completions)

    def test_auto_complete_empty(self):
        completions = self.get("/ajax/complete/Part/reference/", term="Nothing")
        self.assertEquals([], completions)

    def test_navigate(self):
        data = self.get("/ajax/navigate/Part/Part1/a/")
        self.assertTrue(int(data["width"] > 0))
        self.assertTrue(int(data["height"] > 0))
        self.assertTrue("form" in data)
        self.assertTrue("divs" in data)

    def test_can_add_child_ok(self):
        p2 = self.create("part2")
        data = self.get("/ajax/can_add_child/%d/" % self.controller.id,
                type=p2.type, reference=p2.reference, revision=p2.revision)
        self.assertTrue(data["can_add"])

    def test_can_add_child_existing_child(self):
        p2 = self.create("part2")
        self.controller.add_child(p2, 10, 10)
        data = self.get("/ajax/can_add_child/%d/" % self.controller.id,
                type=p2.type, reference=p2.reference, revision=p2.revision)
        self.assertFalse(data["can_add"])

    def test_can_add_child_parent(self):
        p2 = self.create("part2")
        p2.add_child(self.controller, 10, 10)
        data = self.get("/ajax/can_add_child/%d/" % self.controller.id,
                type=p2.type, reference=p2.reference, revision=p2.revision)
        self.assertFalse(data["can_add"])

    def test_can_add_child_self(self):
        p2 = self.controller
        data = self.get("/ajax/can_add_child/%d/" % self.controller.id,
                type=p2.type, reference=p2.reference, revision=p2.revision)
        self.assertFalse(data["can_add"])

    def test_can_add_child_document(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.get("/ajax/can_add_child/%d/" % self.controller.id,
                type=doc.type, reference=doc.reference, revision=doc.revision)
        self.assertFalse(data["can_add"])

    def test_add_child_get(self):
        p2 = self.create("part2")
        data = self.get("/ajax/add_child/%d/" % self.controller.id,
                type=p2.type, reference=p2.reference, revision=p2.revision)
        parent = data["parent"]
        self.assertEqual(self.controller.id, parent["id"])
        self.assertEqual(self.controller.type, parent["type"])
        self.assertEqual(self.controller.reference, parent["reference"])
        self.assertEqual(self.controller.revision, parent["revision"])
        self.assertTrue("form" in data)

    def test_add_child_post(self):
        p2 = self.create("part2")
        data = self.post("/ajax/add_child/%d/" % self.controller.id,
                type=p2.type, reference=p2.reference, revision=p2.revision,
                quantity="10", order="10", unit="g")
        self.assertEqual("ok", data["result"])

        link = self.controller.get_children()[0].link
        self.assertEqual(link.parent.id, self.controller.id)
        self.assertEqual(link.child.id, p2.id)
        self.assertEqual(link.quantity, 10)
        self.assertEqual(link.order, 10)

    def test_add_child_post_error(self):
        p2 = self.create("part2")
        data = self.post("/ajax/add_child/%d/" % self.controller.id,
                type=p2.type, reference=p2.reference, revision=p2.revision,
                quantity="badvalue", order="10")
        self.assertEqual("error", data["result"])
        self.assertEqual([], self.controller.get_children())

    def test_can_attach_part_doc(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.get("/ajax/can_attach/%d/" % self.controller.id,
                type=doc.type, reference=doc.reference, revision=doc.revision)
        self.assertTrue(data["can_attach"])

    def test_can_attach_doc_part(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.get("/ajax/can_attach/%d/" % doc.id,
                type=self.controller.type, reference=self.controller.reference,
                revision=self.controller.revision)
        self.assertTrue(data["can_attach"])

    def test_can_attach_part_part(self):
        p2 = self.create("part2")
        data = self.post("/ajax/can_attach/%d/" % self.controller.id,
                type=p2.type, reference=p2.reference, revision=p2.revision)
        self.assertFalse(data["can_attach"])

    def test_can_attach_doc_doc(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.post("/ajax/can_attach/%d/" % doc.id,
                type=doc.type, reference=doc.reference, revision=doc.revision)
        self.assertFalse(data["can_attach"])

    def test_can_attach_attached(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        self.controller.attach_to_document(doc)
        data = self.get("/ajax/can_attach/%d/" % self.controller.id,
                type=doc.type, reference=doc.reference, revision=doc.revision)
        self.assertFalse(data["can_attach"])

    def test_attach_get(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.get("/ajax/attach/%d/" % self.controller.id,
                type=doc.type, reference=doc.reference, revision=doc.revision)
        plmobject = data["plmobject"]
        self.assertEqual(self.controller.id, plmobject["id"])
        self.assertEqual(self.controller.type, plmobject["type"])
        self.assertEqual(self.controller.reference, plmobject["reference"])
        self.assertEqual(self.controller.revision, plmobject["revision"])
        self.assertTrue("form" in data)

    def test_attach_part_doc_post(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.post("/ajax/attach/%d/" % self.controller.id,
                type=doc.type, reference=doc.reference, revision=doc.revision)
        self.assertEqual("ok", data["result"])
        link = self.controller.get_attached_documents()[0]
        self.assertEqual(doc.id, link.document.id)

    def test_attach_doc_part_post(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        data = self.post("/ajax/attach/%d/" % doc.id,
                type=self.controller.type, reference=self.controller.reference,
                revision=self.controller.revision)
        self.assertEqual("ok", data["result"])
        link = self.controller.get_attached_documents()[0]
        self.assertEqual(doc.id, link.document.id)

    def test_attach_doc_part_post_error(self):
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        self.controller.attach_to_document(doc)
        data = self.post("/ajax/attach/%d/" % doc.id,
                type=self.controller.type, reference=self.controller.reference,
                revision=self.controller.revision)
        self.assertEqual("error", data["result"])

    def test_thumbnails(self):
        # create a document with a file
        doc = DocumentController.create("Doc", "Document", "a", self.user,
                self.DATA)
        thumbnail = ContentFile(file("datatests/thumbnail.png").read())
        thumbnail.name = "Thumbnail.png"
        doc.add_file(self.get_file())
        f2 = doc.files.all()[0]
        doc.add_thumbnail(f2, thumbnail)

        data = self.get("/ajax/thumbnails/%s/%s/%s/" % (doc.type, doc.reference,
            doc.revision))
        files = data["files"]
        self.assertEqual(1, len(files))
        # download the file and the thumbnail
        response_file = self.client.get(files[0]["url"])
        self.assertEqual(response_file.status_code, 200)
        response_img = self.client.get(files[0]["img"])
        self.assertEqual(response_img.status_code, 200)

