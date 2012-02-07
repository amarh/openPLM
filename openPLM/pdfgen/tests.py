from cStringIO import StringIO

from pyPdf import PdfFileReader

from openPLM.plmapp.tests.views import CommonViewTest


class PdfAttributesViewTestCase(CommonViewTest):

    def check_pdf(self, response, num_pages=1):
        """Reads the content of *response* as a PDF file (with pyPdf)
        and checks that it has *num_pages* page (that check can be avoid
        by setting num_pages to None).
        """
        stream = StringIO(response.content)
        pdf = PdfFileReader(stream) # fails if it is not a valid pdf
        if num_pages is not None:
            self.assertEqual(num_pages, pdf.getNumPages())

    def test_user_attributes(self):
        response = self.client.get("/pdf/user/%s/attributes/" % self.user.username)
        self.check_pdf(response)
    
    def test_group_attributes(self):
        response = self.client.get("/pdf/group/%s/attributes/" % self.group.name)
        self.check_pdf(response)
    
    def test_part_attributes(self):
        response = self.client.get("/pdf%sattributes/" % self.controller.plmobject_url)
        self.check_pdf(response)

# TODO test merged pdfs

