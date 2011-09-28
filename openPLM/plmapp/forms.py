############################################################################
# openPLM - open source PLM
# Copyright 2010 Philippe Joulaud, Pierre Cosquer
# 
# This file is part of openPLM.
#
#    openPLM is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    openPLM is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pierre.cosquer@insa-rennes.fr
################################################################################

import re

from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import modelform_factory, modelformset_factory
from django.contrib.auth.models import User, Group
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

import openPLM.plmapp.models as m
from openPLM.plmapp.controllers import rx_bad_ref, DocumentController
from openPLM.plmapp.controllers.user import UserController
from openPLM.plmapp.widgets import JQueryAutoComplete

class PLMObjectForm(forms.Form):
    u"""
    A formulaire that identifies a :class:`PLMObject`.
    """

    type = forms.CharField()
    reference = forms.CharField()
    revision = forms.CharField()


def _clean_reference(self):
    data = self.cleaned_data["reference"]
    if rx_bad_ref.search(data):
        raise ValidationError(_("Bad reference: '#', '?', '/' and '..' are not allowed"))
    return re.sub("\s+", " ", data.strip(" "))

def _clean_revision(self):
    data = self.cleaned_data["revision"]
    if rx_bad_ref.search(data):
        raise ValidationError(_("Bad revision: '#', '?', '/' and '..' are not allowed"))
    return re.sub("\s+", " ", data.strip(" "))

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
    Form = get_creation_form.cache.get(cls)
    if Form is None:
        fields = cls.get_creation_fields()
        Form = modelform_factory(cls, fields=fields, exclude=('type', 'state'))
        if issubclass(cls, m.PLMObject):
            Form.clean_reference = _clean_reference
            Form.clean_revision = _clean_revision
            def _clean(self):
                cleaned_data = self.cleaned_data
                ref = cleaned_data.get("reference", "")
                rev = cleaned_data.get("revision", "")
                if cls.objects.filter(type=cls.__name__, revision=rev, reference=ref):
                    raise ValidationError(_("An object with the same type, reference and revision already exists"))
                return cleaned_data
            Form.clean = _clean
        get_creation_form.cache[cls] = Form
    if data:
        return Form(data=data, empty_permitted=empty_allowed)
    else:
        return Form()
get_creation_form.cache = {}
        
def get_modification_form(cls=m.PLMObject, data=None, instance=None):
    Form = get_modification_form.cache.get(cls)
    if Form is None:
        fields = cls.get_modification_fields()
        Form = modelform_factory(cls, fields=fields)
        get_modification_form.cache[cls] = Form
    if data:
        return Form(data)
    elif instance:
        return Form(instance=instance)
    else:
        return Form()
get_modification_form.cache = {}

def integerfield_clean(value):
    if value:
        value = value.replace(" ", "")
        value_validated = re.search(r'^([><]?)(\-?\d*)$',value)
        if value_validated:
            return value_validated.groups()
        else:
            raise ValidationError("Number or \"< Number\" or \"> Number\"")
    return None

class TypeForm(forms.Form):
    LISTE = m.get_all_users_and_plmobjects_with_level()
    type = forms.TypedChoiceField(choices=LISTE)

class TypeFormWithoutUser(forms.Form):
    LISTE_WO_USER = m.get_all_plmobjects_with_level()
    type = forms.TypedChoiceField(choices=LISTE_WO_USER)

class TypeSearchForm(TypeForm):
    def __init__(self, *args, **kwargs):
        super(TypeSearchForm, self).__init__(*args, **kwargs)
        self.fields['type'].widget.attrs['onChange'] = 'update_form();'

class FakeItems(object):
    def __init__(self, values):
        self.values = values
    def items(self):
        return self.values

