from openPLM.plmapp.tests.controllers import ControllerTest
import openPLM.plmapp.exceptions as exc

from .models import Page, PageController

class PageControllerTestCase(ControllerTest):

    CONTROLLER = PageController
    TYPE = "Page"
    DATA = {"page_content": u"a content"}

    def test_edit_content(self):
        ctrl = self.create("Page1")
        ctrl.edit_content("blabla")
        page = Page.objects.get(reference="Page1")
        self.assertEqual("blabla", page.page_content)

    def test_edit_content_contributor(self):
        self.create("Page1")
        user = self.get_contributor()
        page = Page.objects.get(reference="Page1")
        ctrl2 = PageController(page, user)
        content = "See You Space Cowboy"
        ctrl2.edit_content(content)
        page2 = Page.objects.get(reference="Page1")
        self.assertEqual(content, page2.page_content)

    def test_edit_content_not_in_group(self):
        self.create("Page1")
        user = self.get_contributor()
        user.groups.remove(self.group)
        page = Page.objects.get(reference="Page1")
        ctrl2 = PageController(page, user)
        content = "See You Space Cowboy"
        self.assertRaises(exc.PermissionError, ctrl2.edit_content, content)
        page2 = Page.objects.get(reference="Page1")
        self.assertEqual(self.DATA["page_content"], page2.page_content)

    def test_edit_content_not_editable(self):
        ctrl = self.create("Page1")
        ctrl.approve_promotion()
        content = "See You Space Cowboy"
        self.assertRaises(exc.PermissionError, ctrl.edit_content, content)
        page2 = Page.objects.get(reference="Page1")
        self.assertEqual(self.DATA["page_content"], page2.page_content)

    def test_add_file_error(self):
        ctrl = self.create("Page1")
        self.assertRaises(exc.AddFileError, ctrl.add_file, self.get_file())
        page = Page.objects.get(reference="Page1")
        self.assertEqual(0, page.files.count())

