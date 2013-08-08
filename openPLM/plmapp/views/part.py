#-!- coding:utf-8 -!-

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

from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import openPLM.plmapp.models as models
import openPLM.plmapp.forms as forms
from openPLM.plmapp.utils.archive import ARCHIVE_FORMATS
from openPLM.plmapp.views.base import (get_obj_from_form, handle_errors, get_generic_data, get_id_card_data, get_obj_by_id)
from openPLM.plmapp.decomposers.base import DecomposersManager
from openPLM.plmapp.utils import r2r


@handle_errors
def display_children(request, obj_type, obj_ref, obj_revi):
    """
    BOM view.

    That view displays the children of the selected object that must be a part.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/bom-child/`

    .. include:: views_params.txt

    **Template:**

    :file:`parts/bom.html`

    **Context:**

    ``RequestContext``

    ``children``
        a list of :class:`.Child`

    ``display_form``
        a :class:`.DisplayChildrenForm`

    ``extra_columns``
        a list of extra columns that are displayed

    ``extension_data``

    ``decomposition_msg``
        a html message to decompose the part (may be empty)

    ``decomposable_children``
        a set of child part ids that are decomposable
    """
    if "diff" in request.GET:
        query = request.GET.urlencode() + "&compact=on"
        return HttpResponseRedirect("%sdiff/?%s" % (request.path, query))
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    if not hasattr(obj, "get_children"):
        return HttpResponseBadRequest("object must be a part")
    date = None
    level = "first"
    state = "all"
    show_documents = show_alternates = False
    if request.GET:
        display_form = forms.DisplayChildrenForm(request.GET)
        if display_form.is_valid():
            date = display_form.cleaned_data["date"]
            level = display_form.cleaned_data["level"]
            state = display_form.cleaned_data["state"]
            show_documents = display_form.cleaned_data["show_documents"]
            show_alternates = display_form.cleaned_data["show_alternates"]
    else:
        display_form = forms.DisplayChildrenForm(initial={"date" : timezone.now(),
            "level" : "first", "state":"all"})
    ctx.update(obj.get_bom(date, level, state, show_documents, show_alternates))
    # decomposition
    if DecomposersManager.count() > 0:
        children_ids = (c.link.child_id for c in ctx["children"])
        decomposable_children = DecomposersManager.get_decomposable_parts(children_ids)
        decomposition_msg = DecomposersManager.get_decomposition_message(obj)
    else:
        decomposition_msg = ""
        decomposable_children = []
    ctx.update({'current_page' : 'BOM-child',
                'decomposition_msg' : decomposition_msg,
                'decomposable_children' : decomposable_children,
                "display_form" : display_form,
                })
    return r2r('parts/bom.html', ctx, request)


