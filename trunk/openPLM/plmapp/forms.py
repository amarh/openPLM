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
from collections import defaultdict

from django import forms
from django.conf import settings
from django.forms.formsets import formset_factory, BaseFormSet
from django.forms.models import modelform_factory, modelformset_factory, \
        BaseModelFormSet
from django.contrib.auth.models import User, Group
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from django.utils.functional import memoize

import openPLM.plmapp.models as m
from openPLM.plmapp.units import UNITS, DEFAULT_UNIT
from openPLM.plmapp.controllers import rx_bad_ref, DocumentController
from openPLM.plmapp.controllers.user import UserController
from openPLM.plmapp.controllers.group import GroupController
from openPLM.plmapp.widgets import JQueryAutoComplete
from openPLM.plmapp.encoding import ENCODINGS

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

INVALID_GROUP = _("Bad group, check that the group exists and that you belong"
        " to this group.")

def auto_complete_fields(form, cls):
    """
    Replaces textinputs field of *form* with auto complete fields.

    :param form: a :class:`Form` instance or class
    :param cls: class of the source that provides suggested values
    """
    for field, form_field in form.base_fields.iteritems():
        if field not in ("reference", "revision") and \
                isinstance(form_field.widget, forms.TextInput):
            source = '/ajax/complete/%s/%s/' % (cls.__name__, field)
            form_field.widget = JQueryAutoComplete(source)

def get_new_reference(cls, start=0):
    u"""
    Returns a new reference for creating a :class:`.PLMObject` of type
    *cls*.

    The formatting is ``PART_000XX`` if *cls* is a subclass of :class:`.Part`
    and ``DOC_000XX`` otherwise.
    
    The number is the count of Parts or Documents plus *start* plus 1.
    It is incremented while an object with the same reference aleady exists.
    *start* can be used to create several creation forms at once.

    .. note::
        The returned referenced may not be valid if a new object has been
        created after the call to this function.
    """
    if issubclass(cls, m.Part):
        base_cls, name = m.Part, "PART"
    else:
        base_cls, name = m.Document, "DOC"
    nb = base_cls.objects.count() + start + 1
    reference = "%s_%05d" % (name, nb)
    while base_cls.objects.filter(reference=reference).exists():
        nb += 1
        reference = "%s_%05d" % (name, nb)
    return reference

def get_initial_creation_data(cls, start=0):
    u"""
    Returns initial data to create a new object (from :func:`get_creation_form`).

    :param cls: class of the created object
    :param start: used to generate the reference,  see :func:`get_new_reference`
    """
    if issubclass(cls, m.PLMObject):
        data = {
                'reference' : get_new_reference(cls, start), 
                'revision' : 'a',
                'lifecycle' : str(m.get_default_lifecycle().pk),
        }
    else:
        data = {}
    return data

def get_creation_form(user, cls=m.PLMObject, data=None, start=0):
    u"""
    Returns a creation form suitable to creates an object
    of type *cls*.

    The returned form can be used, if it is valid, with the function
    :meth:`~plmapp.controllers.PLMObjectController.create_from_form`
    to create a :class:`~plmapp.models.PLMObject` and his associated
    :class:`~plmapp.controllers.PLMObjectController`.

    If *data* is provided, it will be used to fill the form.

    *start* is used if *data* is ``None``, it's usefull if you need to show
    several initial creation forms at once and you want different references.
    """
    Form = get_creation_form.cache.get(cls)
    if Form is None:
        fields = cls.get_creation_fields()
        Form = modelform_factory(cls, fields=fields, exclude=('type', 'state'))
        # replace textinputs with autocomplete inputs, see ticket #66
        auto_complete_fields(Form, cls)
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
    if data is None:
        form = Form(initial=get_initial_creation_data(cls, start))
    else:
        form = Form(data=data)
    if issubclass(cls, m.PLMObject):
        # display only valid groups
        groups = user.groups.all().values_list("id", flat=True)
        field = form.fields["group"]
        field.queryset = m.GroupInfo.objects.filter(id__in=groups)
        field.error_messages["invalid_choice"] = INVALID_GROUP
    return form
