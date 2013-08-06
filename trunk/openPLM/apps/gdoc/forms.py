

from django import forms
from openPLM.plmapp.forms import get_creation_form

from openPLM.apps.gdoc.models import GoogleDocument

from openPLM.apps.gdoc.gutils import get_gdocs

def clean_gdoc(self):
    cleaned_data = self.cleaned_data
    cleaned_data["name"] = self.gdocs[cleaned_data["resource_id"]]
    return cleaned_data

def get_gdoc_creation_form(user, client, data=None, start=0):
    form = get_creation_form(user, GoogleDocument, data, start)
    gdocs = get_gdocs(client)
    form.gdocs = dict(gdocs)
    form.fields["resource_id"] = forms.ChoiceField(choices=gdocs,
            required=True)
    del form.fields.keyOrder[-1]
    form.fields.keyOrder.insert(0, "resource_id")
    old_clean = form.clean
    form.clean = lambda: old_clean() and clean_gdoc(form)
    return form
