# tests to checks that #108 (step management - Suggested part references
# are all the same) is fixed 

from openPLM.plmapp.forms import get_new_reference
from openPLM.plmapp.models import Part, Document
from openPLM.plmapp.tests.base import BaseTestCase

class SuggestedReferenceTestCase(BaseTestCase):

    def assertNewReference(self, expected, model, start=0):
        ref = get_new_reference(model, start=start)
        self.assertEqual(expected, ref)

    def test_simple(self):
        self.create("PART_00001")
        self.assertNewReference("PART_00002", Part)

    def test_empty(self):
        self.assertNewReference("PART_00001", Part)
        self.assertNewReference("PART_00007", Part, 6)
        self.assertNewReference("DOC_00001", Document)
        self.assertNewReference("DOC_01516", Document, 1515)
        self.assertNewReference("DOC_421516", Document, 421515)

    def test_one_revision(self):
        p1 = self.create("PART_00001")
        p1_b = p1.revise("b")
        self.assertNewReference("PART_00002", Part)

    def test_small_gap(self):
        self.create("PART_00001")
        self.create("PART_00003")
        self.assertNewReference("PART_00004", Part)

    def test_big_gap(self):
        self.create("PART_00001")
        self.create("PART_00099")
        for i in range(10):
            self.assertNewReference("PART_00%d" % (100+i), Part, i)

    def test_unmatched_ref(self):
        self.create("plopppp")
        self.assertNewReference("PART_00001", Part)
        self.create("PART_00001")
        self.assertNewReference("PART_00002", Part)

