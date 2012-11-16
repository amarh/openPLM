
import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PartController, DocumentController

from openPLM.plmapp.tests.base import BaseTestCase


class SynchronizedTestCase(BaseTestCase):

    def setUp(self):
        super(SynchronizedTestCase, self).setUp()
        self.c1 = PartController.create("aPart1", self.TYPE, "a",
                                                 self.user, self.DATA)
        self.c2 = PartController.create("aPart2", self.TYPE, "a",
                                                  self.user, self.DATA)
        self.c3 = PartController.create("aPart3", self.TYPE, "a",
                                                  self.user, self.DATA)
        self.c4 = PartController.create("aPart4", self.TYPE, "a",
                                                  self.user, self.DATA)
        self.c5 = PartController.create("aPart5", self.TYPE, "a",
                                                  self.user, self.DATA)

        self.doc = DocumentController.create("doc_1", "Document", "a",
                    self.user, self.DATA)
        self.doc.promote(checked=True)

    def assertPromotable(self, *controllers):
        for c in controllers:
            self.assertTrue(c.object.is_promotable())

    def assertNotPromotable(self, *controllers):
        for c in controllers:
            self.assertFalse(c.object.is_promotable())

    def test_is_promotable_two_parts(self):
        models.SynchronizedPartSet.join(self.c1.object, self.c2.object)
        # no documents attached
        self.assertNotPromotable(self.c1, self.c2)

        # only one part attached to a document
        self.doc.attach_to_part(self.c1)
        self.assertNotPromotable(self.c1, self.c2)

        # both parts attached to a document: they are promotable
        self.doc.attach_to_part(self.c2)
        self.assertPromotable(self.c1, self.c2)

    def test_is_promotable_parent_and_child(self):
        models.SynchronizedPartSet.join(self.c1.object, self.c2.object)
        self.c1.add_child(self.c2, 5, 5)
        # no documents attached
        self.assertNotPromotable(self.c1, self.c2)

        # only c1 attached to a document
        self.doc.attach_to_part(self.c1)
        self.assertNotPromotable(self.c1, self.c2)
        
        # both parts attached to a document: they are promotable
        self.doc.attach_to_part(self.c2)
        self.assertPromotable(self.c1, self.c2)

        # only c2 attached to a document: still promotable
        self.c1.detach_document(self.doc)
        self.assertPromotable(self.c1, self.c2)

    def test_is_promotable_two_parents(self):
        models.SynchronizedPartSet.join(self.c1.object, self.c2.object)
        self.c1.add_child(self.c3, 5, 5)
        self.c2.add_child(self.c4, 5, 5)

        # children are draft
        self.assertNotPromotable(self.c1, self.c2)

        self.c3.promote(checked=True)
        # c4 is still a draft
        self.assertNotPromotable(self.c1, self.c2)

        # official children: promotables
        self.c4.promote(checked=True)
        self.assertPromotable(self.c1, self.c2)

    def test_is_promotable_more_parents(self):
        models.SynchronizedPartSet.join(self.c1.object, self.c2.object)
        models.SynchronizedPartSet.join(self.c3.object, self.c1.object)
        self.c1.add_child(self.c3, 5, 5)
        self.c2.add_child(self.c4, 5, 5)
        self.c1.add_child(self.c2, 45, 64)
        
        # c4 is draft, c3 has no document
        self.assertNotPromotable(self.c1, self.c2, self.c3)

        self.c4.promote(checked=True)
        # c3 has no document
        self.assertNotPromotable(self.c1, self.c2, self.c3)

        self.doc.attach_to_part(self.c3)
        # all requirements are met
        self.assertPromotable(self.c1, self.c2, self.c3)

