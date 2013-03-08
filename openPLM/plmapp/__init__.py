from django.conf import settings

from django.contrib.comments.forms import CommentForm
from openPLM.plmapp.utils.importing import import_dotted_path

def get_form():
    widget_class = getattr(settings, "RICHTEXT_WIDGET_CLASS", None)
    if widget_class is not None:
        cls = import_dotted_path(widget_class)
        CommentForm.base_fields["comment"].widget = cls()
    return CommentForm