def get_search_form(cls=m.PLMObject, data=None):
    Form = get_search_form.cache.get(cls)
    if Form is None:
        if issubclass(cls, (m.PLMObject, m.GroupInfo)):
            fields = set(cls.get_creation_fields())
            fields.update(set(cls.get_modification_fields()))
            fields.difference_update(("type", "lifecycle"))
        else:
            fields = set(["username", "first_name", "last_name"])
        fields_dict = {}
        for field in fields:
            model_field = cls._meta.get_field(field)
            form_field = model_field.formfield()
            form_field.help_text = ""
            if isinstance(form_field.widget, forms.Textarea):
                form_field.widget = forms.TextInput(attrs={'title':"You can use * charactere(s) to enlarge your research.", 'value':"*"})
            if isinstance(form_field.widget, forms.TextInput):
                source = '/ajax/complete/%s/%s/' % (cls.__name__, field)
                form_field.widget = JQueryAutoComplete(source,
                    attrs={'title':"You can use * charactere(s) to enlarge your research.", 'value':"*"})
            if isinstance(form_field, forms.fields.IntegerField) and isinstance(form_field.widget, forms.TextInput):
                form_field.widget = forms.TextInput(attrs={'title':"Please enter a whole number. You can use < or > to enlarge your research."})
            form_field.required = False
            fields_dict[field] = form_field
            if isinstance(form_field, forms.fields.IntegerField):
                form_field.clean = integerfield_clean

        def search(self, query_set=None):
            if self.is_valid():
                query = {}
                for field in self.changed_data:
                    model_field = cls._meta.get_field(field)
                    form_field = model_field.formfield()
                    value =  self.cleaned_data[field]
                    if value is None or (isinstance(value, basestring) and value.isspace()):
                        continue
                    if isinstance(form_field, forms.fields.CharField)\
                                    and isinstance(form_field.widget, (forms.TextInput, forms.Textarea)):
                        value_list = re.split(r"\s*\*\s*", value)
                        if len(value_list)==1:
                            query["%s__iexact"%field]=value_list[0]
                        else :
                            if value_list[0]:
                                query["%s__istartswith"%field]=value_list[0]
                            if value_list[-1]:
                                query["%s__iendswith"%field]=value_list[-1]
                            for value_item in value_list[1:-1]:
                                if value_item:
                                    query["%s__icontains"%field]=value_item
                    elif isinstance(form_field, forms.fields.IntegerField)\
                                    and isinstance(form_field.widget, (forms.TextInput, forms.Textarea)):
                        sign, value_str = self.cleaned_data[field]
                        cr = "%s__%s" %(field, {"" : "exact", ">" : "gt", "<" : "lt"}[sign])
                        query[cr]= int(value_str)
                    else:
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
        get_search_form.cache[cls] = Form
    if data is not None:
        return Form(data=data, empty_permitted=True)
    else:
        return Form(empty_permitted=True)
get_search_form.cache = {}    
      
class AddChildForm(PLMObjectForm):
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

ChildrenFormset = modelformset_factory(m.ParentChildLink,
                                       form=ModifyChildForm, extra=0)
def get_children_formset(controller, data=None):
    if data is None:
        queryset = m.ParentChildLink.objects.filter(parent=controller,
                                                    end_time__exact=None)
        formset = ChildrenFormset(queryset=queryset)
    else:
        formset = ChildrenFormset(data=data)
    return formset

class AddRevisionForm(forms.Form):
    revision = forms.CharField()
    clean_revision = _clean_revision
    
class AddRelPartForm(PLMObjectForm):
    pass
    
class ModifyRelPartForm(forms.ModelForm):
    delete = forms.BooleanField(required=False, initial=False)
    document = forms.ModelChoiceField(queryset=m.Document.objects.all(),
                                   widget=forms.HiddenInput())
    part = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   widget=forms.HiddenInput())
    class Meta:
        model = m.DocumentPartLink
        fields = ["document", "part"]
        
RelPartFormset = modelformset_factory(m.DocumentPartLink,
                                      form=ModifyRelPartForm, extra=0)
def get_rel_part_formset(controller, data=None):
    if data is None:
        queryset = controller.get_attached_parts()
        formset = RelPartFormset(queryset=queryset)
    else:
        formset = RelPartFormset(data=data)
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
        
FileFormset = modelformset_factory(m.DocumentFile, form=ModifyFileForm, extra=0)
def get_file_formset(controller, data=None):
    if data is None:
        queryset = controller.files
        formset = FileFormset(queryset=queryset)
    else:
        formset = FileFormset(data=data)
    return formset

