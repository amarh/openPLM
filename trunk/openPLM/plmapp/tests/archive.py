import zipfile
import tarfile
from cStringIO import StringIO

from openPLM.plmapp.tests.views import CommonViewTest
from openPLM.plmapp.controllers.document import DocumentController

class ArchiveViewTestCase(CommonViewTest):

    def setUp(self):
        super(ArchiveViewTestCase, self).setUp()
        self.document = DocumentController.create('doc1', 'Document',
                'a', self.user, self.DATA)
        self.filenames = []
        self.contents = {}
        for i in range(5):
            name = "file_%d.test" % i
            content = "content_%d" % i
            self.filenames.append(name)
            self.contents[name] = content
            self.document.add_file(self.get_file(name, content))

        # add another file named "file_4.test"
        self.filenames.append("file_4_1.test")
        self.contents["file_4_1.test"] = content
        self.document.add_file(self.get_file(name, content))

        # create another document
        self.document_bis = DocumentController.create('doc2', 'Document',
                'a', self.user, self.DATA)
        self.file_bis = "file_bis.test"
        self.document_bis.add_file(self.get_file(self.file_bis, "file_bis"))
        self.contents[self.file_bis] = "file_bis"

        self.controller.attach_to_document(self.document)
        self.controller.attach_to_document(self.document_bis)

    def get_archive(self, obj, format):
        response = self.client.get(obj.plmobject_url + "archive/",
             {"format": format})
        return StringIO("".join(response.streaming_content))

    def test_download_document_zip(self):
        f = self.get_archive(self.document, "zip")
        zf = zipfile.ZipFile(f)
        self.assertFalse(zf.testzip())
        names = sorted(zf.namelist())
        self.assertEqual(self.filenames, names)
        for name in names:
            self.assertEqual(self.contents[name], zf.open(name).read())
        zf.close()

    def test_download_document_tar(self):
        f = self.get_archive(self.document, "tar")
        tf = tarfile.open(fileobj=f)
        names = sorted(tf.getnames())
        self.assertEqual(self.filenames, names)
        for name in names:
            self.assertEqual(self.contents[name], tf.extractfile(name).read())
        tf.close()

    def test_download_part_zip(self):
        f = self.get_archive(self.controller, "zip")
        zf = zipfile.ZipFile(f)
        self.assertFalse(zf.testzip())
        names = sorted(zf.namelist())
        self.assertEqual(self.filenames + [self.file_bis], names)
        for name in names:
            self.assertEqual(self.contents[name], zf.open(name).read())
        zf.close()

    def test_download_part_tar(self):
        f = self.get_archive(self.controller, "tar")
        tf = tarfile.open(fileobj=f)
        names = sorted(tf.getnames())
        self.assertEqual(self.filenames + [self.file_bis], names)
        for name in names:
            self.assertEqual(self.contents[name], tf.extractfile(name).read())
        tf.close()

