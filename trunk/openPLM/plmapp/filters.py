from django.conf import settings
from django.utils.html import strip_tags, linebreaks
from django.utils.safestring import mark_safe
from openPLM.plmapp.utils.importing import import_dotted_path

def richtext(content):
    """
    This template filter takes a string value and passes it through the
    function specified by the RICHTEXT_FILTER setting.
    """
    richtext_filter = getattr(settings, "RICHTEXT_FILTER", None)
    if richtext_filter:
        func = import_dotted_path(richtext_filter)
    else:
        func = lambda s: mark_safe(linebreaks(s, True))
    return func(content)


def plaintext(content):
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
        func = lambda s: strip_tags(f(s))
    else:
        func = lambda s: s
    return func(content)


try:
    import markdown
except ImportError:
    pass
else:
    def markdown_filter(text):
        md = markdown.markdown(text,
            safe_mode='escape',
            output_format='html5',
            extensions=["abbr", "tables", "def_list", "smart_strong", "toc",]
        )
        return mark_safe(md)


