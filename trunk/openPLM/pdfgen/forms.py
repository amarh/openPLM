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
from django.forms.models import modelform_factory, inlineformset_factory, \
        BaseModelFormSet
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from django.utils.functional import memoize

import openPLM.plmapp.models as m

class SelectPdfForm(forms.ModelForm):
    selected = forms.BooleanField(required=False, initial=True)

    class Meta:
        model = m.DocumentFile
        fields = ["document"]       

SelectPdfFormset = inlineformset_factory(m.Document, m.DocumentFile,
        form=SelectPdfForm, extra=0)

def get_pdf_formset(controller, data=None, **kwargs):
    instance = controller
    if hasattr(instance, "object"):
        instance = controller.object
    queryset = instance.files.filter(filename__iendswith=".pdf")
    formset = SelectPdfFormset(data=data, queryset=queryset,
            instance=instance, **kwargs)
    return formset