@handle_errors(undo="..")
def edit_children(request, obj_type, obj_ref, obj_revi):
    """
    View to edit a BOM.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/bom-child/edit/`

    .. include:: views_params.txt

    **Template:**

    :file:`parts/bom_edit.html`

    **Context:**

    ``RequestContext``

    ``children_formset``
        a formset to edit the BOM

    ``extra_columns``
        a list of extra columns that are displayed

    ``extra_fields``
        a list of extra fields that are editable

    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    if not hasattr(obj, "get_children"):
        return HttpResponseBadRequest("object must be a part")
    if request.method == "POST":
        formset = forms.get_children_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_children(formset)
            return HttpResponseRedirect("..")
    else:
        formset = forms.get_children_formset(obj)
    extra_columns = []
    extra_fields = []
    for PCLE in models.get_PCLEs(obj.object):
        fields = PCLE.get_visible_fields()
        if fields:
            extra_columns.extend((f, PCLE._meta.get_field(f).verbose_name)
                    for f in fields)
            prefix = PCLE._meta.module_name
            extra_fields.extend('%s_%s' % (prefix, f) for f in fields)
    ctx.update({'current_page':'BOM-child',
                'extra_columns' : extra_columns,
                'extra_fields' : extra_fields,
                'children_formset': formset, })
    return r2r('parts/bom_edit.html', ctx, request)


@handle_errors(undo="../..")
def replace_child(request, obj_type, obj_ref, obj_revi, link_id):
    """
    View to replace a child by another one.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/bom-child/replace/{link_id}/`

    .. include:: views_params.txt
    :param link_id: id of the :class:`.ParentChildLink` being replaced

    **Template:**

    :file:`parts/bom_replace.html`

    **Context:**

    ``RequestContext``

    ``replace_child_form``
        a form to select the replacement part

    ``link``
        :class:`.ParentChildLink` being replaced

    ``link_creation``
        Set to True

    ``attach``
        set to (*obj*, "add_child")
    """
    link_id = int(link_id)
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi,
            load_all=True)
    link = models.ParentChildLink.objects.get(id=link_id)
    if request.method == "POST":
        form = forms.AddPartForm(request.POST)
        if form.is_valid():
            obj.replace_child(link, get_obj_from_form(form, request.user))
            return HttpResponseRedirect("../..")
    else:
        form = forms.AddPartForm()
    if ctx["results"]:
        obj.precompute_can_add_child2()
    ctx["replace_child_form"] = form
    ctx["link"] = link
    ctx["attach"] = (obj, "add_child")
    ctx["link_creation"] = True
    return r2r("parts/bom_replace.html", ctx, request)


@handle_errors
def add_child(request, obj_type, obj_ref, obj_revi):
    """
    View to add a child to a part.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/bom-child/add/`

    .. include:: views_params.txt

    **Template:**

    :file:`parts/bom_add.html`

    **Context:**

    ``RequestContext``

    ``add_child_form``
        a form to add a child (:class:`.AddChildForm`)

    ``link``
        :class:`.ParentChildLink` being replaced

    ``link_creation``
        Set to True

    ``attach``
        set to (*obj*, "add_child")

    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi,
            load_all=True)

    if request.method == "POST" and request.POST:
        add_child_form = forms.AddChildForm(obj.object, request.POST)
        if add_child_form.is_valid():
            child_obj = get_obj_from_form(add_child_form, request.user)
            obj.add_child(child_obj,
                          add_child_form.cleaned_data["quantity"],
                          add_child_form.cleaned_data["order"],
                          add_child_form.cleaned_data["unit"],
                          **add_child_form.extensions)
            return HttpResponseRedirect(obj.plmobject_url + "BOM-child/")
    else:
        if "type" in request.GET and request.GET["type"] in models.get_all_parts():
            # use GET params only if they seems valid
            initial = request.GET
        else:
            initial = None
        add_child_form = forms.AddChildForm(obj.object, initial=initial)
        ctx['current_page'] = 'BOM-child'
    if ctx["results"]:
        obj.precompute_can_add_child2()
        orders = list(obj.parentchildlink_parent.values_list('order', flat=True))
        initial_order = max(orders) + 10 if orders else 10
        ctx['order'] = initial_order
    ctx.update({'link_creation': True,
                'add_child_form': add_child_form,
                'attach' : (obj, "add_child")})
    return r2r('parts/bom_add.html', ctx, request)


