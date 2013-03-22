from django import forms

from openPLM.plmapp.forms import enhance_fields
from .models import Page


class PageForm(forms.Form):
    page_content = forms.CharField(widget=forms.Textarea())

enhance_fields(PageForm, Page)
