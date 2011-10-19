
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
              u'draft_official_deprecated'],
             [u'SinglePart',
              u'sp2',
              u's',
              u'SP2',
              u'Lui',
              self.group.name,
              u'draft_official_deprecated'],
             ]


    def import_csv(self, Importer, rows):
        csv_file = cStringIO.StringIO()
        UnicodeWriter(csv_file).writerows(rows)
        csv_file.seek(0)
        importer = Importer(csv_file, self.user)
        headers = importer.get_preview().guessed_headers
        objects = importer.import_csv(headers)
        return objects

    def test_import_valid(self):
        csv_rows = self.get_valid_rows()
        objects = self.import_csv(PLMObjectsImporter, csv_rows)
        self.assertEquals(len(csv_rows) - 1, len(objects))
        sp1 = get_obj("SinglePart", "sp1", "s", self.user)
        self.assertEquals("SP1", sp1.name)

    def test_import_csv_invalid_last_row(self):
        """
        Tests that an import with an invalid row doest not modify
        the database.
        """
        csv_rows = self.get_valid_rows()
        csv_rows.append(["BadType", "bt", "1", "BT",
            self.group.name, u'draft_official_deprecated'])
        plmobjects = list(PLMObject.objects.all())
        self.assertRaises(CSVImportError, self.import_csv,
                PLMObjectsImporter, csv_rows)
        self.assertEquals(plmobjects, list(PLMObject.objects.all()))

    def get_valid_bom(self):
        return [["parent-type", "parent-reference", "parent-revision",
                 "child-type", "child-reference", "child-revision",
                 "quantity", "order"],
                ["Part", "p1", "a", "SinglePart", "sp1", "s", "10", "15"],
                ["SinglePart", "sp1", "s", "SinglePart", "sp2", "s", "10.5", "16"],
                ]

    def test_import_bom_valid(self):
        """
        Tests an import of a valid bom.
        """
        self.import_csv(PLMObjectsImporter, self.get_valid_rows())
        csv_rows = self.get_valid_bom()
        objects = self.import_csv(BOMImporter, csv_rows)
        # objects should be [parent1, child1, ...]
        self.assertEquals((len(csv_rows) - 1) * 2, len(objects))

        # first row
        parent = get_obj("Part", "p1", "a", self.user)
        child = get_obj("SinglePart", "sp1", "s", self.user)
        c = parent.get_children()[0]
        self.assertEquals(c.link.parent.id, parent.id)
        self.assertEquals(c.link.child.id, child.id)
        self.assertEquals(c.link.quantity, 10)
        self.assertEquals(c.link.order, 15)

        # second row
        parent = get_obj("SinglePart", "sp1", "s", self.user)
        child = get_obj("SinglePart", "sp2", "s", self.user)
        c = parent.get_children()[0]
        self.assertEquals(c.link.parent.id, parent.id)
        self.assertEquals(c.link.child.id, child.id)
        self.assertEquals(c.link.quantity, 10.5)
        self.assertEquals(c.link.order, 16)

    def test_import_bom_invalid_order(self):
        """
        Tests an import of an invalid bom: invalid order.
        """
        self.import_csv(PLMObjectsImporter, self.get_valid_rows())
        csv_rows = self.get_valid_bom()
        csv_rows[-1][-1] = "not an integer"
        self.assertRaises(CSVImportError, self.import_csv,
                          BOMImporter, csv_rows)
        self.assertEquals(0, len(ParentChildLink.objects.all()))
    
    def test_import_bom_invalid_parent(self):
        """
        Tests an import of an invalid bom: invalid parent.
        """
        self.import_csv(PLMObjectsImporter, self.get_valid_rows())
        csv_rows = self.get_valid_bom()
        csv_rows[1][0] = "not an type"
        self.assertRaises(CSVImportError, self.import_csv,
                          BOMImporter, csv_rows)
        self.assertEquals(0, len(ParentChildLink.objects.all()))

    def test_import_bom_invalid_duplicated_row(self):
        """
        Tests an import of an invalid bom: a row is duplicated.
        """
        self.import_csv(PLMObjectsImporter, self.get_valid_rows())
        csv_rows = self.get_valid_bom()
        csv_rows.append(csv_rows[-1])
        self.assertRaises(CSVImportError, self.import_csv,
                          BOMImporter, csv_rows)
        self.assertEquals(0, len(ParentChildLink.objects.all()))

