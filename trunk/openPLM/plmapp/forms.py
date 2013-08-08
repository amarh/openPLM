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
#    along with openPLM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

import re
from collections import defaultdict
import datetime

from django import forms
from django.conf import settings
from django.forms import ValidationError
from django.forms.formsets import formset_factory, BaseFormSet
from django.forms.models import modelform_factory, modelformset_factory, \
        BaseModelFormSet
from django.forms.fields import BooleanField
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from django.utils.functional import memoize
from django.template.defaultfilters import filesizeformat

from haystack.forms import SearchForm

import openPLM.plmapp.models as m
from openPLM.plmapp.controllers.document import DocumentController
from openPLM.plmapp.controllers.user import UserController
from openPLM.plmapp.controllers.group import GroupController
from openPLM.plmapp.references import get_new_reference, validate_reference, validate_revision
from openPLM.plmapp.widgets import JQueryAutoComplete
from openPLM.plmapp.utils.encoding import ENCODINGS
from openPLM.plmapp.utils.importing import import_dotted_path
from openPLM.plmapp.utils.units import UNITS, DEFAULT_UNIT


def _clean_reference(self):
    data = self.cleaned_data["reference"]
    try:
        validate_reference(data)
    except ValueError as e:
        raise ValidationError(unicode(e))
    return re.sub("\s+", " ", data.strip(" "))

def _clean_revision(self):
    data = self.cleaned_data["revision"]
    try:
        validate_revision(data)
    except ValueError as e:
        raise ValidationError(unicode(e))
    return re.sub("\s+", " ", data.strip(" "))

INVALID_GROUP = _("Bad group, check that the group exists and that you belong"
        " to this group.")

def enhance_fields(form, cls):
    """
    Replaces textinputs field of *form* with auto complete fields.

    Replaces textareas' widgets with widgets user defined widgets
    (:setting:`RICHTEXT_WIDGET_CLASS` setting).

    :param form: a :class:`Form` instance or class
    :param cls: class of the source that provides suggested values
    """
    richtext_class = getattr(settings, "RICHTEXT_WIDGET_CLASS", None)
    if richtext_class is not None:
        richtext_class = import_dotted_path(richtext_class)

    for field, form_field in form.base_fields.iteritems():
        if field not in ("reference", "revision") and \
                isinstance(form_field.widget, forms.TextInput):
            source = '/ajax/complete/%s/%s/' % (cls.__name__, field)
            form_field.widget = JQueryAutoComplete(source)
        elif (richtext_class is not None and
              isinstance(form_field.widget, forms.Textarea)):
            f = cls._meta.get_field(field)
            if getattr(f, "richtext", False):
                form_field.widget = richtext_class()


def get_initial_creation_data(user, cls, start=0, inbulk_cache=None):
    u"""
    Returns initial data to create a new object (from :func:`get_creation_form`).

    :param user: user who will create the object
    :param cls: class of the created object
    :param start: used to generate the reference,  see :func:`.get_new_reference`
    """
    if issubclass(cls, m.PLMObject):
        data = {
            'reference' : get_new_reference(user, cls, start, inbulk_cache),
            'revision' : 'a',
            'lifecycle' : str(m.get_default_lifecycle().pk),
        }
    else:
        data = {}
    return data


class CreationForm(forms.ModelForm):
    """
    Base class of forms used to create an object (Part, Document, Group...)

    :param user: User who creates the object
    :param start: an offset useful when several forms are displayed at the
                  same time so that all forms have a valid, unique reference
    :param inbulk_cache: a dictionary to store cached data, like valid groups
    :param args: extra arguments passed to :class:`~ModelFrom` constructor
    :param kwargs: extra kwargs arguments passed to :class:`~ModelForm` constructor
    """
    def __init__(self, user, start, inbulk_cache, *args, **kwargs):
        self.start = start
        self.inbulk_cache = inbulk_cache
        super(CreationForm, self).__init__(*args, **kwargs)


