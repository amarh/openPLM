from django import forms

from openPLM.apps.oerp.models import PartCost

class CostForm(forms.ModelForm):

    class Meta:
        model = PartCost
        widgets = {
            'part' : forms.HiddenInput(),
        }

def get_cost_form(part, request_data=None):
    try:
        pc = PartCost.objects.get(part=part)
        return CostForm(request_data, instance=pc)
    except PartCost.DoesNotExist:
        return CostForm(request_data, initial={"part":part})