def compare_bom(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if not hasattr(obj, "get_children"):
        return HttpResponseBadRequest("object must be a part")
    date = date2 = None
    level = "first"
    state = "all"
    show_documents = show_alternates = False
    compact = True
    now = timezone.now()
    if request.GET:
        cmp_form = forms.CompareBOMForm(request.GET)
        if cmp_form.is_valid():
            date = cmp_form.cleaned_data["date"]
            date2 = cmp_form.cleaned_data["date2"]
            level = cmp_form.cleaned_data["level"]
            state = cmp_form.cleaned_data["state"]
            show_documents = cmp_form.cleaned_data["show_documents"]
            show_alternates = cmp_form.cleaned_data["show_documents"]
            compact = cmp_form.cleaned_data.get("compact", compact)
    else:
        initial = {"date" : now, "date2" : now, "level" : "first",
            "state" : "all", "compact" : compact, }
        cmp_form = forms.CompareBOMForm(initial=initial)
    ctx.update(obj.cmp_bom(date, date2, level, state, show_documents, show_alternates))
    ctx.update({'current_page' : 'BOM-child',
                "cmp_form" : cmp_form,
                'compact' : compact,
                'date1' : date or now,
                'date2' : date2 or now,
                })
    return r2r('parts/bom_diff.html', ctx, request)


@handle_errors
def display_parents(request, obj_type, obj_ref, obj_revi):
    """
    Parents view.

    That view displays the parents of the selected object that must be a part.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/parents/`

    .. include:: views_params.txt

    **Template:**

    :file:`parts/parents.html`

    **Context:**

    ``RequestContext``

    ``parents``
        a list of :class:`.Parents`

    ``display_form``
        a :class:`.DisplayChildrenForm`

    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    if not hasattr(obj, "get_parents"):
        return HttpResponseBadRequest("object must be a part")
    date = None
    level = "first"
    state = "all"
    if request.GET:
        display_form = forms.DisplayChildrenForm(request.GET)
        if display_form.is_valid():
            date = display_form.cleaned_data["date"]
            level = display_form.cleaned_data["level"]
            state = display_form.cleaned_data["state"]
    else:
        display_form = forms.DisplayChildrenForm(initial=dict(date=timezone.now(),
            level="first", state="all"))
    # FIXME: show attached documents if asked
    del display_form.fields["show_documents"]
    max_level = 1 if level == "first" else -1
    only_official = state == "official"
    parents = obj.get_parents(max_level, date=date, only_official=only_official)
    ids = set([obj.id])
    if level == "last" and parents:
        previous_level = 0
        max_parents = []
        for c in parents:
            if max_parents and c.level > previous_level:
                del max_parents[-1]
            max_parents.append(c)
            previous_level = c.level
        parents = max_parents
    for level, link in parents:
        ids.add(link.parent_id)

    states = models.StateHistory.objects.at(date).filter(plmobject__in=ids)
    if only_official:
        states = states.officials()
    states = dict(states.values_list("plmobject", "state"))

    ctx.update({'current_page':'parents',
                'parents' :  parents,
                'display_form' : display_form,
                'states' : states,
                })
    return r2r('parts/parents.html', ctx, request)


@handle_errors
def alternates(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    ctx.update({
        "current_page" : "alternates",
        "alternates" : obj.get_alternates(),
    })
    return r2r('parts/alternates.html', ctx, request)


@handle_errors
def add_alternate(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if request.POST:
        add_part_form = forms.AddPartForm(request.POST)
        if add_part_form.is_valid():
            part_obj = get_obj_from_form(add_part_form, request.user)
            obj.add_alternate(part_obj)
            return HttpResponseRedirect(obj.plmobject_url + "alternates/")
    else:
        add_part_form = forms.AddPartForm()
    ctx.update({'link_creation': True,
                'add_part_form': add_part_form,
                'attach' : (obj, "add_alternate") })
    return r2r('parts/alternates_add.html', ctx, request)


@handle_errors
def delete_alternate(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if request.POST:
        obj.delete_alternate(obj.object)
    return HttpResponseRedirect(obj.plmobject_url + "alternates/")


@handle_errors
def display_doc_cad(request, obj_type, obj_ref, obj_revi):
    """
    Attached documents view.

    That view displays the documents attached to the selected object that must be a part.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/doc-cad/`

    .. include:: views_params.txt

    **Template:**

    :file:`parts/doccad.html`

    **Context:**

    ``RequestContext``

    ``documents``
        a queryset of :class:`.DocumentPartLink` bound to the part

    ``archive_formats``
        list of available archive formats

    ``docs_formset``
        a formset to detach documents

    ``forms``
        a dictionary (link_id -> form) to get the form related to a link
        (a document may not be "detachable")

    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    if not hasattr(obj, "get_attached_documents"):
        return HttpResponseBadRequest("object must be a part")
    if request.method == "POST":
        formset = forms.get_doc_cad_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_doc_cad(formset)
            return HttpResponseRedirect(".")
    else:
        formset = forms.get_doc_cad_formset(obj)
    dforms = dict((form.instance.id, form) for form in formset.forms)
    documents = obj.get_attached_documents()
    ctx.update({'current_page':'doc-cad',
                'documents': documents,
                'forms' : dforms,
                'archive_formats' : ARCHIVE_FORMATS,
                'docs_formset': formset,
    })
    ctx.update(get_id_card_data([d.document.id for d in documents]))
    return r2r('parts/doccad.html', ctx, request)


@handle_errors
def add_doc_cad(request, obj_type, obj_ref, obj_revi):
    """
    View to attach a document to a part.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/doc-cad/add/`

    .. include:: views_params.txt

    **Template:**

    :file:`parts/doccad_add.html`

    **Context:**

    ``RequestContext``

    ``add_doc_cad_form``
        a form to attach a document (:class:`.AddDocCadForm`)

    ``link_creation``
        Set to True

    ``attach``
        set to (*obj*, "attach_doc")
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    if request.POST:
        add_doc_cad_form = forms.AddDocCadForm(request.POST)
        if add_doc_cad_form.is_valid():
            doc_cad_obj = get_obj_from_form(add_doc_cad_form, request.user)
            obj.attach_to_document(doc_cad_obj)
            return HttpResponseRedirect(obj.plmobject_url + "doc-cad/")
    else:
        add_doc_cad_form = forms.AddDocCadForm()
    ctx.update({'link_creation': True,
                'add_doc_cad_form': add_doc_cad_form,
                'attach' : (obj, "attach_doc")})
    return r2r('parts/doccad_add.html', ctx, request)


@handle_errors
def delete_doc_cad(request, obj_type, obj_ref, obj_revi):
    """
    View to detach a document referred by the POST parameter ``plmobject``.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/doc-cad/delete/`

    .. include:: views_params.txt
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    if request.POST:
        doc_id = int(request.POST["plmobject"])
        doc = get_obj_by_id(doc_id, request.user)
        obj.detach_document(doc)
        msg = _("The document {doc.type}/{doc.reference}/{doc.revision} has been detached.")
        messages.info(request, msg.format(doc=doc))
    return HttpResponseRedirect(obj.plmobject_url + "doc-cad/")