class PLMObjectCreationForm(forms.ModelForm):

    auto = BooleanField(required=False, initial=True,
            help_text=_("Checking this box, you allow OpenPLM to set the reference of the object."))

    clean_reference = _clean_reference
    clean_revision = _clean_revision

    def __init__(self, user, start, inbulk_cache, *args, **kwargs):
        data = kwargs.get("data")
        if data is None:
            initial = get_initial_creation_data(user, self.Meta.model, start, inbulk_cache)
            initial.update(kwargs.pop("initial", {}))
            kwargs["initial"] = initial
        self.start = start
        self.inbulk_cache = inbulk_cache
        self.user = user
        super(PLMObjectCreationForm, self).__init__(*args, **kwargs)
        # lifecycles and groups are cached if inbulk_cache is a dictionary
        # this is an optimization if several creation forms are displayed
        # in one request
        # for example, the decomposition of a STEP file can display
        # a lot of creation forms

        # display only valid groups
        field = self.fields["group"]
        field.cache_choices = inbulk_cache is not None

        if inbulk_cache is None or "group" not in inbulk_cache:
            groups = user.groups.all().values_list("id", flat=True)
            field.queryset = m.GroupInfo.objects.filter(id__in=groups).order_by("name")
            if inbulk_cache is not None:
                # a bit ugly but ModelChoiceField reevalute the
                # queryset if cache_choices is False and choice_cache
                # is not populated
                inbulk_cache["group"] = field.queryset
                list(field.choices) # populates choice_cache
                inbulk_cache["gr_cache"] = field.choice_cache
        else:
            field.queryset = inbulk_cache["group"]
            field.choice_cache = inbulk_cache["gr_cache"]
        field.error_messages["invalid_choice"] = INVALID_GROUP
        if data is None and "group" not in initial:
            # set initial value of group to the last selected group
            try:
                field.initial = inbulk_cache["gr_initial"]
            except (KeyError, TypeError):
                try:
                    last_created_object = m.PLMObject.objects.filter(creator=user).order_by("-ctime")[0]
                    last_group = last_created_object.group
                except IndexError:
                    last_group = field.queryset[0] if field.queryset else None
                if last_group in field.queryset:
                    field.initial = last_group
                if inbulk_cache:
                    inbulk_cache["gr_initial"] = field.initial

        # do not accept the cancelled lifecycle
        field = self.fields["lifecycle"]
        field.cache_choices = inbulk_cache is not None
        if inbulk_cache is None or "lifecycles" not in inbulk_cache:
            lifecycles = m.Lifecycle.objects.filter(type=m.Lifecycle.STANDARD).\
                    exclude(pk=m.get_cancelled_lifecycle().pk).order_by("name")
            self.fields["lifecycle"].queryset = lifecycles
            if inbulk_cache is not None:
                inbulk_cache["lifecycles"] = lifecycles
                list(field.choices)
                inbulk_cache["lc_cache"] = field.choice_cache
        else:
            lifecycles = inbulk_cache["lifecycles"]
            self.fields["lifecycle"].queryset = lifecycles
            field.choice_cache = inbulk_cache["lc_cache"]

    def clean(self):
        cleaned_data = self.cleaned_data
        ref = cleaned_data.get("reference", "")
        rev = cleaned_data.get("revision", "")
        auto = cleaned_data.get("auto", False)
        inbulk = getattr(self, "inbulk_cache")
        cls = self.Meta.model
        user = self.user
        if auto and not ref:
            cleaned_data["reference"] = ref = get_new_reference(user, cls, self.start, inbulk)
        if not auto and not ref:
            self.errors['reference']=[_("You did not check the Auto box: the reference is required.")]
        if cls.objects.filter(type=cls.__name__, revision=rev, reference=ref).exists():
            if not auto:
                raise ValidationError(_("An object with the same type, reference and revision already exists"))
            else:
                cleaned_data["reference"] = get_new_reference(user, cls, self.start, inbulk)
        elif cls.objects.filter(type=cls.__name__, reference=ref).exists():
            raise ValidationError(_("An object with the same type and reference exists, you may consider to revise it."))
        return cleaned_data


class PrivateFileChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.filename


class Document2CreationForm(PLMObjectCreationForm):

    pfiles = PrivateFileChoiceField(queryset=m.PrivateFile.objects.none(),
            required=False, widget=forms.MultipleHiddenInput())

    def __init__(self, user, start, inbulk_cache, *args, **kwargs):
        super(Document2CreationForm, self).__init__(user, start, inbulk_cache,
            *args, **kwargs)
        self.fields["pfiles"].queryset = user.files.all().order_by("filename")


def get_creation_form(user, cls=m.PLMObject, data=None, start=0, inbulk_cache=None, **kwargs):
    u"""
    Returns a creation form suitable to create an object
    of type *cls*.

    The returned form can be used, if it is valid, with the function
    :meth:`~plmapp.controllers.PLMObjectController.create_from_form`
    to create a :class:`~plmapp.models.PLMObject` and its associated
    :class:`~plmapp.controllers.PLMObjectController`.

    If *data* is provided, it will be used to fill the form.

    *start* is used if *data* is ``None``, it's usefull if you need to show
    several initial creation forms at once and you want different references.

    *inbulk_cache* may be a dictionary to cache lifecycles, groups and other
    values. It is useful if a page renders several creation forms bound to the same
    user
    """
    Form = get_creation_form.cache.get(cls)
    if Form is None:
        fields = cls.get_creation_fields()
        if issubclass(cls, m.PLMObject):
            if issubclass(cls, m.Document) and cls.ACCEPT_FILES:
                base_form = Document2CreationForm
            else:
                base_form = PLMObjectCreationForm
            fields.insert(fields.index("reference") + 1, "auto")
        else:
            base_form = CreationForm
        Form = modelform_factory(cls, fields=fields, exclude=('type', 'state'), form=base_form)
        # replace textinputs with autocomplete inputs, see ticket #66
        enhance_fields(Form, cls)
        if issubclass(cls, m.PLMObject):
            Form.base_fields["reference"].required = False
        get_creation_form.cache[cls] = Form
    return Form(user, start, inbulk_cache, data=data, **kwargs)

get_creation_form.cache = {}

def get_modification_form(cls=m.PLMObject, data=None, instance=None):
    Form = get_modification_form.cache.get(cls)
    if Form is None:
        fields = cls.get_modification_fields()
        Form = modelform_factory(cls, fields=fields)
        enhance_fields(Form, cls)
        get_modification_form.cache[cls] = Form
    if data:
        return Form(data)
    elif instance:
        return Form(instance=instance)
    else:
        return Form()
get_modification_form.cache = {}

def group_types(types):
    res = []
    group = []
    for type_, long_name in types:
        if long_name[0] not in '=>':
            group = []
            res.append((long_name, group))
        group.append((type_, long_name))
    return res

def type_field(choices):
    f = forms.TypedChoiceField(choices=choices, label=_("Select a type") )
    f.widget.attrs["autocomplete"] = "off"
    return f

class TypeForm(forms.Form):
    type = type_field(group_types(m.get_all_users_and_plmobjects_with_level()))

class PartTypeForm(forms.Form):
    type = type_field(m.get_all_parts_with_level())

class DocumentTypeForm(forms.Form):
    type = type_field(m.get_all_documents_with_level())


class Document2TypeForm(forms.Form):
    # only documents that accept files
    type = type_field(m.get_all_documents_with_level(True))


