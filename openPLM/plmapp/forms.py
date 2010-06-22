from django import forms
from django.forms.models import modelform_factory, modelformset_factory

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

def get_search_form(cls=m.PLMObject, data=None):
    fields = set(cls.get_creation_fields())
    fields.update(set(cls.get_modification_fields()))
    fields.difference_update(("revision", "type", "reference", "lifecycle"))
    fields_dict = {}
    for field in fields:
        model_field = cls._meta.get_field(field)
        form_field = model_field.formfield()
        form_field.help_text = ""
        if isinstance(form_field.widget, forms.Textarea):
            form_field.widget = forms.TextInput()
        form_field.required = False
        fields_dict[field] = form_field
    
    def search(self, query_set=None):
        if self.is_valid():
            query = {}
            for field in self.changed_data:
                if isinstance(cls._meta.get_field(field),
                              (m.models.CharField, m.models.TextField)):
                    query[field + "__icontains"] = self.cleaned_data[field]
                else:
                    query[field] = self.cleaned_data[field]
            if query_set is not None:
                return query_set.filter(**query)
            else:
                return []
    
    Form = type("Search%sForm" % cls.__name__,
                (forms.BaseForm,),
                {"base_fields" : fields_dict, "search" : search}) 
    if data is not None:
        return Form(data=data, empty_permitted=True)
    else:
        return Form(empty_permitted=True)
    
class type_form(forms.Form):
    DICT = m.get_all_plmobjects()
    TYPES = [(v, v) for v in DICT]
    type = forms.TypedChoiceField(choices=TYPES)

class attributes_form(type_form):
    reference = forms.CharField(widget=forms.TextInput(), required=False)
    revision = forms.CharField(widget=forms.TextInput(), required=False)
    
def get_attr_search_form(cls=m.PLMObject, data=None, instance=None):
    fields = cls.get_modification_fields()
    Form = modelform_factory(cls, fields=fields)
    if data:
        return Form(data)
    elif instance:
        return Form(instance=instance)
    else:
        return Form()
        
class add_child_form(forms.Form):
    child = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   empty_label=None)
    quantity = forms.FloatField(initial=1)
    order = forms.IntegerField(initial=1)

class DisplayChildrenForm(forms.Form):
    LEVELS = (("all", "All levels",),
              ("first", "First level",),
              ("last", "Last level"),)
    level = forms.ChoiceField(choices=LEVELS, widget=forms.RadioSelect())
    date = forms.DateTimeField(required=False)

class ModifyChildForm(forms.ModelForm):
    delete = forms.BooleanField(required=False, initial=False)
    parent = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   widget=forms.HiddenInput())
    child = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   widget=forms.HiddenInput())

    class Meta:
        model = m.ParentChildLink
        fields = ["order", "quantity", "child", "parent"]

def get_children_formset(controller, data=None):
    Formset = modelformset_factory(m.ParentChildLink, form=ModifyChildForm, extra=0)
    if data is None:
        queryset = m.ParentChildLink.objects.filter(parent=controller,
                                                    end_time__exact=None)
        formset = Formset(queryset=queryset)
    else:
        formset = Formset(data=data)
    return formset

class AddRevisionForm(forms.Form):
    revision = forms.CharField()
