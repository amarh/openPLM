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
    from markdown.extensions.wikilinks import WikiLinkExtension, WikiLinks
except ImportError:
    pass
else:
    ref = r'(?:\\ |[^/?#\t\r\v\f\s])+'
    object_pattern = r'(\w+/{ref}/{ref})'.format(ref=ref)
    class PLMLinkExtension(WikiLinkExtension):
        def __init__(self, pattern, configs):
            WikiLinkExtension.__init__(self, configs)
            self.pattern = pattern

        def extendMarkdown(self, md, md_globals):
            self.md = md

            # append to end of inline patterns
            wikilinkPattern = WikiLinks(self.pattern, self.getConfigs())
            wikilinkPattern.md = md
            md.inlinePatterns.add('plmlink%d' % hash(self.pattern),
                wikilinkPattern, "<not_strong")

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
                PLMLinkExtension(r"^@(%s)" % ref, [('base_url', '/user/'),]),
                # groups
                PLMLinkExtension(r"\bgroup:(%s)\b" % ref, [('base_url', '/group/'),]),
                # previous/next revisions
                PLMLinkExtension(r"(?<!\w)(\<\<)(?!\w)", [('build_url', previous_revision)]),
                PLMLinkExtension(r"(?<!\w)(\>\>)(?!\w)", [('build_url', next_revision)]),

            ],
        )
        return mark_safe(md)


