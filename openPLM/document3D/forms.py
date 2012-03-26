from django import forms
from openPLM.document3D.models import *
from django.db.models import Q
from django.db import models
from openPLM.plmapp.models import get_all_parts_with_level
from openPLM.plmapp.forms import group_types
from django.forms.formsets import formset_factory
from openPLM.plmapp.units import UNITS
            
class Doc_Part_type_Form(forms.Form):
    LIST_parts = group_types(get_all_parts_with_level())
    type_part = forms.TypedChoiceField(choices=LIST_parts,label='')
    type_part.widget.attrs["onchange"]="update_form(this,'doc_show')"
    type_part.widget.attrs["class"]="selector"
    #type_part.widget.attrs["onchange"]="this.options[this.selectedIndex].selected"

      
    LIST_document3D = group_types(get_all_plmDocument3Dtypes_with_level())  
    type_document3D = forms.TypedChoiceField(choices=LIST_document3D,label='')
    type_part.widget.attrs["onchange"]="update_form(this,'part_show')"
    
class Form_save_time_last_modification(forms.Form):

    last_modif_time = forms.DateTimeField(label='') 
    last_modif_time.widget.attrs["style"]='display:none'   
    last_modif_microseconds = forms.FloatField(label='') 
    last_modif_microseconds.widget.attrs["style"]='display:none'   
    
class Order_Quantity_Form(forms.Form):

    order = forms.IntegerField(widget=forms.TextInput(attrs={'size':'2'}))
    quantity = forms.FloatField(widget=forms.TextInput(attrs={'size':'4'}))
    unit = forms.ChoiceField(choices=UNITS, initial=DEFAULT_UNIT)

