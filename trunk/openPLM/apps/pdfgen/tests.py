import warnings
from StringIO import StringIO

from pyPdf import PdfFileReader

from openPLM.plmapp.controllers import DocumentController, PartController
from openPLM.plmapp.tests.views import CommonViewTest

from openPLM.apps.pdfgen.views import download_merged_pdf

PDF = """%PDF-1.1

1 0 obj
  << /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
  << /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 300 144] >>
endobj

3 0 obj
  <<  /Type /Page
      /Parent 2 0 R /Resources
       << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Times-Roman >>
           >>
       >>
      /Contents [
        << /Length 105 >>
        stream
          BT
            /F1 18 Tf
            0 0 Td
            (Hello world.) Tj
          ET
        endstream ]
  >>
endobj

xref
0 4
0000000000 65535 f@
0000000010 00000 n@
0000000062 00000 n@
0000000146 00000 n@
trailer
  <<  /Root 1 0 R /Size 4 >>
startxref
496
%%EOF""".replace("@", " ")
# XREF table lines must end with a space, replaced by a @ to avoid
# that an editor removes trailing spaces and breaks the pdf

class PdfTestCase(CommonViewTest):

    def check_pdf(self, response, num_pages=1):
        """Reads the content of *response* as a PDF file (with pyPdf)
        and checks that it has *num_pages* page (that check can be avoid
        by setting num_pages to None).
        """
        if response.streaming:
            content = "".join(response.streaming_content)
        else:
            content = response.content
        stream = StringIO(content)
        warnings.simplefilter('ignore', DeprecationWarning)
        pdf = PdfFileReader(stream) # fails if it is not a valid pdf
        if num_pages is not None:
            self.assertEqual(num_pages, pdf.getNumPages())
        warnings.simplefilter('default', DeprecationWarning)
        return content


class PdfAttributesViewTestCase(PdfTestCase):

    def test_user_attributes(self):
        response = self.client.get("/pdf/user/%s/attributes/" % self.user.username)
        self.check_pdf(response)

    def test_group_attributes(self):
        response = self.client.get("/pdf/group/%s/attributes/" % self.group.name)
        self.check_pdf(response)

    def test_part_attributes(self):
        response = self.client.get("/pdf%sattributes/" % self.controller.plmobject_url)
        self.check_pdf(response)


