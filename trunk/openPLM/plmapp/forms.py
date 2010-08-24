from django import forms
from django.forms.models import modelform_factory, modelformset_factory

import openPLM.plmapp.models as m

from django.forms import ValidationError
import re


from django.contrib.auth.models import User

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

def integerfield_clean(value):
    value_validated = ""
    if value:
        value = "".join(value.split())
        value_validated = re.search(r'^(>|<|)(\-?\d*)$',value)
        if value_validated:
            return value_validated.groups()
        else:
            raise ValidationError("Number or \"< Number\" or \"> Number\"")

class type_form(forms.Form):
    LISTE = m.get_all_users_and_plmobjects_with_level()
    type = forms.TypedChoiceField(choices=LISTE)

#class attributes_form(type_form):
    #reference = forms.CharField(widget=forms.TextInput(attrs={'title':"You can use * charactere(s) to enlarge your research", 'value':"*"}), required=False)
    #revision = forms.CharField(widget=forms.TextInput(attrs={'title':"You can use * charactere(s) to enlarge your research", 'value':"*"}), required=False)

class FakeItems(object):
    def __init__(self, values):
        self.values = values
    def items(self):
        return self.values

def get_search_form(cls=m.PLMObject, data=None):
    if issubclass(cls, m.PLMObject):
        fields = set(cls.get_creation_fields())
        fields.update(set(cls.get_modification_fields()))
        fields.difference_update(("type", "lifecycle"))
    else :
        fields = set(["username", "first_name", "last_name"])
    fields_dict = {}
    for field in fields:
        model_field = cls._meta.get_field(field)
        form_field = model_field.formfield()
        form_field.help_text = ""
        if isinstance(form_field.widget, forms.Textarea):
            form_field.widget = forms.TextInput(attrs={'title':"You can use * charactere(s) to enlarge your research.", 'value':"*"})
        if isinstance(form_field.widget, forms.TextInput):
            form_field.widget = forms.TextInput(attrs={'title':"You can use * charactere(s) to enlarge your research.", 'value':"*"})
        if isinstance(form_field, forms.fields.IntegerField) and isinstance(form_field.widget, forms.TextInput):
            form_field.widget = forms.TextInput(attrs={'title':"Please enter a whole number. You can use < or > to enlarge your research."})
        form_field.required = False
        fields_dict[field] = form_field
        if isinstance(form_field, forms.fields.IntegerField):
            form_field.clean = integerfield_clean

    def search(self, query_set=None):
        if self.is_valid():
            for field in self.changed_data:
                model_field = cls._meta.get_field(field)
                form_field = model_field.formfield()
                if isinstance(form_field, forms.fields.CharField)\
                                and isinstance(form_field.widget, (forms.TextInput, forms.Textarea)):
                    value_list = "".join(self.cleaned_data[field].split())
                    value_list = value_list.split('*')
                    if len(value_list)==1:
                        query={}
                        query["%s__iexact"%field]=value_list[0]
                        query_set = query_set.filter(**query)
                    else :
                        if value_list[0]:
                            query={}
                            query["%s__istartswith"%field]=value_list[0]
                            query_set = query_set.filter(**query)
                        if value_list[-1]:
                            query={}
                            query["%s__iendswith"%field]=value_list[-1]
                            query_set = query_set.filter(**query)
                        for value_item in value_list[1:-1]:
                            if value_item:
                                query={}
                                query["%s__icontains"%field]=value_item
                                query_set = query_set.filter(**query)
                elif isinstance(form_field, forms.fields.IntegerField)\
                                and isinstance(form_field.widget, (forms.TextInput, forms.Textarea)):
                    sign, value_str = self.cleaned_data[field]
                    if not sign :
                        query={}
                        query[field]=value_str
                        query_set = query_set.filter(**query)
                    elif sign==">":
                        query={}
                        query["%s__gt"%field]=value_str
                        query_set = query_set.filter(**query)
                    if sign=="<":
                        query={}
                        query["%s__lt"%field]=value_str
                        query_set = query_set.filter(**query)
                else:
                    query={}
                    query[field] = self.cleaned_data[field]
                    query_set = query_set.filter(**query)
            if query_set is not None:
                return query_set
            else:
                return []
    fields_list = fields_dict.items()
    for ref, field in fields_list:
        if ref=='reference':
            fields_list.remove((ref, field))
            fields_list.insert(0, (ref, field))
            break
    ordered_fields_list = FakeItems(fields_list)
    Form = type("Search%sForm" % cls.__name__,
                (forms.BaseForm,),
                {"base_fields" : ordered_fields_list, "search" : search}) 
    if data is not None:
        return Form(data=data, empty_permitted=True)
    else:
        return Form(empty_permitted=True)
       
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
    type = forms.CharField()
    reference = forms.CharField()
    revision = forms.CharField()
    quantity = forms.FloatField()
    order = forms.IntegerField()

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
    quantity = forms.FloatField(widget=forms.TextInput(attrs={'size':'4'}))
    order = forms.IntegerField(widget=forms.TextInput(attrs={'size':'2'}))
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
    
