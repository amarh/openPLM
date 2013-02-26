# tests to checks that #108 (step management - Suggested part references
# are all the same) is fixed

import re
import datetime
from django.utils import timezone
from django.conf import settings

from openPLM.plmapp.references import get_new_reference, REFERENCE_PATTERNS
from openPLM.plmapp.models import Part, Document
from openPLM.plmapp.tests.base import BaseTestCase

class MockUser(object):
    username = "gege"
    first_name = "Hello"
    last_name = "World"

class SuggestedReferenceTestCase(BaseTestCase):

    def tearDown(self):
        settings.REFERENCE_PATTERNS = REFERENCE_PATTERNS

    def assertNewReference(self, expected, model, start=0):
        ref = get_new_reference(MockUser, model, start=start)
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

    def test_date_patterns(self):
        settings.REFERENCE_PATTERNS = {
                "shared": False,
                "part": ("{now:%y}-{number}-part", r'^\d\d-(\d+)-part$'),
                "doc": ("{now:%y}-{number}-doc", r'^\d\d-(\d+)-doc$'),
        }
        now = timezone.now()
        year = now.strftime("%y")
        self.create("%s-5-part" % year)
        self.assertNewReference("%s-6-part" % year, Part)
        self.assertNewReference("%s-1516-doc" % year, Document, 1515)

    def test_shared_patterns(self):
        settings.REFERENCE_PATTERNS = {
            "shared": True,
            "part": (u"OBJECT_{number:05d}", r"^OBJECT_(\d+)$"),
            "doc": (u"OBJECT_{number:05d}", r"^OBJECT_(\d+)$"),
        }
        self.assertNewReference("OBJECT_00001", Part)
        self.create("OBJECT_00002", "Document")
        self.create("OBJECT_00003")
        self.assertNewReference("OBJECT_00004", Part)
        self.assertNewReference("OBJECT_00004", Document)
        self.create("OBJECT_00010")
        self.assertNewReference("OBJECT_00011", Document)
        self.assertNewReference("OBJECT_00011", Part)

    def test_shared_distinct_patterns(self):
        settings.REFERENCE_PATTERNS = {
            "shared": True,
            "part": (u"PART_{number:05d}", r"^(?:PART|DOC)_(\d+)$"),
            "doc": (u"DOC_{number:05d}", r"^(?:PART|DOC)_(\d+)$"),
        }
        self.assertNewReference("PART_00001", Part)
        self.create("DOC_00002", "Document")
        self.create("PART_00003")
        self.assertNewReference("PART_00004", Part)
        self.assertNewReference("DOC_00004", Document)
        self.create("PART_00010")
        self.assertNewReference("DOC_00011", Document)
        self.assertNewReference("PART_00011", Part)

    def test_user_patterns(self):
        settings.REFERENCE_PATTERNS = {
            "shared": False,
            "part": (u"PART_{number:05d}-{user.username}-{initials}",
                r"^PART_(\d+)-.*$"),
            "doc": (u"DOC_{number:05d}-{user.first_name}-{initials}",
                r"^DOC_(\d+)-.*$"),
        }
        self.assertNewReference("PART_00001-gege-HW", Part)
        self.create("PART_00004-545-55")
        self.assertNewReference("PART_00005-gege-HW", Part)
        self.assertNewReference("DOC_00001-Hello-HW", Document)

    def test_compiled_patterns(self):
        settings.REFERENCE_PATTERNS = {
            "shared": True,
            "part": (u"OBJECT_{number:05d}", re.compile(r"^OBJECT_(\d+)$")),
            "doc": (u"OBJECT_{number:05d}", re.compile(r"^OBJECT_(\d+)$")),
        }
        self.assertNewReference("OBJECT_00001", Part)
        self.create("OBJECT_00002", "Document")
        self.create("OBJECT_00003")
        self.assertNewReference("OBJECT_00004", Part)
        self.assertNewReference("OBJECT_00004", Document)
        self.create("OBJECT_00010")
        self.assertNewReference("OBJECT_00011", Document)
        self.assertNewReference("OBJECT_00011", Part)

