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


from django.contrib import messages

from openPLM.plmapp import forms
import openPLM.plmapp.models as m
from openPLM.plmapp.controllers import DocumentController, PartController

from .main import ViewTest

class DocumentViewTestCase(ViewTest):

    TYPE = "Document"
    CONTROLLER = DocumentController

    def get_part(self, ref="P1"):
        return PartController.create(ref, "Part", "a", self.user,
               self.DATA, True, True)

    def test_related_parts_get(self):
        part = self.get_part()
        self.controller.attach_to_part(part)

        response = self.get(self.base_url + "parts/", page="parts")
        self.assertEqual([part.id],
                         [p.part.id for p in response.context["parts"]])
        self.assertEqual([part.id],
            [f.instance.part.id for f in response.context["parts_formset"].forms])

    def test_related_parts_update_post(self):
        part1 = self.get_part("part1")
        part2 = self.get_part("part2")
        self.controller.attach_to_part(part1)
        self.controller.attach_to_part(part2)
        data = {
                'form-TOTAL_FORMS' : '2',
                'form-INITIAL_FORMS' : '2',
                'form-MAX_NUM_FORMS' : '',

                'form-0-id' : part1.get_attached_documents()[0].id,
                'form-0-part' : part1.id,
                'form-0-document' : self.controller.id,
                'form-0-delete' : 'on',

                'form-1-id' : part2.get_attached_documents()[0].id,
                'form-1-part' : part2.id,
                'form-1-document' : self.controller.id,
                'form-1-delete' : '',
            }
        response = self.post(self.base_url + "parts/", data, page="parts")
        self.assertEqual(1, response.context["parts"].count())
        self.assertEqual(list(part2.get_attached_documents()),
                         list(response.context["parts"]))
        forms_ = response.context["forms"]
        self.assertEqual([part2.id],
                [f.instance.part.id for f in forms_.values()])

    def test_parts_update_post_empty_selection(self):
        part1 = self.get_part("part1")
        part2 = self.get_part("part2")
        self.controller.attach_to_part(part1)
        self.controller.attach_to_part(part2)
        data = {
                'form-TOTAL_FORMS' : '2',
                'form-INITIAL_FORMS' : '2',
                'form-MAX_NUM_FORMS' : '',

                'form-0-id' : part1.get_attached_documents()[0].id,
                'form-0-part' : part1.id,
                'form-0-document' : self.controller.id,
                'form-0-delete' : '',

                'form-1-id' : part2.get_attached_documents()[0].id,
                'form-1-part' : part2.id,
                'form-1-document' : self.controller.id,
                'form-1-delete' : '',
            }
        response = self.post(self.base_url + "parts/", data, page="parts")
        self.assertEqual(2, response.context["parts"].count())
        forms_ = response.context["forms"]
        self.assertEqual(set((part1.id, part2.id)),
                set(f.instance.part.id for f in forms_.values()))

    def test_doc_cad_update_post_all_selected(self):
        part1 = self.get_part("part1")
        part2 = self.get_part("part2")
        self.controller.attach_to_part(part1)
        self.controller.attach_to_part(part2)
        data = {
                'form-TOTAL_FORMS' : '2',
                'form-INITIAL_FORMS' : '2',
                'form-MAX_NUM_FORMS' : '',

                'form-0-id' : part1.get_attached_documents()[0].id,
                'form-0-part' : part1.id,
                'form-0-document' : self.controller.id,
                'form-0-delete' : 'on',

                'form-1-id' : part2.get_attached_documents()[0].id,
                'form-1-part' : part2.id,
                'form-1-document' : self.controller.id,
                'form-1-delete' : 'on',
            }
        response = self.post(self.base_url + "parts/", data, page="parts")
        self.assertEqual(0, response.context["parts"].count())
        self.assertFalse(response.context["forms"])

    def test_add_related_part_get(self):
        response = self.get(self.base_url + "parts/add/", link=True)
        self.assertTrue(isinstance(response.context["add_part_form"],
                                   forms.AddPartForm))
        attach = response.context["attach"]
        self.assertEqual(self.controller.id, attach[0].id)
        self.assertEqual("attach_part", attach[1])

    def test_add_related_part_post(self):
        part = self.get_part("part1")
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
        self.assertEqual("oh oh oh", "".join(response.streaming_content))

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
        # ensures the controller is promotable
        self.controller.add_file(self.get_file())
        super(DocumentViewTestCase, self).test_lifecycle()

    def test_lifecycle_bad_password(self):
        # ensures the controller is promotable
        self.controller.add_file(self.get_file())
        super(DocumentViewTestCase, self).test_lifecycle_bad_password()

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
        part = self.get_part("part1")
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
        part = self.get_part("part1")
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
        part = self.get_part("part1")
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
        self.assertFalse(rev.documentpartlink_document.now().exists())
        # ensure only the old revision is attached to part
        self.assertEqual([self.controller.id],
            list(part.get_attached_documents().values_list("document", flat=True)))

    def test_revise_two_attached_parts_get(self):
        """
        Tests a get request to revise a document with two attached parts.
        One part is a draft, the other is official.
        """
        part1 = self.get_part("part1")
        part2 = self.get_part("part2")
        self.controller.attach_to_part(part1)
        self.controller.attach_to_part(part2)
        part2.object.is_promotable = lambda: True
        part2.promote()
        response = self.get(self.base_url + "revisions/")
        # checks that it is necessary to confirm the revision
        self.assertTrue(response.context["confirmation"])
        formset = response.context["part_formset"]
        self.assertEqual(2, formset.total_form_count())
        form1, form2 = formset.forms
        self.assertTrue(form1.fields["selected"].initial)
        self.assertTrue(form2.fields["selected"].initial)
        self.assertEqual([part1.id, part2.id], sorted([form1.instance.id, form2.instance.id]))

    def test_revise_two_attached_parts_post(self):
        """
        Tests a post request to revise a document with two attached parts.
        One part is a draft and not selected, the other is official and selected.
        """
        part1 = self.get_part("part1")
        part2 = self.get_part("part2")
        self.controller.attach_to_part(part1)
        self.controller.attach_to_part(part2)
        part2.object.is_promotable = lambda: True
        part2.promote()
        data = {
            "revision" : "b",
             "form-TOTAL_FORMS" : "2",
             "form-INITIAL_FORMS" : "2",
             "form-0-selected" : "",
             "form-0-plmobject_ptr" : part1.id,
             "form-1-selected" : "on",
             "form-1-plmobject_ptr" : part2.id,
             }
        response = self.post(self.base_url + "revisions/", data)
        revisions = self.controller.get_next_revisions()
        self.assertEqual(1, len(revisions))
        rev = revisions[0].document
        self.assertEqual("b", rev.revision)
        # ensure p1 and p2 are still attached to the old revision
        parts = self.controller.get_attached_parts().values_list("part", flat=True)
        self.assertEqual([part1.id, part2.id], sorted(parts))
        # ensure p2 is attached to the new revision
        parts = rev.documentpartlink_document.values_list("part", flat=True)
        self.assertEqual([part2.id], list(parts))
        # ensure both documents are attached to p2
        self.assertEqual([self.controller.id, rev.id],
            sorted(part2.get_attached_documents().values_list("document", flat=True)))

    def test_revise_one_deprecated_part_attached_get(self):
        """
        Tests a get request to revise a document which has one deprecated
        attached part.
        This part must not be suggested when the user revises the document.
        """
        part = self.get_part("part1")
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
        part = self.get_part("part1")
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
        self.assertFalse(rev.documentpartlink_document.now().exists())
        # ensure only the old revision is attached to part
        self.assertEqual([self.controller.id],
            list(part.get_attached_documents().values_list("document", flat=True)))

    def test_revise_one_attached_revised_part_get(self):
        """
        Tests a get request to revise a document which has one attached part.
        The part has been revised and so its revision must be suggested and
        the part must not be suggested when the user revises the document.
        """
        part = self.get_part("part1")
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
        part = self.get_part("part1")
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
        part = self.get_part("part1")
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

    def test_create_and_attach_get(self):
        """
        Tests a create request with a related part set.
        """
        part = self.get_part("part1")
        response = self.get("/object/create/", {"type" : self.TYPE,
            "__next__" : "/home/", "related_part" : part.id})
        self.assertEqual("/home/", response.context["next"])
        self.assertEqual(part.object, response.context["related"].object)
        self.assertEqual(str(part.id), str(response.context["related_part"]))
        self.assertTrue(isinstance(response.context["creation_type_form"],
            forms.DocumentTypeForm))

    def test_create_and_attach_post(self):
        part = self.get_part("part1")
        data = self.DATA.copy()
        data.update({
                "__next__" : "/home/",
                "related_part" : part.id,
                "type" : self.TYPE,
                "reference" : "doc2",
                "auto" : False,
                "revision" : "a",
                "name" : "Docc",
                "group" : str(self.group.id),
                "lifecycle" : m.get_default_lifecycle().pk,
                "state" : m.get_default_state().pk,
                })
        response = self.post("/object/create/", data, follow=False,
                status_code=302)
        self.assertRedirects(response, "/home/")
        obj = m.PLMObject.objects.get(type=self.TYPE, reference="doc2", revision="a")
        self.assertEqual("Docc", obj.name)
        self.assertEqual(self.user, obj.owner)
        self.assertEqual(self.user, obj.creator)
        link = m.DocumentPartLink.current_objects.get(document=obj, part=part.id)

    def test_create_and_attach_post_error(self):
        part = self.get_part("part1")
        # cancels the part so that it can not be attached
        part.cancel()
        data = self.DATA.copy()
        data.update({
                "__next__" : "/home/",
                "related_part" : part.id,
                "type" : self.TYPE,
                "reference" : "doc2",
                "auto" : False,
                "revision" : "a",
                "name" : "Docc",
                "group" : str(self.group.id),
                "lifecycle" : m.get_default_lifecycle().pk,
                "state" : m.get_default_state().pk,
                })
        response = self.post("/object/create/", data, follow=True, page="parts")
        msgs = list(response.context["messages"])
        self.assertEqual(2, len(msgs))
        self.assertEqual(messages.INFO, msgs[0].level)
        self.assertEqual(messages.ERROR, msgs[1].level)
        obj = m.PLMObject.objects.get(type=self.TYPE, reference="doc2", revision="a")
        self.assertEqual("Docc", obj.name)
        self.assertEqual(self.user, obj.owner)
        self.assertEqual(self.user, obj.creator)
        self.assertFalse(m.DocumentPartLink.current_objects.filter(
            document=obj, part=part.id).exists())


class SpecialCharactersDocumentViewTestCase(DocumentViewTestCase):
    REFERENCE = u"Pa *-\xc5\x93\xc3\xa9'"


