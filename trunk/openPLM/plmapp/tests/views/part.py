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

class PartViewTestCase(ViewTest):

    def test_create_and_attach_get(self):
        """
        Tests a create request with a related document set.
        """
        doc = self.attach_to_official_document()
        response = self.get("/object/create/", {"type" : self.TYPE,
            "__next__" : "/home/", "related_doc" : doc.id})
        self.assertEqual("/home/", response.context["next"])
        self.assertEqual(doc.object, response.context["related"].object)
        self.assertEqual(str(doc.id), str(response.context["related_doc"]))
        self.assertTrue(isinstance(response.context["creation_type_form"],
            forms.PartTypeForm))

    def test_create_and_attach_post(self):
        doc = self.attach_to_official_document()
        data = self.DATA.copy()
        data.update({
                "__next__" : "/home/",
                "related_doc" : doc.id,
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
        response = self.post("/object/create/", data, follow=False,
                status_code=302)
        self.assertRedirects(response, "/home/")
        obj = m.PLMObject.objects.get(type=self.TYPE, reference="mapart", revision="a")
        self.assertEqual("MaPart", obj.name)
        self.assertEqual(self.user, obj.owner)
        self.assertEqual(self.user, obj.creator)
        link = m.DocumentPartLink.current_objects.get(document=doc.object, part=obj)

    def test_create_and_attach_post_error(self):
        doc = self.attach_to_official_document()
        # cancels the doc so that it can not be attached
        doc.cancel()
        data = self.DATA.copy()
        data.update({
                "__next__" : "/home/",
                "related_doc" : doc.id,
                "type" : self.TYPE,
                "reference" : "mapart",
                "auto" : False,
                "revision" : "a",
                "name" : "MaPart",
                "group" : str(self.group.id),
                "lifecycle" : m.get_default_lifecycle().pk,
                "state" : m.get_default_state().pk,
                })
        response = self.post("/object/create/", data, follow=True, page="doc-cad")
        msgs = list(response.context["messages"])
        self.assertEqual(2, len(msgs))
        self.assertEqual(messages.INFO, msgs[0].level)
        self.assertEqual(messages.ERROR, msgs[1].level)
        obj = m.PLMObject.objects.get(type=self.TYPE, reference="mapart", revision="a")
        self.assertEqual("MaPart", obj.name)
        self.assertEqual(self.user, obj.owner)
        self.assertEqual(self.user, obj.creator)
        self.assertFalse(m.DocumentPartLink.current_objects.filter(
            document=doc.object, part=obj).exists())

    def test_children(self):
        child1 = PartController.create("c1", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child1, 10 , 20)
        child2 = PartController.create("c2", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child2, 10, 20)
        response = self.get(self.base_url + "BOM-child/", page="BOM-child")
        self.assertEqual(2, len(list(response.context["children"])))
        form = response.context["display_form"]

    def test_children_last_level(self):
        """
        Tests the children view, shows only the last level.

        self
         -> c1
             -> c4
                 -> c6
             -> c5
         -> c2
         -> c3
             -> c7
             -> c8

        last level: (c4 -> c6), (c1 -> c5), (self -> c2), (c3 -> c7), (c3 -> c8)
        """
        child1 = PartController.create("c1", "Part", "a", self.user, self.DATA)
        ls1 = self.controller.add_child(child1, 10 , 20)
        child2 = PartController.create("c2", "Part", "a", self.user, self.DATA)
        ls2 = self.controller.add_child(child2, 10, 21)
        child3 = PartController.create("c3", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child3, 10, 22)
        child4 = PartController.create("c4", "Part", "a", self.user, self.DATA)
        l14 = child1.add_child(child4, 10, 23)
        child5 = PartController.create("c5", "Part", "a", self.user, self.DATA)
        l15 = child1.add_child(child5, 10, 24)
        child6 = PartController.create("c6", "Part", "a", self.user, self.DATA)
        l46 = child4.add_child(child6, 10, 25)
        child7 = PartController.create("c7", "Part", "a", self.user, self.DATA)
        l37 = child3.add_child(child7, 10, 26)
        child8 = PartController.create("c8", "Part", "a", self.user, self.DATA)
        l38 = child3.add_child(child8, 10, 27)
        response = self.get(self.base_url + "BOM-child/",
                {"level":"last", "state" : "all"},
                page="BOM-child")
        children = response.context["children"]
        self.assertEqual(5, len(children))
        self.assertEqual([l46, l15, ls2, l37, l38], [c.link for c in children])

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
        self.assertEqual(0, len(list(response.context["documents"])))

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
        self.assertEqual(2, response.context["documents"].count())
        forms_ = response.context["forms"]
        self.assertEqual([doc1.id], [f.instance.document.id for f in forms_.values()])

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

    def test_doc_cad_update_post(self):
        doc1 = DocumentController.create("doc1", "Document", "a", self.user,
                self.DATA)
        doc2 = DocumentController.create("doc2", "Document", "a", self.user,
                self.DATA)
        self.controller.attach_to_document(doc1)
        self.controller.attach_to_document(doc2)
        data = {
                'form-TOTAL_FORMS' : '2',
                'form-INITIAL_FORMS' : '2',
                'form-MAX_NUM_FORMS' : '',

                'form-0-id' : doc1.get_attached_parts()[0].id,
                'form-0-part' : self.controller.id,
                'form-0-document' : doc1.id,
                'form-0-delete' : 'on',

                'form-1-id' : doc2.get_attached_parts()[0].id,
                'form-1-part' : self.controller.id,
                'form-1-document' : doc2.id,
                'form-1-delete' : '',
            }
        response = self.post(self.base_url + "doc-cad/", data, page="doc-cad")
        self.assertEqual(1, response.context["documents"].count())
        self.assertEqual(list(doc2.get_attached_parts()),
                         list(response.context["documents"]))
        forms_ = response.context["forms"]
        self.assertEqual([doc2.id], [f.instance.document.id for f in forms_.values()])

    def test_doc_cad_update_post_empty_selection(self):
        doc1 = DocumentController.create("doc1", "Document", "a", self.user,
                self.DATA)
        doc2 = DocumentController.create("doc2", "Document", "a", self.user,
                self.DATA)
        self.controller.attach_to_document(doc1)
        self.controller.attach_to_document(doc2)
        data = {
                'form-TOTAL_FORMS' : '2',
                'form-INITIAL_FORMS' : '2',
                'form-MAX_NUM_FORMS' : '',

                'form-0-id' : doc1.get_attached_parts()[0].id,
                'form-0-part' : self.controller.id,
                'form-0-document' : doc1.id,
                'form-0-delete' : '',

                'form-1-id' : doc2.get_attached_parts()[0].id,
                'form-1-part' : self.controller.id,
                'form-1-document' : doc2.id,
                'form-1-delete' : '',
            }
        response = self.post(self.base_url + "doc-cad/", data, page="doc-cad")
        self.assertEqual(2, response.context["documents"].count())
        forms_ = response.context["forms"]
        self.assertEqual(set((doc1.id, doc2.id)),
                set(f.instance.document.id for f in forms_.values()))

    def test_doc_cad_update_post_all_selected(self):
        doc1 = DocumentController.create("doc1", "Document", "a", self.user,
                self.DATA)
        doc2 = DocumentController.create("doc2", "Document", "a", self.user,
                self.DATA)
        self.controller.attach_to_document(doc1)
        self.controller.attach_to_document(doc2)
        data = {
                'form-TOTAL_FORMS' : '2',
                'form-INITIAL_FORMS' : '2',
                'form-MAX_NUM_FORMS' : '',

                'form-0-id' : doc1.get_attached_parts()[0].id,
                'form-0-part' : self.controller.id,
                'form-0-document' : doc1.id,
                'form-0-delete' : 'on',

                'form-1-id' : doc2.get_attached_parts()[0].id,
                'form-1-part' : self.controller.id,
                'form-1-document' : doc2.id,
                'form-1-delete' : 'on',
            }
        response = self.post(self.base_url + "doc-cad/", data, page="doc-cad")
        self.assertEqual(0, response.context["documents"].count())
        self.assertFalse(response.context["forms"])

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
        self.assertFalse(rev.documentpartlink_part.now().exists())
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
        self.assertFalse(rev.documentpartlink_part.now().exists())
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
        # ensure the new revisison is a child of the parent
        children = parent2.get_children(1)
        self.assertEqual(1, len(children))
        level, link2 = children[0]
        self.assertEqual(parent2.id, link2.parent_id)
        self.assertEqual(link.order, link2.order)
        self.assertEqual(link.quantity, link2.quantity)
        self.assertEqual(link.unit, link2.unit)
        self.assertEqual(rev.id, link2.child_id)



class SpecialCharactersPartViewTestCase(PartViewTestCase):
    REFERENCE = u"Pa *-\xc5\x93\xc3\xa9'"

