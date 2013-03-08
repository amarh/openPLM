from django.test.utils import override_settings
from django.utils.encoding import iri_to_uri
from django.utils.safestring import SafeData

from openPLM.plmapp.filters import plaintext, richtext, markdown_filter

from openPLM.plmapp.tests.base import BaseTestCase

SIMPLE_TEXT =  u"_a_ simple text"
class RichTextTestCase(BaseTestCase):

    def setUp(self):
        super(RichTextTestCase, self).setUp()
        self.ctrl = self.create("P1")

    def test_richtext_default_settings(self):
        html = richtext(SIMPLE_TEXT, self.ctrl)
        self.assertHTMLEqual(html, u"<p><em>a</em> simple text</p>")
        self.assertTrue(isinstance(html, SafeData))

    def test_plaintext_default_settings(self):
        html = plaintext(SIMPLE_TEXT, self.ctrl)
        self.assertEqual(html, u"a simple text")
        self.assertFalse(isinstance(html, SafeData))

    @override_settings(RICHTEXT_FILTER=None)
    def test_richtext_disabled(self):
        html = richtext(SIMPLE_TEXT, self.ctrl)
        self.assertHTMLEqual(html, u"<p>%s</p>" % SIMPLE_TEXT)
        self.assertTrue(isinstance(html, SafeData))

    @override_settings(RICHTEXT_FILTER=None, RICHTEXT_PLAIN_FILTER=None)
    def test_plaintext_disabled(self):
        html = plaintext(SIMPLE_TEXT, self.ctrl)
        self.assertEqual(html, SIMPLE_TEXT)
        self.assertFalse(isinstance(html, SafeData))


class MarkDownFilterTestCase(BaseTestCase):

    def setUp(self):
        super(MarkDownFilterTestCase, self).setUp()
        self.ctrl = self.create("P1")

    def markdown(self, text, wanted):
        html = markdown_filter(text, self.ctrl)
        self.assertTrue(isinstance(html, SafeData))
        self.assertHTMLEqual(html, wanted)
        return html

    def test_emph(self):
        self.markdown(SIMPLE_TEXT,  u"<p><em>a</em> simple text</p>")

    def test_object_url(self):
        wanted = u"<p><a class='wikilink' href='%s'>Part/P1/a</a></p>" % self.ctrl.plmobject_url
        self.markdown(u"[Part/P1/a]", wanted)

    def test_object_url_with_space(self):
        url = "/object/Part/P1%20a/a/"
        wanted = u"<p><a class='wikilink' href='%s'>Part/P1 a/a</a></p>" % url
        self.markdown(u"[Part/P1\\ a/a]", wanted)

    def test_object_url_special_character(self):
        url = iri_to_uri(u"/object/Part/P1/\xe0\u0153/")
        wanted = u"<p><a class='wikilink' href='%s'>Part/P1/\xe0\u0153</a></p>" % url
        self.markdown(u"[Part/P1/\xe0\u0153]", wanted)

    def test_next_revision(self):
        revb = self.ctrl.revise("b")
        wanted = u"<p>next<a class='wikilink' href='%s'>&gt;&gt;</a>rev</p>" % revb.plmobject_url
        self.markdown(u"next >> rev", wanted)

    def test_user_url(self):
        wanted = u"<p><a class='wikilink' href='/user/robert/'>robert</a></p>"
        self.markdown("@robert", wanted)

    def test_user_url_with_space(self):
        wanted = u"<p><a class='wikilink' href='/user/robert%20baratheon/'>robert baratheon</a></p>"
        self.markdown("@robert\\ baratheon", wanted)

    def test_group_url(self):
        wanted = u"<p><a class='wikilink' href='/group/tortuesninja/'>tortuesninja</a></p>"
        self.markdown("group:tortuesninja", wanted)

