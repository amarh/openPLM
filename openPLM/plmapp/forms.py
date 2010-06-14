from django import forms
from django.forms.models import modelform_factory

import openPLM.plmapp.models as m


def get_creation_form(cls=m.PLMObject, initial=None):
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
    Form = modelform_factory(cls, fields=fields, exclude=('type',)) 
    if initial:
        return Form(initial)
    else:
        return Form()


def get_modification_form(cls=m.PLMObject, initial=None, instance=None):
    fields = cls.get_modification_fields()
    Form = modelform_factory(cls, fields=fields)
    if initial:
        return Form(initial)
    elif instance:
        return Form(instance=instance)
    else:
        return Form()

class TypeChoiceForm(forms.Form):
    DICT = m.get_all_plmobjects()
    TYPES = [(v, v) for v in DICT]
    
    type = forms.TypedChoiceField(choices=TYPES, coerce=DICT.get)

