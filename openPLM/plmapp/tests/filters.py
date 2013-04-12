from django.test.utils import override_settings
from django.utils.encoding import iri_to_uri
from django.utils.safestring import SafeData

from openPLM.plmapp.filters import plaintext, richtext, markdown_filter

from openPLM.plmapp.tests.base import BaseTestCase

def richtext_filter(text, object):
    """ simple filter to test settings"""
    return text.upper()

def plaintext_filter(text, object):
    """ simple filter to test settings"""
    return text.lower()

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

    @override_settings(RICHTEXT_FILTER='openPLM.plmapp.tests.filters.richtext_filter')
    def test_richtext_test(self):
        html = richtext("test", self.ctrl)
        self.assertHTMLEqual(html, "TEST")

    @override_settings(RICHTEXT_FILTER='openPLM.plmapp.tests.filters.richtext_filter',
        RICHTEXT_PLAIN_FILTER='openPLM.plmapp.tests.filters.plaintext_filter')
    def test_plaintext_test(self):
        html = plaintext("TEST", self.ctrl)
        self.assertEqual(html, "test")



class MarkDownFilterTestCase(BaseTestCase):

    def setUp(self):
        super(MarkDownFilterTestCase, self).setUp()
        self.ctrl = self.create("P1")

    def markdown(self, text, wanted):
        html = markdown_filter(text, self.ctrl)
        self.assertTrue(isinstance(html, SafeData))
        self.assertHTMLEqual(html, wanted)
        return html

    # openplm extensions

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

    def test_previous_revision(self):
        revb = self.ctrl.revise("b")
        wanted = u"<p>prev<a class='wikilink' href='%s'>&lt;&lt;</a>rev</p>" % self.ctrl.plmobject_url
        html = markdown_filter(u"prev << rev", revb)
        self.assertHTMLEqual(html, wanted)

    def test_inexisting_previous_revision(self):
        wanted = u"<p>prev<a class='wikilink' href=''>&lt;&lt;</a>rev</p>"
        self.markdown(u"prev << rev", wanted)

    def test_inexisting_next_revision(self):
        wanted = u"<p>next<a class='wikilink' href=''>&gt;&gt;</a>rev</p>"
        self.markdown(u"next >> rev", wanted)

    def test_user_url(self):
        wanted = u"<p><a class='wikilink' href='/user/robert/'>@robert</a></p>"
        self.markdown("@robert", wanted)

    def test_user_url_with_space(self):
        wanted = u"<p><a class='wikilink' href='/user/robert%20baratheon/'>@robert baratheon</a></p>"
        self.markdown("@robert\\ baratheon", wanted)

    def test_group_url(self):
        wanted = u"<p><a class='wikilink' href='/group/tortuesninja/'>group:tortuesninja</a></p>"
        self.markdown("group:tortuesninja", wanted)

    def test_part_url(self):
        wanted = u"<p><a class='wikilink' href='/redirect_name/part/tortuesninja/'>part:tortuesninja</a></p>"
        self.markdown("part:tortuesninja", wanted)

    def test_part_url2(self):
        wanted = u"<p><a class='wikilink' href='/redirect_name/part/tortues%20ninja!/'>part:tortues ninja!</a></p>"
        self.markdown('part:"tortues ninja!"', wanted)

    def test_doc_url(self):
        wanted = u"<p><a class='wikilink' href='/redirect_name/doc/tortuesninja/'>doc:tortuesninja</a></p>"
        self.markdown("doc:tortuesninja", wanted)

    def test_doc_url2(self):
        wanted = u"<p><a class='wikilink' href='/redirect_name/doc/tortues%20ninja!/'>doc:tortues ninja!</a></p>"
        self.markdown('doc:"tortues ninja!"', wanted)

    # builtin syntax

    def test_emph(self):
        self.markdown(SIMPLE_TEXT,  u"<p><em>a</em> simple text</p>")

    def test_title(self):
        wanted = u"<h1 id='plm-hello'>Hello</h1><p>world</p>"
        self.markdown(u"# Hello #\n\nworld", wanted)

    def test_link(self):
        wanted = u"<p><a href='http://example.com'>http://example.com</a></p>"
        self.markdown(u"<http://example.com>", wanted)

    def test_link2(self):
        wanted = u"<p><a href='http://example.com'>hello</a></p>"
        self.markdown(u"[hello](http://example.com)", wanted)

    def test_safe_link(self):
        wanted = u"<p><a href=''>c</a></p>"
        self.markdown(u"[c](javascript:plop)", wanted)

