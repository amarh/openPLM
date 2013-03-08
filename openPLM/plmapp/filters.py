from django.conf import settings
from django.utils.html import strip_tags, linebreaks
from django.utils.safestring import mark_safe
from openPLM.plmapp.utils.importing import import_dotted_path

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
        func = lambda s, o: strip_tags(f(s, o))
    else:
        func = lambda s, o: s
    return func(content, object)

try:
    import markdown
    from markdown.inlinepatterns import LinkPattern
    from markdown.util import etree
    from markdown.extensions.wikilinks import WikiLinkExtension
    from django.utils.encoding import iri_to_uri
except ImportError:
    pass
else:
    ref = r'(?:\\ |[^/?#\t\r\v\f\s])+'
    object_pattern = r'(\w+/{ref}/{ref})'.format(ref=ref)
    def build_url2(label, base, end):
        return iri_to_uri('%s%s%s' % (base, label, end))

    class PLMLinkExtension(WikiLinkExtension):
        def __init__(self, pattern, configs):
            if "build_url" not in [c[0] for c in configs]:
                configs.append(("build_url", build_url2))
            WikiLinkExtension.__init__(self, configs)
            self.pattern = pattern

        def extendMarkdown(self, md, md_globals):
            self.md = md

            # append to end of inline patterns
            wikilinkPattern = PLMPattern(self.pattern, self.getConfigs())
            wikilinkPattern.markdown = md
            md.inlinePatterns.add('plmlink%d' % hash(self.pattern),
                wikilinkPattern, "<not_strong")

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
                label = label.replace("\ ", " ")
                url = self.config['build_url'](label, base_url, end_url)
                a = etree.Element('a')
                a.text = label.replace("\\ ", " ")
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
                return object.get_previous_revisions()[0].plmobject_url
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
                # objects
                PLMLinkExtension(r"\[%s\]" % object_pattern, [('base_url', '/object/'),]),
                # users
                PLMLinkExtension(r"(?<!\w)@(%s)" % ref, [('base_url', '/user/'),]),
                # groups
                PLMLinkExtension(r"\bgroup:(%s)\b" % ref, [('base_url', '/group/'),]),
                # previous/next revisions
                PLMLinkExtension(r"(?<!\w)(\<\<)(?!\w)", [('build_url', previous_revision)]),
                PLMLinkExtension(r"(?<!\w)(\>\>)(?!\w)", [('build_url', next_revision)]),

            ],
        )
        return mark_safe(md)