class AddRelPartForm(forms.Form):
    type = forms.CharField()
    reference = forms.CharField()
    revision = forms.CharField()
    
class ModifyRelPartForm(forms.ModelForm):
    delete = forms.BooleanField(required=False, initial=False)
    document = forms.ModelChoiceField(queryset=m.Document.objects.all(),
                                   widget=forms.HiddenInput())
    part = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   widget=forms.HiddenInput())
    class Meta:
        model = m.DocumentPartLink
        fields = ["document", "part"]
        
def get_rel_part_formset(controller, data=None):
    Formset = modelformset_factory(m.DocumentPartLink, form=ModifyRelPartForm, extra=0)
    if data is None:
        queryset = controller.get_attached_parts()
        formset = Formset(queryset=queryset)
    else:
        formset = Formset(data=data)
    return formset

class AddFileForm(forms.Form):
    filename = forms.FileField()
    
class ModifyFileForm(forms.ModelForm):
    delete = forms.BooleanField(required=False, initial=False)
    document = forms.ModelChoiceField(queryset=m.Document.objects.all(),
                                   widget=forms.HiddenInput())
    class Meta:
        model = m.DocumentFile
        fields = ["document"]
        
def get_file_formset(controller, data=None):
    Formset = modelformset_factory(m.DocumentFile, form=ModifyFileForm, extra=0)
    if data is None:
        queryset = controller.files
        formset = Formset(queryset=queryset)
    else:
        formset = Formset(data=data)
    return formset



class AddDocCadForm(forms.Form):
    type = forms.CharField()
    reference = forms.CharField()
    revision = forms.CharField()
    
class ModifyDocCadForm(forms.ModelForm):
    delete = forms.BooleanField(required=False, initial=False)
    part = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   widget=forms.HiddenInput())
    document = forms.ModelChoiceField(queryset=m.Document.objects.all(),
                                   widget=forms.HiddenInput())
    class Meta:
        model = m.DocumentPartLink
        fields = ["part", "document"]
        
def get_doc_cad_formset(controller, data=None):
    Formset = modelformset_factory(m.DocumentPartLink, form=ModifyDocCadForm, extra=0)
    if data is None:
        queryset = controller.get_attached_documents()
        formset = Formset(queryset=queryset)
    else:
        formset = Formset(data=data)
    return formset

class FilterObjectForm4Part(forms.Form):
    child = forms.BooleanField(initial=True, required=False)
    parents = forms.BooleanField(required=False)
    doc = forms.BooleanField(required=False)
    cad = forms.BooleanField(required=False)
    owner = forms.BooleanField(required=False)
    signer = forms.BooleanField(required=False)
    notified = forms.BooleanField(required=False)
    data={'Child': True, 'Parents': False, 'Doc': True, 'Cad': False, 'User': False}

class FilterObjectForm4Doc(forms.Form):
    part = forms.BooleanField(initial=True, required=False)
    owner = forms.BooleanField(required=False)
    signer = forms.BooleanField(required=False)
    notified = forms.BooleanField(required=False)
    data={'Part': True, 'Owner': True, 'Signer': False, 'Notified': False}

class FilterObjectForm4User(forms.Form):
    owned = forms.BooleanField(required=False)
    to_sign = forms.BooleanField(required=False)
    request_notification_from = forms.BooleanField(required=False)
    data={'owned': True, 'to_sign': False, 'request_notification_from': False}

class OpenPLMUserChangeForm(forms.ModelForm):
    #username = forms.RegexField(widget=forms.HiddenInput())
    class Meta:
        model = User
        exclude = ('username','is_staff', 'is_active', 'is_superuser', 'last_login', 'date_joined', 'groups', 'user_permissions', 'password')

class replace_management_form(forms.Form):
    type = forms.CharField()
    username = forms.CharField()
    

