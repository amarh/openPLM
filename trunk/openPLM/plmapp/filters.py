import re, htmlentitydefs

from django.conf import settings
from django.utils.html import strip_tags, linebreaks
from django.utils.safestring import mark_safe
from openPLM.plmapp.utils.importing import import_dotted_path

## http://effbot.org/zone/re-sub.htm#unescape-html
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)


def richtext(content, object):
    """
    This template filter takes a string value and passes it through the
    function specified by the RICHTEXT_FILTER setting.
    """
    richtext_filter = getattr(settings, "RICHTEXT_FILTER", None)
    if richtext_filter:
        func = import_dotted_path(richtext_filter)
    else:
        func = lambda s, o: mark_safe(linebreaks(s, True))
    return func(content, object)


def plaintext(content, object):
    """
    This template filter takes a string value and passes it through the
    function specified by the RICHTEXT_PLAIN_FILTER setting.
    """
    richtext_filter = getattr(settings, "RICHTEXT_FILTER", None)
    richtext_plain_filter = getattr(settings, "RICHTEXT_PLAIN_FILTER", None)
    if richtext_plain_filter:
        func = import_dotted_path(richtext_plain_filter)
    elif richtext_filter:
        f = import_dotted_path(richtext_filter)
        func = lambda s, o: unescape(strip_tags(f(s, o)))
    else:
        func = lambda s, o: s
    return func(content, object)

try:
    import markdown
    from markdown.inlinepatterns import LinkPattern
    from markdown.util import etree
    from markdown.extensions import Extension
    from markdown.extensions.headerid import slugify
    from django.utils.encoding import iri_to_uri
except ImportError:
    pass
else:
    ref = r'(?:\\ |[^/?#\t\r\v\f\s])+'
    object_pattern = r'(\w+/{ref}/{ref})'.format(ref=ref)
    def build_url(label, base, end):
        return iri_to_uri('%s%s%s' % (base, label, end))

    def prefixed_slugify(*args, **kwargs):
        return "plm-" + slugify(*args, **kwargs)

    class PLMLinkExtension(Extension):
        def __init__(self, pattern, configs):
            # set extension defaults
            self.config = {
                            'base_url' : ['/', 'String to append to beginning or URL.'],
                            'end_url' : ['/', 'String to append to end of URL.'],
                            'html_class' : ['wikilink', 'CSS hook. Leave blank for none.'],
                            'build_url' : [build_url, 'Callable formats URL from label.'],
                            'base_label' : ['', 'String to prepend to the label'],
                            'end_label' : ['', 'String to append to the label'],
            }

            # Override defaults with user settings
            for key, value in configs :
                self.setConfig(key, value)
            self.pattern = pattern

        def extendMarkdown(self, md, md_globals):
            self.md = md

            # append to end of inline patterns
            pattern = PLMPattern(self.pattern, self.getConfigs())
            pattern.markdown = md
            md.inlinePatterns.add('plmlink%d' % hash(self.pattern), pattern,
                "<not_strong")

    class PLMPattern(LinkPattern):
        def __init__(self, pattern, config):
            LinkPattern.__init__(self, pattern)
            self.config = config

        def handleMatch(self, m):
            if m.group(2).strip():
                base_url = self.config['base_url']
                end_url = self.config['end_url']
                html_class = self.config['html_class']
                label = self.unescape(m.group(2).strip())
                label = label.replace("\\ ", " ")
                url = self.config['build_url'](label, base_url, end_url)
                a = etree.Element('a')
                a.text = u'%s%s%s' % (self.config['base_label'],  label, self.config['end_label'])
                a.set('href', self.unescape(url))
                if html_class:
                    a.set('class', html_class)
            else:
                a = ''
            return a

    def markdown_filter(text, object):
        # TODO: optimize this code
        def previous_revision(label, base, end):
            try:
                return object.get_previous_revisions()[-1].plmobject_url
            except Exception:
                return ""
        def next_revision(label, base, end):
            try:
                return object.get_next_revisions()[0].plmobject_url
            except Exception:
                return ""

        md = markdown.markdown(text,
            safe_mode='escape',
            output_format='html5',
            extensions=["abbr", "tables", "def_list", "smart_strong", "toc",
                "headerid", "fenced_code", "sane_lists", "footnotes",
                # objects
                PLMLinkExtension(r"\[%s\]" % object_pattern, [('base_url', '/object/')]),
                PLMLinkExtension(r"\bpart:(\w+)", [('base_url', '/redirect_name/part/'),
                    ('base_label', 'part:')]),
                PLMLinkExtension(r'\bpart:"([^"]+)"', [('base_url', '/redirect_name/part/'),
                    ('base_label', 'part:')]),
                PLMLinkExtension(r"\bdoc:(\w+)", [('base_url', '/redirect_name/doc/'),
                    ('base_label', 'doc:')]),
                PLMLinkExtension(r'\bdoc:"([^"]+)"', [('base_url', '/redirect_name/doc/'),
                    ('base_label', 'doc:')]),
                # users
                PLMLinkExtension(r"(?<!\w)@(%s)" % ref, [('base_url', '/user/'),
                    ('base_label', '@')]),
                # groups
                PLMLinkExtension(r"\bgroup:(%s)\b" % ref, [('base_url', '/group/'),
                    ('base_label', 'group:')]),
                # previous/next revisions
                PLMLinkExtension(r"(?<!\w)(\<\<)(?!\w)", [('build_url', previous_revision)]),
                PLMLinkExtension(r"(?<!\w)(\>\>)(?!\w)", [('build_url', next_revision)]),

            ],
            extension_configs={
                'headerid': [('slugify', prefixed_slugify), ],
            }
        )
        return mark_safe(md)


