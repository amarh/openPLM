import re

from django import forms
from django.forms.fields import BooleanField
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

import openPLM.plmapp.models as m
from openPLM.plmapp.references import validate_reference
from openPLM.plmapp.forms import enhance_fields

from openPLM.apps.ecr.models import ECR, get_default_lifecycle

def get_new_reference(start=0, inbulk_cache=None):
    u"""
    Returns a new reference for creating a new :class:`.ECR`.

    .. note::
        The returned referenced may not be valid if a new object has been
        created after the call to this function.
    """

    if inbulk_cache is not None and "max_ecr" in inbulk_cache:
        max_ref = inbulk_cache["max_ecr"]
    else:
        try:
            max_ref = ECR.objects.order_by("-reference_number")\
                .values_list("reference_number", flat=True)[0]
        except IndexError:
            max_ref = 0
        if inbulk_cache is not None:
            inbulk_cache["max_ecr"] = max_ref
    nb = max_ref + start + 1
    return "ECR_%05d" % nb

def get_initial_creation_data(start=0, inbulk_cache=None):
    u"""
    Returns initial data to create a new ECR (from :func:`get_creation_form`).

    :param cls: class of the created object
    :param start: used to generate the reference,  see :func:`get_new_reference`
    """
    return {
            'reference' : get_new_reference(start, inbulk_cache),
            'lifecycle' : str(get_default_lifecycle().pk),
    }

class ECRForm(forms.ModelForm):

    class Meta:
        model = ECR
        fields = ECR.get_creation_fields()
        fields.insert(fields.index("reference") + 1, "auto")

    auto = BooleanField(required=False, initial=True,
            help_text=_("Checking this box, you allow OpenPLM to set the reference of the ECR."))

    def clean_reference(self):
        data = self.cleaned_data["reference"]
        try:
            validate_reference(data)
        except ValueError as e:
            raise ValidationError(unicode(e))
        return re.sub("\s+", " ", data.strip(" "))

    def clean(self):
        cleaned_data = self.cleaned_data
        ref = cleaned_data.get("reference", "")
        auto = cleaned_data.get("auto", False)
        inbulk = getattr(self, "inbulk_cache")
        start = getattr(self, "start", 0)
        if auto and not ref:
            cleaned_data["reference"] = ref = get_new_reference(start, inbulk)
        if not auto and not ref:
            self.errors['reference']=[_("You did not check the Auto box: the reference is required.")]
        if ECR.objects.filter(reference=ref).exists():
            if not auto:
                raise ValidationError(_("An object with the same type, reference and revision already exists"))
            else:
                cleaned_data["reference"] = get_new_reference(start, inbulk)
        return cleaned_data

ECRForm.base_fields["reference"].required = False
enhance_fields(ECRForm, ECR)

def get_creation_form(user, data=None, start=0, inbulk_cache=None, **kwargs):
    u"""
    Returns a creation form suitable to create an ECR.

    The returned form can be used, if it is valid, with the function
    :meth:`~plmapp.controllers.ECRController.create_from_form`
    to create a :class:`~plmapp.models.ECR` and its associated
    :class:`~plmapp.controllers.ECRController`.

    If *data* is provided, it will be used to fill the form.

    *start* is used if *data* is ``None``, it's usefull if you need to show
    several initial creation forms at once and you want different references.

    *inbulk_cache* may be a dictionary to cache lifecycles, groups and other
    values. It is useful if a page renders several creation forms bound to the same
    user
    """
    if data is None:
        initial = get_initial_creation_data(start, inbulk_cache)
        initial.update(kwargs.pop("initial", {}))
        form = ECRForm(initial=initial, **kwargs)
    else:
        form = ECRForm(data=data, **kwargs)

    # do not accept the cancelled lifecycle
    field = form.fields["lifecycle"]
    field.cache_choices = inbulk_cache is not None
    form.inbulk_cache = inbulk_cache
    if inbulk_cache is None or "lifecycles" not in inbulk_cache:
        lifecycles = m.Lifecycle.objects.filter(type=m.Lifecycle.ECR).\
                exclude(pk=m.get_cancelled_lifecycle().pk)
        form.fields["lifecycle"].queryset = lifecycles
        if inbulk_cache is not None:
            inbulk_cache["lifecycles"] = lifecycles
            list(field.choices)
            inbulk_cache["lc_cache"] = field.choice_cache
    else:
        lifecycles = inbulk_cache["lifecycles"]
        form.fields["lifecycle"].queryset = lifecycles
        field.choice_cache = inbulk_cache["lc_cache"]
    return form