class SimpleSearchForm(SearchForm):

    LIST = group_types(m.get_all_users_and_plmobjects_with_level())
    type = forms.TypedChoiceField(choices=[("all", _("All"))] + LIST)
    type.widget.attrs["autocomplete"] = "off"
    q = forms.CharField(label=_("Query"), required=False, initial="*")
    search_official = forms.BooleanField(label=_("Official objects"), required=False)

    def __init__(self, *args, **kwargs):
        super(SimpleSearchForm, self).__init__(*args, **kwargs)
        # swap type and q fields
        t = self.fields.pop("type")
        q = self.fields.pop("q")
        o = self.fields.pop("search_official")
        self.fields["type"] = t
        self.fields["q"] = q
        self.fields["search_official"] = o

    def search(self):
        from haystack.query import EmptySearchQuerySet
        from openPLM.plmapp.search import SmartSearchQuerySet

        if self.is_valid():
            type_ = self.cleaned_data["type"]
            query = self.cleaned_data["q"].strip()
            if type_ != "all":
                cls = m.get_all_users_and_plmobjects()[type_]
                d = {}
                m.get_all_subclasses(cls, d)
                mods = d.values()
                if issubclass(cls, m.Document) and query not in ("", "*"):
                # include documentfiles if we search for a document and
                # if the query does not retrieve all documents
                    mods.append(m.DocumentFile)

                sqs = SmartSearchQuerySet().models(*mods)
            else:
                sqs = SmartSearchQuerySet()
            if self.cleaned_data["search_official"]:
                sqs = sqs.filter(state_class="official")
            if not query or query == "*":
                return sqs.exclude(state_class="cancelled")
            results = sqs.highlight().auto_query(query)
            return results
        else:
            return EmptySearchQuerySet()


OBJECT_DOES_NOT_EXIST_MSG = _(
"""The object %(type)s // %(reference)s // %(revision)s does not exist.
Note that all fields are case-sensitive.
"""
)
class PLMObjectForm(forms.Form):
    u"""
    A form that identifies a :class:`PLMObject`.
    """

    type = forms.CharField()
    reference = forms.CharField()
    revision = forms.CharField()

    def clean(self):
        cleaned_data = super(PLMObjectForm, self).clean()
        type_ = cleaned_data.get("type")
        reference = cleaned_data.get("reference")
        revision = cleaned_data.get("revision")
        if type_ and reference and revision:
            d = dict(type=type_, reference=reference, revision=revision)
            if not m.PLMObject.objects.filter(**d).exists():
                raise ValidationError(OBJECT_DOES_NOT_EXIST_MSG % d)
        return cleaned_data



class AddChildForm(PLMObjectForm, PartTypeForm):
    quantity = forms.FloatField(initial=1)
    order = forms.IntegerField(widget=forms.HiddenInput())
    unit = forms.ChoiceField(choices=UNITS, initial=DEFAULT_UNIT)

    def __init__(self, parent, *args, **kwargs):
        super(AddChildForm, self).__init__(*args, **kwargs)
        self._PCLEs = defaultdict(list)
        initial = kwargs.get("initial")
        if not self.is_bound and (initial is None or "order" not in initial):
            orders = list(parent.parentchildlink_parent.values_list('order', flat=True))
            initial_order = max(orders) + 10 if orders else 10
            self.fields["order"].initial = initial_order

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
                try:
                    data[field] = self.cleaned_data[field_name]
                except KeyError:
                    # the form is invalid
                    pass
            self.extensions[PCLE._meta.module_name] = data
        return self.cleaned_data

class DisplayChildrenForm(forms.Form):
    LEVELS = (("all", _("All levels")),
              ("first", _("First level")),
              ("last", _("Last level")),)
    STATES = (("all" , _("All status")),
              ("official", _("Official")),)
    level = forms.ChoiceField(choices=LEVELS, widget=forms.RadioSelect())
    date = forms.SplitDateTimeField(required=False)
    state = forms.ChoiceField(choices=STATES, initial="all")
    show_alternates = forms.BooleanField(label=_("Show alternates"),
            required=False, initial=False)
    show_documents = forms.BooleanField(label=_("Show documents"),
            required=False, initial=False)

