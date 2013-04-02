from openPLM.plmapp.tests.controllers import ControllerTest
from openPLM.plmapp.tests.views import CommonViewTest
import openPLM.plmapp.exceptions as exc
from openPLM.plmapp.widgets import MarkdownWidget

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


class PageViewTestCase(CommonViewTest):

    CONTROLLER = PageController
    TYPE = "Page"
    DATA = {"page_content": u"a content"}

    def test_page_view(self):
        response = self.get(self.base_url + "page/", page="page")
        self.assertContains(response, self.DATA["page_content"])
        self.assertTemplateUsed(response, "richpage/page.html")
        # edit link
        self.assertContains(response, "edit_content/")
        self.controller.approve_promotion()
        response = self.get(self.base_url + "page/", page="page")
        self.assertContains(response, self.DATA["page_content"])
        self.assertNotContains(response, "edit_content/")
        self.assertTemplateUsed(response, "richpage/page.html")

    def test_redirect_base_to_page(self):
        response = self.get(self.base_url, follow=False, status_code=301)
        self.assertRedirects(response, self.base_url + "page/", 301)

    def test_edit_content_get(self):
        response = self.get(self.base_url + "edit_content/", page="page")
        form = response.context["form"]
        self.assertEqual(self.controller.page_content, form.initial["page_content"])
        self.assertTemplateUsed(response, "richpage/edit_content.html")
        media = MarkdownWidget().media.render()
        self.assertEqual(form.media.render(), media)

    def test_edit_content_post(self):
        content = "hello pinkie"
        response = self.post(self.base_url + "edit_content/", {"page_content": content})
        page = Page.objects.get(id=self.controller.id)
        self.assertEqual(content, page.page_content)
        self.assertRedirects(response, self.base_url + "page/")
        self.assertContains(response, content)
        self.assertTemplateUsed(response, "richpage/page.html")

    def test_richtext(self):
        self.controller.edit_content(u"# Hello #\n\nworld")
        response = self.get(self.base_url + "page/", page="page")
        wanted = u"<div class='richtext'><h1 id='plm-hello'>Hello</h1><p>world</p></div>"
        self.assertContains(response, wanted, html=True)