get_creation_form.cache = {}
        
def get_modification_form(cls=m.PLMObject, data=None, instance=None):
    Form = get_modification_form.cache.get(cls)
    if Form is None:
        fields = cls.get_modification_fields()
        Form = modelform_factory(cls, fields=fields)
        auto_complete_fields(Form, cls)
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

def group_types(types):
    res = []
    group = []
    for type_, long_name in types:
        if long_name[0] not in '=>':
            group = []
            res.append((long_name, group))
        group.append((type_, long_name))
    return res

class TypeForm(forms.Form):
    LIST = group_types(m.get_all_users_and_plmobjects_with_level())
    type = forms.TypedChoiceField(choices=LIST)

class TypeFormWithoutUser(forms.Form):
    LIST_WO_USER = group_types(m.get_all_plmobjects_with_level())
    type = forms.TypedChoiceField(choices=LIST_WO_USER,
            label=_("Select a type"))

class TypeSearchForm(TypeForm):
    pass

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
            fields.difference_update(("type", "lifecycle", "group"))
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


from haystack.forms import SearchForm
class SimpleSearchForm(SearchForm):
   
    LIST = group_types(m.get_all_users_and_plmobjects_with_level())
    type = forms.TypedChoiceField(choices=LIST)
    q = forms.CharField(label=_("Query"), required=False)

    def __init__(self, *args, **kwargs):
        super(SimpleSearchForm, self).__init__(*args, **kwargs)
        self.fields.insert(0, 'type', self.fields.pop('type'))
    
    def search(self):
        from haystack.query import EmptySearchQuerySet
        from openPLM.plmapp.search import SmartSearchQuerySet
        
        if self.is_valid():
            cls = m.get_all_users_and_plmobjects()[self.cleaned_data["type"]]
            d = {}
            m._get_all_subclasses(cls, d)
            mods = d.values()
            query = self.cleaned_data["q"].strip()
            if issubclass(cls, m.Document) and query.strip() not in ("", "*"):
            # include documentfiles if we search for a document and
            # if the query does not retrieve all documents
                mods.append(m.DocumentFile)

            sqs = SmartSearchQuerySet().highlight().models(*mods)
            if not query or query == "*":
                return sqs
            results = sqs.auto_query(query)
            return results
        else:
            return EmptySearchQuerySet()
        

class AddChildForm(PLMObjectForm):
    quantity = forms.FloatField()
    order = forms.IntegerField()
    unit = forms.ChoiceField(choices=UNITS, initial=DEFAULT_UNIT)

    def __init__(self, parent, *args, **kwargs):
        super(AddChildForm, self).__init__(*args, **kwargs)
        self._PCLEs = defaultdict(list)
        for PCLE in m.get_PCLEs(parent):
            for field in PCLE.get_editable_fields():
                model_field = PCLE._meta.get_field(field)
                form_field = model_field.formfield()
                field_name = "%s_%s" % (PCLE._meta.module_name, field)
                self.fields[field_name] = form_field
                self._PCLEs[PCLE].append(field)
        
    def clean(self):
        super(AddChildForm, self).clean()
        self.extensions = {}
        for PCLE, fields in self._PCLEs.iteritems():
            data = {}
            for field in fields:
                field_name = "%s_%s" % (PCLE._meta.module_name, field)
                data[field] = self.cleaned_data[field_name]
            self.extensions[PCLE._meta.module_name] = data
        return self.cleaned_data

class DisplayChildrenForm(forms.Form):
    LEVELS = (("all", "All levels",),
              ("first", "First level",),
              ("last", "Last level"),)
    level = forms.ChoiceField(choices=LEVELS, widget=forms.RadioSelect())
    date = forms.SplitDateTimeField(required=False)