class CompareBOMForm(DisplayChildrenForm):
    date = forms.SplitDateTimeField(label=_("Fisrt date"), required=False)
    date2 = forms.SplitDateTimeField(label=_("Second date"), required=False)
    compact = forms.BooleanField(initial=True, required=False)

    def __init__(self, *args, **kwargs):
        super(CompareBOMForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder =  ("date", "date2", "level", "state",
                "show_alternates", "show_documents", "compact")


class ModifyChildForm(forms.ModelForm):
    delete = forms.BooleanField(required=False, initial=False)
    parent = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   widget=forms.HiddenInput())
    child = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   widget=forms.HiddenInput())
    quantity = forms.FloatField(widget=forms.TextInput(attrs={'size':'4'}))
    order = forms.IntegerField(widget=forms.TextInput(attrs={'size':'2'}))
    unit = forms.ChoiceField(choices=UNITS, initial=DEFAULT_UNIT)

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
                try:
                    data[field] = self.cleaned_data[field_name]
                except KeyError:
                    # the form is invalid
                    pass
            self.extensions[PCLE._meta.module_name] = data
        return self.cleaned_data

class BaseChildrenFormSet(BaseModelFormSet):

    def __init__(self, *args, **kwargs):
        # all form instances have the same parent
        # a cache parent id -> pcles reduces the number of queries
        # to get the leaf object and its pcles
        self.pcle_cache = {}
        super(BaseChildrenFormSet, self).__init__(*args, **kwargs)

    def add_fields(self, form, index):
        super(BaseChildrenFormSet, self).add_fields(form, index)
        form.PCLEs = defaultdict(list)
        try:
            pcles = self.pcle_cache[form.instance.parent_id]
        except KeyError:
            parent = form.instance.parent.get_leaf_object()
            pcles = [p for p in m.get_PCLEs(parent) if p.one_per_link()]
            self.pcle_cache[parent.id] = pcles
        for PCLE in pcles:
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
        queryset = m.ParentChildLink.current_objects.filter(parent=controller)
        queryset = queryset.select_related("child__state")
        formset = ChildrenFormset(queryset=queryset)
    else:
        formset = ChildrenFormset(data=data)
    return formset

class AddRevisionForm(forms.Form):
    revision = forms.CharField()
    group = forms.ModelChoiceField(queryset=m.GroupInfo.objects.none())
    clean_revision = _clean_revision

    def __init__(self, ctrl, user, *args, **kwargs):
        super(AddRevisionForm, self).__init__(*args, **kwargs)
        groups = user.groups.all().values_list("id", flat=True)
        groupinfos = m.GroupInfo.objects.filter(id__in=groups)
        in_group = ctrl.check_in_group(user, raise_=False)
        fgroup = self.fields["group"]
        fgroup.queryset = groupinfos
        fgroup.required = not in_group
        if in_group:
            self.initial["group"] = ctrl.group


class RelPartForm(forms.ModelForm):
    document = forms.ModelChoiceField(queryset=m.Document.objects.all(),
                                   widget=forms.HiddenInput())
    part = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   widget=forms.HiddenInput())
    class Meta:
        model = m.DocumentPartLink
        fields = ["document", "part"]

class SelectPartForm(forms.ModelForm):
    selected = forms.BooleanField(required=False, initial=True)
    class Meta:
        model = m.Part
        fields = ["selected"]

SelectPartFormset = modelformset_factory(m.Part, form=SelectPartForm, extra=0)


class SelectDocumentForm(forms.Form):
    selected = forms.BooleanField(required=False, initial=True)
    document = forms.ModelChoiceField(queryset=m.Document.objects.all(),
                                   widget=forms.HiddenInput())

SelectDocumentFormset = formset_factory(form=SelectDocumentForm, extra=0)

class SelectChildForm(forms.Form):
    selected = forms.BooleanField(required=False, initial=True)
    link = forms.ModelChoiceField(queryset=m.ParentChildLink.objects.all(),
                                   widget=forms.HiddenInput())
SelectChildFormset = formset_factory(form=SelectChildForm, extra=0)


class SelectParentForm(SelectChildForm):
    selected = forms.BooleanField(required=False, initial=False)
    new_parent = forms.ModelChoiceField(queryset=m.Part.objects.all(),
                                   widget=forms.HiddenInput())
