

from django import forms
from openPLM.plmapp.forms import get_creation_form

from openPLM.gdoc.models import GoogleDocument

from openPLM.gdoc.gutils import get_gdocs

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
    form.clean = lambda:clean_gdoc(form)
    return form
