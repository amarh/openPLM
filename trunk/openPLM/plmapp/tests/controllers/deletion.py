import os
import datetime
from django.utils import timezone

import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import DocumentController
from openPLM.plmapp.files import deletable as dlt

from openPLM.plmapp.tests.base import BaseTestCase

on_checkin = list(dlt.ON_CHECKIN_SELECTORS)
on_delete = list(dlt.ON_DELETE_SELECTORS)
on_cancel = list(dlt.ON_CANCEL_SELECTORS)
on_deprecate = list(dlt.ON_DEPRECATE_SELECTORS)

class DeletionTestCase(BaseTestCase):
    TYPE = "Document"
    CONTROLLER = DocumentController
    DATA = {}

    def setUp(self):
        super(DeletionTestCase, self).setUp()
        self.controller = self.CONTROLLER.create("adoc", self.TYPE, "a",
                                                 self.user, self.DATA)
        self.old_files = []


    def tearDown(self):
        dlt.ON_CHECKIN_SELECTORS[:] = on_checkin
        dlt.ON_DELETE_SELECTORS[:] = on_delete
        dlt.ON_CANCEL_SELECTORS[:] = on_cancel
        dlt.ON_DEPRECATE_SELECTORS[:] = on_deprecate
        for f in list(self.controller.files.all()) + self.old_files:
            os.chmod(f.file.path, 0700)
            os.remove(f.file.path)

    def assertDeleted(self, doc_file):
        self.assertTrue(doc_file.deleted)
        self.assertTrue(doc_file.deprecated)
        self.assertFalse(os.path.exists(doc_file.file.path))

    def assertNotDeleted(self, doc_file):
        self.assertFalse(doc_file.deleted)
        self.assertTrue(doc_file.deprecated)
        self.assertTrue(os.path.exists(doc_file.file.path))

    def test_delete_file(self):
        self.controller.add_file(self.get_file())
        f2 = self.controller.files.all()[0]
        path = f2.file.path
        self.controller.delete_file(f2)
        self.assertEqual([], list(self.controller.files.all()))
        self.assertFalse(os.path.exists(path))
 
    def test_checkin_keep_all(self):
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.yes, dlt.KeepAllFiles())]
        d = self.controller.add_file(self.get_file(data="d0"))
        for i in range(1, 10):
            data = "d%d" % i
            self.controller.checkin(d, self.get_file(data=data))
            self.assertEqual(len(self.controller.files), 1)
            d = self.controller.files.all()[0]
            self.assertEqual(d.file.read(), data)
            self.assertNotDeleted(d.previous_revision)
            self.assertEqual("d%d" % (i-1), d.previous_revision.file.read())

    def test_checkin_delete_all(self):
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.yes, dlt.DeleteAllFiles())]
        d = self.controller.add_file(self.get_file(data="d0"))
        for i in range(1, 10):
            data = "d%d" % i
            self.controller.checkin(d, self.get_file(data=data))
            d, = self.controller.files.all()
            self.assertEqual(i, d.previous_revision.revision)
            self.assertDeleted(d.previous_revision)
            self.assertFalse(d.deleted)

    def test_checkin_last_file(self):
        COUNT = 3
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.yes, dlt.KeepLastNFiles(COUNT))]
        d = self.controller.add_file(self.get_file(data="d0"))
        for i in range(1, 10):
            self.controller.checkin(d, self.get_file(data="d%d" % i))
            d, = self.controller.files.all()
        doc_files = list(d.older_files.order_by("revision"))
        for df in doc_files[:-COUNT]:
            self.assertDeleted(df)
        for df in doc_files[-COUNT+1:]:
            self.assertNotDeleted(df)
        self.assertEqual(COUNT, models.DocumentFile.objects.filter(document=d.document, deleted=False).count())

    def test_checkin_modulo(self):
        N = 3
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.yes, dlt.Modulo(N))]
        d = self.controller.add_file(self.get_file(data="d0"))
        for i in range(1, 10):
            self.controller.checkin(d, self.get_file(data="d%d" % i))
            d, = self.controller.files.all()
        for df in d.older_files.all():
            if df.revision % N == 1:
                self.assertNotDeleted(df)
            else:
                self.assertDeleted(df)

    def test_checkin_younger(self):
        delta = datetime.timedelta(weeks=4)
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.yes, dlt.YoungerThan(delta))]
        d = self.controller.add_file(self.get_file(data="d0"))
        self.controller.checkin(d, self.get_file(data="plop"))
        d, = self.controller.files.all()
        self.assertDeleted(d.previous_revision)
        d.ctime = d.ctime - 2 * delta
        d.save()
        self.controller.checkin(d, self.get_file(data="spam"))
        d, = self.controller.files.all()
        self.assertNotDeleted(d.previous_revision)

    def test_checkin_maxsize_oldest(self):
        # start to delete oldest revisions
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.yes, dlt.MaximumTotalSize(20))]
        d = self.controller.add_file(self.get_file(data="d"))
        self.controller.checkin(d, self.get_file(data="p" *18))
        # total size : 19 bytes
        d, = self.controller.files.all()
        self.assertNotDeleted(d.previous_revision)
        self.controller.checkin(d, self.get_file(data="sp"))
        d, = self.controller.files.all()
        self.assertNotDeleted(d.previous_revision)
        self.assertDeleted(d.previous_revision.previous_revision)

    def test_checkin_max_per_date(self):
        # max: 2 per day
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.yes, dlt.MaxPerDate("day", 2))]
        d = self.controller.add_file(self.get_file(data="d"))
        self.controller.checkin(d, self.get_file(data="p" *18))
        d, = self.controller.files.all()
        self.assertNotDeleted(d.previous_revision)
        self.controller.checkin(d, self.get_file(data="p" *18))
        d, = self.controller.files.all()
        # 1st revision: kept
        # 2nd revision: deleted
        self.assertDeleted(d.previous_revision)
        self.assertNotDeleted(d.previous_revision.previous_revision)
        # max: 3 per day
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.yes, dlt.MaxPerDate("day", 3))]
        self.controller.checkin(d, self.get_file(data="p" *18))
        d, = self.controller.files.all()
        self.assertNotDeleted(d.previous_revision)
        self.assertEqual(2, d.older_files.filter(deleted=False).count())
        # add another one
        self.controller.checkin(d, self.get_file(data="p" *18))
        d, = self.controller.files.all()
        # 1st revision: kept
        # 2nd revision: deleted
        # 3nd revision: kept
        # 4th revision: deleted
        self.assertNotDeleted(d.older_files.get(revision=1))
        self.assertDeleted(d.older_files.get(revision=2))
        self.assertNotDeleted(d.older_files.get(revision=3))
        self.assertDeleted(d.older_files.get(revision=4))

    def test_checkin_maxsize_biggest(self):
        # start testing biggest revisions 
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.yes, dlt.MaximumTotalSize(20, "-size"))]
        d = self.controller.add_file(self.get_file(data="d"))
        self.controller.checkin(d, self.get_file(data="p" *18))
        d = self.controller.files.get(id=d.id)
        self.controller.checkin(d, self.get_file(data="sp"))
        d = self.controller.files.get(id=d.id)
        self.assertDeleted(d.previous_revision)
        self.assertNotDeleted(d.previous_revision.previous_revision)

    def test_patterns(self):
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.pattern("*.txt"), dlt.KeepAllFiles()),
                (dlt.yes, dlt.DeleteAllFiles())]
        d = self.controller.add_file(self.get_file("x.test"))
        self.controller.checkin(d, self.get_file("x.test"))
        d = self.controller.files.get(id=d.id)
        self.assertDeleted(d.previous_revision)
        # txt file
        d = self.controller.add_file(self.get_file("x.txt"))
        self.controller.checkin(d, self.get_file("x.txt"))
        d = self.controller.files.get(id=d.id)
        self.assertNotDeleted(d.previous_revision)

    def test_delete_delete_all(self):
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.yes, dlt.KeepAllFiles())]
        dlt.ON_DELETE_SELECTORS[:] = [(dlt.yes, dlt.DeleteAllFiles(True))]
        d = self.controller.add_file(self.get_file("x.test"))
        self.controller.checkin(d, self.get_file("x.test"))
        d = self.controller.files.get(id=d.id)
        self.controller.delete_file(d)
        d = self.controller.deprecated_files.get(id=d.id)
        self.assertDeleted(d)
        self.assertDeleted(d.previous_revision)

    def test_delete_keep_all(self):
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.yes, dlt.KeepAllFiles())]
        dlt.ON_DELETE_SELECTORS[:] = [(dlt.yes, dlt.KeepAllFiles())]
        d = self.controller.add_file(self.get_file("x.test"))
        self.controller.checkin(d, self.get_file("x.test"))
        d = self.controller.files.get(id=d.id)
        self.controller.delete_file(d)
        d = self.controller.deprecated_files.get(id=d.id)
        self.assertNotDeleted(d)
        self.assertNotDeleted(d.previous_revision)

    def test_deprecate_keep_all(self):
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.yes, dlt.KeepAllFiles())]
        dlt.ON_DEPRECATE_SELECTORS[:] = [(dlt.yes, dlt.KeepAllFiles())]
        d = self.controller.add_file(self.get_file("x.test"))
        self.controller.checkin(d, self.get_file("x.test"))
        d = self.controller.files.get(id=d.id)
        self.controller._deprecate()
        d = self.controller.files.get(id=d.id)
        self.assertFalse(d.deleted)
        self.assertNotDeleted(d.previous_revision)

    def test_deprecate_delete_all(self):
        dlt.ON_CHECKIN_SELECTORS[:] = [(dlt.yes, dlt.KeepAllFiles())]
        dlt.ON_DEPRECATE_SELECTORS[:] = [(dlt.yes, dlt.DeleteAllFiles(True))]
        d = self.controller.add_file(self.get_file("x.test"))
        self.controller.checkin(d, self.get_file("x.test"))
        d = self.controller.files.get(id=d.id)
        self.controller._deprecate()
        d = self.controller.deprecated_files.get(id=d.id)
        self.assertDeleted(d)
        self.assertDeleted(d.previous_revision)