SelectParentFormset = formset_factory(form=SelectParentForm, extra=0)



class AddPartForm(PLMObjectForm, PartTypeForm):
    pass

class ModifyRelPartForm(RelPartForm):
    delete = forms.BooleanField(required=False, initial=False)

RelPartFormset = modelformset_factory(m.DocumentPartLink,
                                      form=ModifyRelPartForm, extra=0)

def get_rel_part_formset(controller, data=None, **kwargs):
    queryset = controller.get_detachable_parts()
    formset = RelPartFormset(queryset=queryset, data=data, **kwargs)
    return formset

class AddFileForm(forms.Form):
    filename = forms.FileField()

class DeleteFileForm(forms.ModelForm):
    delete = forms.BooleanField(required=False, initial=False)
    document = forms.ModelChoiceField(queryset=m.Document.objects.all(),
                                   widget=forms.HiddenInput())
    class Meta:
        model = m.DocumentFile
        fields = ["document"]

FileFormset = modelformset_factory(m.DocumentFile, form=DeleteFileForm, extra=0)
def get_file_formset(controller, data=None):
    if data is None:
        queryset = controller.files.order_by("-locked", "-ctime")
        formset = FileFormset(queryset=queryset)
    else:
        formset = FileFormset(data=data)
    return formset


class DeletePrivateFileForm(forms.ModelForm):
    delete = forms.BooleanField(required=False, initial=False)
    creator = forms.ModelChoiceField(queryset=User.objects.all(),
                                   widget=forms.HiddenInput())
    class Meta:
        model = m.PrivateFile
        fields = ["creator"]

PrivateFileFormset = modelformset_factory(m.PrivateFile, form=DeletePrivateFileForm, extra=0)
def get_private_file_formset(controller, data=None):
    if data is None:
        queryset = controller.files.order_by("-ctime")
        formset = PrivateFileFormset(queryset=queryset)
    else:
        formset = PrivateFileFormset(data=data)
    return formset



class AddDocCadForm(PLMObjectForm, DocumentTypeForm):
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
def get_doc_cad_formset(controller, data=None, **kwargs):
    queryset = controller.get_detachable_documents()
    formset = DocCadFormset(queryset=queryset, data=data, **kwargs)
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
    date = forms.DateField(required=False,
        widget=forms.DateInput(attrs={"size":10}))
    time = forms.TimeField(required=False,
            widget=forms.TimeInput(attrs={"size":8}))

class PartNavigateFilterForm(NavigateFilterForm):
    child = forms.BooleanField(initial=True, required=False, label=_("child"))
    parents = forms.BooleanField(initial=True, required=False, label=_("parents"))
    doc = forms.BooleanField(initial=True, required=False, label=_("doc"))
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

class ECRNavigateFilterForm(NavigateFilterForm):
    owner = forms.BooleanField(required=False, label=_("owner"))
    signer = forms.BooleanField(required=False, label=_("signer"))
    part = forms.BooleanField(initial=True, required=False, label=_("part"))
    doc = forms.BooleanField(initial=True, required=False, label=_("doc"))


def get_navigate_form(obj):
    if isinstance(obj, UserController):
        cls = UserNavigateFilterForm
    elif isinstance(obj, DocumentController):
        cls = DocNavigateFilterForm
    elif isinstance(obj, GroupController):
        cls = GroupNavigateFilterForm
    elif obj.type == "ECR":
        cls = ECRNavigateFilterForm
    else:
        cls = PartNavigateFilterForm
    return cls


MAX_AVATAR_SIZE = 100 * 1024

class OpenPLMUserChangeForm(forms.ModelForm):

    class Meta:
        model = User
        exclude = ('username','is_staff', 'is_active', 'is_superuser',
                'last_login', 'date_joined', 'groups', 'user_permissions',
                'password')

    avatar = forms.ImageField(required=False)

    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']
        if avatar:
            max_size = getattr(settings, "MAX_AVATAR_SIZE", MAX_AVATAR_SIZE)
            content_type = avatar.content_type.split('/')[0]
            if content_type == "image":
                if avatar.size > max_size:
                    raise forms.ValidationError(_('Please keep filesize under %s. Current filesize %s') %
                            (filesizeformat(max_size), filesizeformat(avatar.size)))
            else:
                raise forms.ValidationError(_('File type is not supported'))
        return avatar