class PdfMergeTestCase(PdfTestCase):

    def setUp(self):
        super(PdfMergeTestCase, self).setUp()
        self.doc = DocumentController.create("Doc1", "Document", "q",
                self.user, self.DATA, True, True)
        self.doc_url = self.doc.plmobject_url

    def test_download_merged_pdf(self):
        for i in range(4):
            response = download_merged_pdf(self.doc, self.doc.files)
            content = self.check_pdf(response, i + 1)
            self.doc.add_file(self.get_file("hello%d.pdf" % i, data=PDF))
            self.assertEqual(i, content.count("world"))

    def test_select_pdf_empty_document_html(self):
        response = self.get(self.doc_url + "pdf/")
        formset = response.context["pdf_formset"]
        self.assertEqual(0, formset.total_form_count())

    def test_select_pdf_empty_document_pdf(self):
        data = {
                "Download" : "download",
                'documentfile_set-TOTAL_FORMS': "0",
                'documentfile_set-INITIAL_FORMS': "0",
                }
        response = self.client.get(self.doc_url + "pdf/", data=data)
        self.check_pdf(response, 1)

    def test_select_pdf_one_pdf_document_html(self):
        df = self.doc.add_file(self.get_file("hello.pdf", data=PDF))
        response = self.get(self.doc_url + "pdf/")
        formset = response.context["pdf_formset"]
        self.assertEqual(1, formset.total_form_count())
        form = formset.forms[0]
        self.assertTrue(form.fields["selected"].initial)
        self.assertEqual(form.instance, df)

    def test_select_pdf_one_pdf_document_pdf(self):
        df = self.doc.add_file(self.get_file("hello.pdf", data=PDF))
        data = {
                "Download" : "download",
                'documentfile_set-TOTAL_FORMS': '1',
                'documentfile_set-INITIAL_FORMS': '1',
                'documentfile_set-0-id' : df.id,
                'documentfile_set-0-document' : self.doc.id,
                'documentfile_set-0-selected' : 'on',
                }
        response = self.client.get(self.doc_url + "pdf/", data=data)
        content = self.check_pdf(response, 2)
        self.assertTrue("world" in content)

    def test_select_pdf_one_unselected_pdf_document_pdf(self):
        df = self.doc.add_file(self.get_file("hello.pdf", data=PDF))
        data = {
                "Download" : "download",
                'documentfile_set-TOTAL_FORMS': '1',
                'documentfile_set-INITIAL_FORMS': '1',
                'documentfile_set-0-id' : df.id,
                'documentfile_set-0-document' : self.doc.id,
                'documentfile_set-0-selected' : '',
                }
        response = self.client.get(self.doc_url + "pdf/", data=data)
        content = self.check_pdf(response, 1)
        self.assertFalse("world" in content)

    def test_select_pdf_two_pdf_document_html(self):
        df1 = self.doc.add_file(self.get_file("hello1.pdf", data=PDF))
        df2 = self.doc.add_file(self.get_file("hello2.pdf", data=PDF))
        response = self.get(self.doc_url + "pdf/")
        formset = response.context["pdf_formset"]
        self.assertEqual(2, formset.total_form_count())
        for form in formset.forms:
            self.assertTrue(form.fields["selected"].initial)
            self.assertTrue(form.instance in (df1, df2))

    def test_select_pdf_two_pdf_document_pdf(self):
        df1 = self.doc.add_file(self.get_file("hello1.pdf",
            data=PDF.replace("world", "worl1")))
        df2 = self.doc.add_file(self.get_file("hello2.pdf",
            data=PDF.replace("world", "worl2")))
        data = {
                "Download" : "download",
                'documentfile_set-TOTAL_FORMS': '2',
                'documentfile_set-INITIAL_FORMS': '1',
                'documentfile_set-0-id' : df1.id,
                'documentfile_set-0-document' : self.doc.id,
                'documentfile_set-0-selected' : 'on',
                'documentfile_set-1-id' : df2.id,
                'documentfile_set-1-document' : self.doc.id,
                'documentfile_set-1-selected' : '',
                }
        response = self.client.get(self.doc_url + "pdf/", data=data)
        content = self.check_pdf(response, 2)
        self.assertTrue("worl1" in content)
        self.assertFalse("worl2" in content)

    def test_select_pdf_one_pdf_part_html(self):
        df = self.doc.add_file(self.get_file("hello.pdf", data=PDF))
        self.controller.attach_to_document(self.doc)
        response = self.get(self.base_url + "pdf/")
        formset = response.context["children"][0][1].formsets[0]
        self.assertEqual(1, formset.total_form_count())
        form = formset.forms[0]
        prefix = "pdf_self_%d-0" % self.doc.id
        self.assertEqual(form.prefix, prefix)
        self.assertTrue(form.fields["selected"].initial)
        self.assertEqual(form.instance, df)

    def test_select_pdf_one_pdf_part_pdf(self):
        df = self.doc.add_file(self.get_file("hello.pdf", data=PDF))
        self.controller.attach_to_document(self.doc)
        prefix = "pdf_self_%d" % self.doc.id
        data = {
                "Download" : "download",
                prefix + '-TOTAL_FORMS': '1',
                prefix + '-INITIAL_FORMS': '1',
                prefix + '-0-id' : df.id,
                prefix + '-0-document' : self.doc.id,
                prefix + '-0-selected' : 'on',
                }
        response = self.client.get(self.base_url + "pdf/", data=data)
        content = self.check_pdf(response, 2)
        self.assertTrue("world" in content)

    def test_select_pdf_chidlren_part_pdf(self):
        child = PartController.create("Child", "Part", "f",
                self.user, self.DATA, True, True)
        self.doc.attach_to_part(child)
        self.controller.add_child(child, 1, 1, 'm')
        df = self.doc.add_file(self.get_file("hello.pdf", data=PDF))
        prefix = "pdf_%d_%d" % (self.controller.get_children()[0].link.id,
                self.doc.id)
        data = {
                "Download" : "download",
                prefix + '-TOTAL_FORMS': '1',
                prefix + '-INITIAL_FORMS': '1',
                prefix + '-0-id' : df.id,
                prefix + '-0-document' : self.doc.id,
                prefix + '-0-selected' : 'on',
                }
        response = self.client.get(self.base_url + "pdf/", data=data)
        content = self.check_pdf(response, 2)
        self.assertTrue("world" in content)