class AddDocCadForm(PLMObjectForm):
    pass
    
class ModifyDocCadForm(forms.ModelForm):
    delete = forms.BooleanField(required=False, initial=False)
    part = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   widget=forms.HiddenInput())
    document = forms.ModelChoiceField(queryset=m.Document.objects.all(),
                                   widget=forms.HiddenInput())
    class Meta:
        model = m.DocumentPartLink
        fields = ["part", "document"]
        
DocCadFormset = modelformset_factory(m.DocumentPartLink,
                                     form=ModifyDocCadForm, extra=0)
def get_doc_cad_formset(controller, data=None):
    if data is None:
        queryset = controller.get_attached_documents()
        formset = DocCadFormset(queryset=queryset)
    else:
        formset = DocCadFormset(data=data)
    return formset


class NavigateFilterForm(forms.Form):
    only_search_results = forms.BooleanField(initial=False,
                required=False, label=_("only search results"))
    prog = forms.ChoiceField(choices=(("twopi", _("Radial 1")),
                                      ("neato", _("Radial 2")),
                                      ("dot", _("Hierarchical"))),
                             required=False, initial="twopi",
                             label=_("layout"))
    doc_parts = forms.CharField(initial="", required="",
                                widget=forms.HiddenInput())
    update = forms.BooleanField(initial=False, required=False,
           widget=forms.HiddenInput() )

class PartNavigateFilterForm(NavigateFilterForm):
    child = forms.BooleanField(initial=True, required=False, label=_("child"))
    parents = forms.BooleanField(required=False, label=_("parents"))
    doc = forms.BooleanField(required=False, label=_("doc"))
    cad = forms.BooleanField(required=False, label=_("cad"))
    owner = forms.BooleanField(required=False, label=_("owner"))
    signer = forms.BooleanField(required=False, label=_("signer"))
    notified = forms.BooleanField(required=False, label=_("notified"))

class DocNavigateFilterForm(NavigateFilterForm):
    part = forms.BooleanField(initial=True, required=False, label=_("part"))
    owner = forms.BooleanField(initial=True, required=False, label=_("owner"))
    signer = forms.BooleanField(required=False, label=_("signer"))
    notified = forms.BooleanField(required=False, label=_("notified"))

class UserNavigateFilterForm(NavigateFilterForm):
    owned = forms.BooleanField(initial=True, required=False, label=_("owned"))
    to_sign = forms.BooleanField(required=False, label=_("to sign"))
    request_notification_from = forms.BooleanField(required=False, label=_("request notification from"))

def get_navigate_form(obj):
    if isinstance(obj, UserController):
        cls = UserNavigateFilterForm
    elif isinstance(obj, DocumentController):
        cls = DocNavigateFilterForm
    else:
        cls = PartNavigateFilterForm
    return cls


class OpenPLMUserChangeForm(forms.ModelForm):
    #username = forms.RegexField(widget=forms.HiddenInput())
    class Meta:
        model = User
        exclude = ('username','is_staff', 'is_active', 'is_superuser', 'last_login', 'date_joined', 'groups', 'user_permissions', 'password')

class SelectUserForm(forms.Form):
    type = forms.CharField(label=_("Type"), initial="User")
    username = forms.CharField(label=_("Username"))
    
    
class ModifyUserForm(forms.Form):
    delete = forms.BooleanField(required=False, initial=False)
    user = forms.ModelChoiceField(queryset=User.objects.all(),
                                   widget=forms.HiddenInput())
    group = forms.ModelChoiceField(queryset=Group.objects.all(),
                                   widget=forms.HiddenInput())
    
    @property
    def user_data(self):
        return self.initial["user"]

UserFormset = formset_factory(ModifyUserForm, extra=0)
def get_user_formset(controller, data=None):
    if data is None:
        queryset = controller.user_set.exclude(id=controller.owner.id)
        initial = [dict(group=controller.object, user=user)
                for user in queryset]
        formset = UserFormset(initial=initial)
    else:
        formset = UserFormset(data)
    return formset