USER_DOES_NOT_EXIST_MSG = _(
"""The user "%(username)s" does not exist.
Note that username field is case-sensitive.
"""
)
class SelectUserForm(forms.Form):
    type = forms.CharField(label=_("Type"), initial="User")
    username = forms.CharField(label=_("Username"))

    def clean(self):
        cleaned_data = super(SelectUserForm, self).clean()
        username = cleaned_data.get("username")
        if username:
            if not User.objects.filter(username=username).exists():
                raise ValidationError(USER_DOES_NOT_EXIST_MSG %
                        {"username" : username})
        return cleaned_data


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
    ROLES = (("contributor",_("Contributor: can create parts, documents, groups and sponsor other users")),
            ("reader", _("Reader: can not edit or create contents")),
            ("restricted", _("Restricted account: can only access to specific contents")),
    )
    sponsor = forms.ModelChoiceField(queryset=User.objects.all(),
            required=True, widget=forms.HiddenInput())
    warned = forms.BooleanField(initial=False, required=False,
                                widget=forms.HiddenInput())
    role = forms.TypedChoiceField(choices=ROLES, required=False,
            initial="contributor", widget=forms.RadioSelect)
    language = forms.TypedChoiceField(choices=settings.LANGUAGES)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'groups')

    def __init__(self, *args, **kwargs):
        sponsor = kwargs.pop("sponsor", None)
        language = kwargs.pop("language", None)
        super(SponsorForm, self).__init__(*args, **kwargs)
        if "sponsor" in self.data:
            sponsor = int(self.data["sponsor"])
        if sponsor is not None:
            qset = m.GroupInfo.objects.filter(owner__id=sponsor)
            self.fields["groups"].queryset = qset
        self.fields["groups"].help_text = _("The new user will belong to the selected groups")
        for key, field in self.fields.iteritems():
            field.required = key not in ("warned", "role", "groups")

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

    def clean_role(self):
        role = self.cleaned_data["role"] or "contributor"
        return role

    def clean(self):
        super(SponsorForm, self).clean()
        try:
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
                role = self.cleaned_data.get("role", "contributor")
                groups = self.cleaned_data["groups"]
                if role == "restricted" and groups:
                    self.cleaned_data["groups"] = ()
                if role != "restricted" and not groups:
                    error = _("A contributor or reader must belong to at least one group.")
                    raise forms.ValidationError(error)
        except KeyError:
            pass
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

class ConfirmPasswordForm(forms.Form):
    """
    A form that checks the user has entered his password.
    """
    password = forms.CharField(label=_("Password"),
            widget=forms.PasswordInput(attrs= { "autocomplete" : "off" }))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(ConfirmPasswordForm, self).__init__(*args, **kwargs)

    def clean_password(self):
        """
        Validates that the password field is correct.
        """
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError(_("Your password was entered incorrectly. Please enter it again."))
        return password

class HistoryObjectForm(forms.Form):
    """
    A Form asking the user the information he wants displayed in the history
    """
    document = forms.BooleanField(required = False, initial=True)
    part = forms.BooleanField(required = False, initial=True)
    group = forms.BooleanField(required = False, initial=True)

class HistoryDateForm(forms.Form):
    date_history_begin = forms.DateTimeField(label=_(u"View Changes From *"),
        widget=forms.DateInput(attrs={"size":10}), initial=datetime.date.today(),
        error_messages = {"invalid":"The date isn't valid (format valid: AAAA-MM-JJ)."})
    number_days = forms.IntegerField(label=_(u"and *"), help_text = "days back",  initial=30, max_value=90, min_value=1)
    done_by = forms.CharField(label = _(u"Done by "), required = False)

