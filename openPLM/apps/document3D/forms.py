from django import forms
from openPLM.apps.document3D.models import *
from openPLM.plmapp.models import get_all_parts_with_level
from openPLM.plmapp.units import UNITS
            
class Doc_Part_type_Form(forms.Form):
    LIST_parts = get_all_parts_with_level()
    type_part = forms.TypedChoiceField(choices=LIST_parts,
            label='', initial="Part")
    #deep = forms.IntegerField(label='')
    #deep.widget.attrs["style"] = 'display:none;'    
class Form_save_time_last_modification(forms.Form):

    last_modif_time = forms.DateTimeField()
    last_modif_time.widget.attrs["style"] = 'display:none;'
    last_modif_microseconds = forms.FloatField() 
    last_modif_microseconds.widget.attrs["style"] = 'display:none;'
    
class Order_Quantity_Form(forms.Form):

    order = forms.IntegerField(widget=forms.TextInput(attrs={'size':'2'}))
    quantity = forms.FloatField(widget=forms.TextInput(attrs={'size':'4'}))
    unit = forms.ChoiceField(choices=UNITS, initial=DEFAULT_UNIT)

