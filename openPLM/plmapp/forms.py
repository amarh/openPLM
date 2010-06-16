from django import forms
from django.forms.models import modelform_factory

import openPLM.plmapp.models as m


def get_creation_form(cls=m.PLMObject, data=None, empty_allowed=False):
    u"""
    Returns a creation form suitable to creates an object
    of type *cls*.

    The returned form can be used, if it is valid, with the function
    :meth:`~plmapp.controllers.PLMObjectController.create_from_form`
    to create a :class:`~plmapp.models.PLMObject` and his associated
    :class:`~plmapp.controllers.PLMObjectController`.

    If *initial* is provided, it will be used to fill the form.
    """

    fields = cls.get_creation_fields()
    Form = modelform_factory(cls, fields=fields, exclude=('type', 'state')) 
    if data:
        return Form(data=data, empty_permitted=empty_allowed)
    else:
        return Form()
        
def get_modification_form(cls=m.PLMObject, data=None, instance=None):
    fields = cls.get_modification_fields()
    Form = modelform_factory(cls, fields=fields)
    if data:
        return Form(data)
    elif instance:
        return Form(instance=instance)
    else:
        return Form()

class TypeChoiceForm(forms.Form):
    DICT = m.get_all_plmobjects()
    TYPES = [(v, v) for v in DICT]
    type = forms.TypedChoiceField(choices=TYPES)

class ChoiceForm(forms.Form):
    DICT = m.get_all_plmobjects()
    TYPES = [(v, v) for v in DICT]
    type = forms.TypedChoiceField(choices=TYPES, required=False)
    reference = forms.CharField(widget=forms.TextInput(), required=False)
    revision = forms.CharField(widget=forms.TextInput(), required=False)

class AddChildForm(forms.Form):
    child = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   empty_label=None)
    quantity = forms.IntegerField(initial=1)
    order = forms.IntegerField(initial=1)
