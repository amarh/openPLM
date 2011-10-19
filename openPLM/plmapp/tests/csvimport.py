
import cStringIO
from django.contrib.auth.models import User
from django.test import TransactionTestCase

from openPLM.plmapp.utils import *
from openPLM.plmapp.exceptions import *
from openPLM.plmapp.models import *
from openPLM.plmapp.controllers import *
from openPLM.plmapp.lifecycle import *
from openPLM.computer.models import *
from openPLM.office.models import *
from openPLM.cad.models import *
from openPLM.plmapp.csvimport import *
from openPLM.plmapp.unicodecsv import *
from openPLM.plmapp.base_views import *


class CSVImportTestCase(TransactionTestCase):
    CONTROLLER = PLMObjectController
    TYPE = "Part"
    DATA = {}

    def setUp(self):
        self.cie = User.objects.create(username="company")
        p = self.cie.get_profile()
        p.is_contributor = True
        p.save()
        self.leading_group = GroupInfo.objects.create(name="leading_group",
                owner=self.cie, creator=self.cie)
        self.cie.groups.add(self.leading_group)
        self.user = User(username="user")
        self.user.set_password("password")
        self.user.save()
        self.user.get_profile().is_contributor = True
        self.user.get_profile().save()
        self.group = GroupInfo(name="grp", owner=self.user, creator=self.user,
                description="grp")
        self.group.save()
        self.user.groups.add(self.group)
        self.DATA["group"] = self.group

    def get_valid_rows(self):
        return [[u'Type',
              u'reference',
              u'revision',
              u'name',
              u'supplier',
              u'group',
              u'lifecycle'],
             [u'Part',
              u'p1',
              u'a',
              u'Part1',
              u'Moi',
              self.group.name,
              u'draft_official_deprecated'],
             [u'Document',
              u'd1',
              u'2',
              u'Document1',
              u'',
              self.group.name,
              u'draft_official_deprecated'],
             [u'Document',
              u'd2',
              u'7',
              u'Document 2',
              u'',
              self.group.name,
              u'draft_official_deprecated'],
             [u'SinglePart',
              u'sp1',
              u's',
              u'SP1',
              u'Lui',
              self.group.name,
              u'draft_official_deprecated']]

    def test_import_valid(self):
        csv_rows = self.get_valid_rows()
        csv_file = cStringIO.StringIO()
        UnicodeWriter(csv_file).writerows(csv_rows)
        csv_file.seek(0)
        importer = PLMObjectsImporter(csv_file, self.user)
        headers = importer.get_preview().guessed_headers
        objects = importer.import_csv(headers)
        self.assertEquals(len(csv_rows) - 1, len(objects))
        sp1 = get_obj("SinglePart", "sp1", "s", self.user)
        self.assertEquals("SP1", sp1.name)

    def test_import_csv_invalid_last_row(self):
        """
        Tests that an import with an invalid row doest not modify
        the database.
        """
        csv_file = cStringIO.StringIO()
        csv_rows = self.get_valid_rows()
        csv_rows.append(["BadType", "bt", "1", "BT",
            self.group.name, u'draft_official_deprecated'])
        plmobjects = list(PLMObject.objects.all())
        UnicodeWriter(csv_file).writerows(csv_rows)
        csv_file.seek(0)
        importer = PLMObjectsImporter(csv_file, self.user)
        headers = importer.get_preview().guessed_headers
        self.assertRaises(CSVImportError, importer.import_csv, headers)
        self.assertEquals(plmobjects, list(PLMObject.objects.all()))