class ModifyChildForm(forms.ModelForm):
    delete = forms.BooleanField(required=False, initial=False)
    parent = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   widget=forms.HiddenInput())
    child = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   widget=forms.HiddenInput())
    quantity = forms.FloatField(widget=forms.TextInput(attrs={'size':'4'}))
    order = forms.IntegerField(widget=forms.TextInput(attrs={'size':'2'}))
    unit = forms.ChoiceField(choices=UNITS, initial=DEFAULT_UNIT,
            widget=forms.Select(attrs={"class":"tiny"}))

    class Meta:
        model = m.ParentChildLink
        fields = ["order", "quantity", "unit", "child", "parent",]
    
    def clean(self):
        super(ModifyChildForm, self).clean()
        self.extensions = {}
        for PCLE, fields in self.PCLEs.iteritems():
            data = {}
            for field in fields:
                field_name = "%s_%s" % (PCLE._meta.module_name, field)
                data[field] = self.cleaned_data[field_name]
            self.extensions[PCLE._meta.module_name] = data
        return self.cleaned_data

class BaseChildrenFormSet(BaseModelFormSet):
    def add_fields(self, form, index):
        super(BaseChildrenFormSet, self).add_fields(form, index)
        form.PCLEs = defaultdict(list)
        parent = form.instance.parent.get_leaf_object()
        for PCLE in m.get_PCLEs(parent):
            if not PCLE.one_per_link():
                continue
            try:
                ext = PCLE.objects.get(link=form.instance)
            except PCLE.DoesNotExist:
                ext = None
            for field in PCLE.get_editable_fields():
                initial = getattr(ext, field, None)
                model_field = PCLE._meta.get_field(field)
                form_field = model_field.formfield(initial=initial)
                field_name = "%s_%s" % (PCLE._meta.module_name, field)
                if isinstance(form_field.widget, forms.TextInput):
                    form_field.widget.attrs["size"] = 10
                form.fields[field_name] = form_field
                form.PCLEs[PCLE].append(field)

ChildrenFormset = modelformset_factory(m.ParentChildLink,
       form=ModifyChildForm, extra=0, formset=BaseChildrenFormSet)
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
    prog = forms.ChoiceField(choices=(("dot", _("Hierarchical")),
                                      ("neato", _("Radial 1")),
                                      ("twopi", _("Radial 2")),
                                      ),
                             required=False, initial="dot",
                             label=_("layout"))
    doc_parts = forms.CharField(initial="", required="",
                                widget=forms.HiddenInput())
    update = forms.BooleanField(initial=False, required=False,
           widget=forms.HiddenInput() )

class PartNavigateFilterForm(NavigateFilterForm):
    child = forms.BooleanField(initial=True, required=False, label=_("child"))
    parents = forms.BooleanField(initial=True, required=False, label=_("parents"))
    doc = forms.BooleanField(initial=True, required=False, label=_("doc"))
    cad = forms.BooleanField(required=False, label=_("cad"))
    owner = forms.BooleanField(required=False, label=_("owner"))
    signer = forms.BooleanField(required=False, label=_("signer"))
    notified = forms.BooleanField(required=False, label=_("notified"))

class DocNavigateFilterForm(NavigateFilterForm):
    part = forms.BooleanField(initial=True, required=False, label=_("part"))
    owner = forms.BooleanField(required=False, label=_("owner"))
    signer = forms.BooleanField(required=False, label=_("signer"))
    notified = forms.BooleanField(required=False, label=_("notified"))

class UserNavigateFilterForm(NavigateFilterForm):
    owned = forms.BooleanField(initial=True, required=False, label=_("owned"))
    to_sign = forms.BooleanField(required=False, label=_("to sign"))
    request_notification_from = forms.BooleanField(required=False, label=_("request notification from"))

class GroupNavigateFilterForm(NavigateFilterForm):
    owner = forms.BooleanField(required=False, label=_("owner"))
    user = forms.BooleanField(required=False, label=_("user"))
    part = forms.BooleanField(initial=True, required=False, label=_("part"))
    doc = forms.BooleanField(initial=True, required=False, label=_("doc"))

def get_navigate_form(obj):
    if isinstance(obj, UserController):
        cls = UserNavigateFilterForm
    elif isinstance(obj, DocumentController):
        cls = DocNavigateFilterForm
    elif isinstance(obj, GroupController):
        cls = GroupNavigateFilterForm
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


class SponsorForm(forms.ModelForm):
    sponsor = forms.ModelChoiceField(queryset=User.objects.all(),
            required=True, widget=forms.HiddenInput())
    warned = forms.BooleanField(initial=False, required=False,
                                widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'groups')

    def __init__(self, *args, **kwargs):
        sponsor = kwargs.pop("sponsor", None)
        super(SponsorForm, self).__init__(*args, **kwargs)
        if "sponsor" in self.data:
            sponsor = int(self.data["sponsor"])
        if sponsor is not None:
            qset = m.GroupInfo.objects.filter(owner__id=sponsor)
            self.fields["groups"].queryset = qset
        self.fields["groups"].help_text = _("The new user will belong to the selected groups") 
        for key, field in self.fields.iteritems():
            if key != "warned":
                field.required = True

    def clean_email(self):
        email = self.cleaned_data["email"]
        if email and bool(User.objects.filter(email=email)):
            raise forms.ValidationError(_(u'Email address must be unique.'))
        try:
            # checks *email*
            if settings.RESTRICT_EMAIL_TO_DOMAINS:
                # i don't know if a domain can contains a '@'
                domain = email.rsplit("@", 1)[1]
                if domain not in Site.objects.values_list("domain", flat=True):
                    raise forms.ValidationError(_(u"Email's domain not valid")) 
        except AttributeError:
            # restriction disabled if the setting is not set
            pass
        return email
  
    def clean(self):
        super(SponsorForm, self).clean()
        if not self.cleaned_data.get("warned", False):
            first_name = self.cleaned_data["first_name"]
            last_name = self.cleaned_data["last_name"]
            homonyms = User.objects.filter(first_name=first_name, last_name=last_name)
            if homonyms:
                self.data = self.data.copy()
                self.data["warned"] = "on"
                error = _(u"Warning! There are homonyms: %s!") % \
                    u", ".join(u.username for u in homonyms)
                raise forms.ValidationError(error)
        return self.cleaned_data

_inv_qset = m.Invitation.objects.filter(state=m.Invitation.PENDING)
class InvitationForm(forms.Form):
    invitation = forms.ModelChoiceField(queryset=_inv_qset,
            required=True, widget=forms.HiddenInput())

class CSVForm(forms.Form):
    file = forms.FileField()
    encoding = forms.TypedChoiceField(initial="utf_8", choices=ENCODINGS)


def get_headers_formset(Importer):
    class CSVHeaderForm(forms.Form):
        HEADERS = Importer.get_headers()
        header = forms.TypedChoiceField(choices=zip(HEADERS, HEADERS),
                required=False)

    class BaseHeadersFormset(BaseFormSet):

        def clean(self):
            if any(self.errors):
                return
            headers = []
            for form in self.forms:
                header = form.cleaned_data['header']
                if header == u'None':
                    header = None
                if header and header in headers:
                    raise forms.ValidationError(_("Columns must have distinct headers."))
                headers.append(header) 
            for field in Importer.REQUIRED_HEADERS:
                if field not in headers:
                    raise forms.ValidationError(Importer.get_missing_headers_msg())
            self.headers = headers

    return formset_factory(CSVHeaderForm, extra=0, formset=BaseHeadersFormset)

get_headers_formset = memoize(get_headers_formset, {}, 1)

from openPLM.plmapp.archive import ARCHIVE_FORMATS
class ArchiveForm(forms.Form):
    format = forms.TypedChoiceField(choices=zip(ARCHIVE_FORMATS, ARCHIVE_FORMATS))

