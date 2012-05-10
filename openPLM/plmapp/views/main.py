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
#    Pierre Cosquer : pierre.cosquer@insa-rennes.fr
################################################################################

"""
Introduction
=============

This module contains all views to display html pages.

All URLs are linked with django's standard views or with plmapp view functions hereafter.
Each of them receives an httprequest object.
Then treat data with the help of different controllers and different models.
Then adress a html template with a context dictionnary via an httpresponse.

We have a view for each :class:`PLMObject` or :class:`UserProfile` :func:`menu_items`.
We have some views which allow link creation between 2 instances of :class:`PLMObject` or between
an instance of :class:`PLMObject` and an instance of :class:`UserProfile`.
We have some views for link deletion.
We have some views for link edition.
We have views for :class:`PLMObject` creation and edition.
Finaly we have :func:`navigate` which draw a picture with a central object and its related objects.

"""

import os
import csv
import datetime
import tempfile
import itertools
from operator import attrgetter
from mimetypes import guess_type
from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.forms import HiddenInput
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseServerError, \
                        HttpResponsePermanentRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.utils import simplejson
from django.views.i18n import set_language as dj_set_language
from django.views.decorators.csrf import *

from haystack.views import SearchView

import openPLM.plmapp.csvimport as csvimport
import openPLM.plmapp.models as models
import openPLM.plmapp.forms as forms
from openPLM.plmapp.archive import generate_archive
from openPLM.plmapp.base_views import get_obj, get_obj_from_form, \
    get_obj_by_id, handle_errors, get_generic_data, get_navigate_data, \
    get_creation_view
from openPLM.plmapp.cadformats import is_cad_file
from openPLM.plmapp.controllers import get_controller 
from openPLM.plmapp.decomposers.base import DecomposersManager
from openPLM.plmapp.exceptions import ControllerError, PermissionError
from openPLM.plmapp.utils import level_to_sign_str, get_next_revision

import glob

def r2r(template, dictionary, request):
    """
    Shortcut for:
    
    ::
        
        render_to_response(template, dictionary,
                              context_instance=RequestContext(request))
    """
    return render_to_response(template, dictionary,
                              context_instance=RequestContext(request))


def set_language(request):
    """
    A wrapper arround :func:`django.views.i18n.set_language` that
    stores the language in the user profile.
    """
    response = dj_set_language(request)
    if request.method == "POST" and request.user.is_authenticated():
        language = request.session.get('django_language')
        if language:
            request.user.get_profile().language = language
            request.user.get_profile().save()
    return response

##########################################################################################
###                    Function which manage the html home page                        ###
##########################################################################################

def get_last_edited_objects(user):
    """
    Returns the 5 last objects edited by *user*. It returns a list of the most
    recent history entries associated to these objects.
    """
    histories = []
    plmobjects = []
    r = ("plmobject__id", "plmobject__reference", "plmobject__revision", "plmobject__type")
    qs = user.history_user.order_by("-date", "-pk").select_related("plmobject")
    qs = qs.only("date", "action", "details", *r)
    try:
        h = qs[0]
        histories.append(h)
        plmobjects.append(h.plmobject_id)
        for i in xrange(4):
            h = qs.filter(date__lt=h.date).exclude(plmobject__in=plmobjects)[0]
            histories.append(h)
            plmobjects.append(h.plmobject_id)
    except (models.History.DoesNotExist, IndexError):
        pass # no more histories
    return histories

@handle_errors
def display_home_page(request):
    """
    Home page view.

    :url: :samp:`/home/`
    
    **Template:**
    
    :file:`home.html`

    **Context:**

    ``RequestContext``
 
    ``pending_invitations_owner``
        QuerySet of pending invitations to groups owned by the user

    ``pending_invitations_guest``
        QuerySet of pending invitations to groups that the user can joined

    """
    obj, ctx = get_generic_data(request, "User", request.user.username)
    del ctx["object_menu"]

    pending_invitations_owner = obj.invitation_inv_owner. \
            filter(state=models.Invitation.PENDING).order_by("group__name")
    ctx["pending_invitations_owner"] = pending_invitations_owner
    pending_invitations_guest = obj.invitation_inv_guest. \
            filter(state=models.Invitation.PENDING).order_by("group__name")
    ctx["pending_invitations_guest"] = pending_invitations_guest
    ctx["display_group"] = True

    return r2r("home.html", ctx, request)

#############################################################################################
###All functions which manage the different html pages related to a part, a doc and a user###
#############################################################################################
@handle_errors
def display_object_attributes(request, obj_type, obj_ref, obj_revi):
    """
    Attributes view of the given object.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/attributes/`

    .. include:: views_params.txt 

    **Template:**
    
    :file:`attribute.html`

    **Context:**

    ``RequestContext``
    
    ``object_attributes``
        list of tuples(verbose attribute name, value)
        
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    object_attributes_list = []
    attrs = obj.attributes
    if getattr(settings, "HIDE_EMAILS", False):
        if not ctx["is_owner"]:
            attrs = (attr for attr in attrs if attr != "email")
    for attr in attrs:
        item = obj.get_verbose_name(attr)
        object_attributes_list.append((item, getattr(obj, attr)))
    ctx.update({'current_page' : 'attributes',
                'object_attributes': object_attributes_list})
    return r2r('attributes.html', ctx, request)

##########################################################################################
@handle_errors
def display_object(request, obj_type, obj_ref, obj_revi):
    """
    Generic object view.

    Permanently redirects to the attribute page of the given object if it
    is a part, an user or a group and to the files page if it is a document.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/`
    """
     
    if obj_type in ('User', 'Group'):
        url = u"/%s/%s/attributes/" % (obj_type.lower(), obj_ref)
    else:
        model_cls = models.get_all_plmobjects()[obj_type]
        page = "files" if issubclass(model_cls, models.Document) else "attributes"
        url = u"/object/%s/%s/%s/%s/" % (obj_type, obj_ref, obj_revi, page) 
    return HttpResponsePermanentRedirect(iri_to_uri(url))

##########################################################################################
@handle_errors
def display_object_lifecycle(request, obj_type, obj_ref, obj_revi):
    """
    Lifecycle view of the given object (a part or a document).
  
    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/lifecycle/[apply/]`
    
    .. include:: views_params.txt 
  
    POST requests must have a "demote" or "promote" key and must
    validate the :class:`.ConfirmPasswordForm` form.
    If the form is valid, the object is promoted or demoted according to
    the request.

    **Template:**
    
    :file:`lifecycle.html`

    **Context:**

    ``RequestContext``
    
    ``object_lifecycle``
        List of tuples (state name, *boolean*, signer role). The boolean is
        True if the state name equals to the current state. The signer role
        is a dict {"role" : name of the role, "user__username" : name of the
        signer}

    ``is_signer``
        True if the current user has the permission to promote this object

    ``is_signer_dm``
        True if the current user has the permission to demote this object

    ``password_form``
        A form to ask the user password

    ``cancelled_revisions``
        List of plmobjects that will be cancelled if the object is promoted
    
    ``deprecated_revisions``
        List of plmobjects that will be deprecated if the object is promoted

    ``action``
        Only for unsuccessful POST requests.
        Name of the action ("demote" or "promote") that the user tries to do.
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if request.method == 'POST':
        password_form = forms.ConfirmPasswordForm(request.user, request.POST)
        if password_form.is_valid():
            if "demote" in request.POST:
                obj.demote()
            elif "promote" in request.POST:
                obj.promote()
            return HttpResponseRedirect("..")
        if "demote" in request.POST:
            ctx["action"] = "demote"
        elif "promote" in request.POST:
            ctx["action"] = "promote"
    else: 
        password_form = forms.ConfirmPasswordForm(request.user)
    state = obj.state.name
    object_lifecycle = []
    roles = dict(obj.plmobjectuserlink_plmobject.values_list("role", "user__username"))
    lcs = obj.lifecycle.to_states_list()
    for i, st in enumerate(lcs):
        signer = roles.get(level_to_sign_str(i))
        object_lifecycle.append((st, st == state, signer))
    is_signer = obj.check_permission(obj.get_current_sign_level(), False)
    is_signer_dm = obj.check_permission(obj.get_previous_sign_level(), False)

    # warning if a previous revision will be cancelled/deprecated
    cancelled = []
    deprecated = []
    if is_signer:
        if lcs.next_state(state) == obj.lifecycle.official_state.name:
            for rev in obj.get_previous_revisions():
                if rev.is_official:
                    deprecated.append(rev)
                elif rev.is_draft or rev.is_proposed:
                    cancelled.append(rev)
    ctx["cancelled_revisions"] = cancelled
    ctx["deprecated_revisions"] = deprecated

    ctx.update({'current_page':'lifecycle', 
                'object_lifecycle': object_lifecycle,
                'is_signer' : is_signer, 
                'is_signer_dm' : is_signer_dm,
                'password_form' : password_form,
                })
    return r2r('lifecycle.html', ctx, request)


@handle_errors
def display_object_revisions(request, obj_type, obj_ref, obj_revi):
    """
    View that displays the revisions of the given object (a part or
    a document) and shows a form to make a new revision.
    
    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/revisions/`
    
    .. include:: views_params.txt 

    This view returns the result of :func:`revise_document` 
    if the object is a document and the result of :func:`revise_part`
    if the object is a part.
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    ctx["add_revision_form"] = None
    if obj.is_document:
        return revise_document(obj, ctx, request)
    else:
        return revise_part(obj, ctx, request)

def revise_document(obj, ctx, request):
    """
    View to revise a document.

    :param obj: displayed document
    :type obj: :class:`.DocumentController`
    :param ctx: initial context
    :type ctx: dict
    :param request: riven request
  
    This view can create a new revision of the document, it required
    the following POST parameters:

    :post params:
        revision
            new revision of the document
        a valid :class:`.SelectPartFormset`
            Only required if *confirmation* is True, see below.


    A revised document may be attached to some parts.
    These parts are given by :meth:`.DocumentController.get_suggested_parts`.
    If there is at least one suggested part, a confirmation of which
    parts will be attached to the new document is required.

    **Template:**
    
    :file:`documents/revisions.html`

    **Context:**

    ``RequestContext``

    ``confirmation``
        True if a confirmation is required to revise the document.

    ``revisions``
        list of revisions of the document
    
    ``add_revision_form``
        form to revise the document. Only set if the document is revisable.

    ``part_formset``
        a :class:`.SelectPartFormset` of parts that the new revision
        may be attached to. Only set if *confirmation* is True.
    """
    confirmation = False
    if obj.is_revisable():
        parts = obj.get_suggested_parts()
        confirmation = bool(parts)
       
        if request.method == "POST" and request.POST:
            add_form = forms.AddRevisionForm(request.POST)
            selected_parts = []
            valid_forms = True
            if confirmation:
                part_formset = forms.SelectPartFormset(request.POST)
                if part_formset.is_valid():
                    for form in part_formset.forms:
                        part = form.instance
                        if part not in parts: 
                            # invalid data
                            # an user should not be able to go here if he 
                            # does not write by hand its post request
                            # so we do not need to generate an error message
                            valid_forms = False
                            break
                        if form.cleaned_data["selected"]:
                            selected_parts.append(part)
                else:
                    valid_forms = False
            if add_form.is_valid() and valid_forms:
                obj.revise(add_form.cleaned_data["revision"], selected_parts)
                return HttpResponseRedirect(".")
        else:
            add_form = forms.AddRevisionForm({"revision" : get_next_revision(obj.revision)})
            if confirmation:
                ctx["part_formset"] = forms.SelectPartFormset(queryset=parts)
        ctx["add_revision_form"] = add_form

    ctx["confirmation"] = confirmation
    revisions = obj.get_all_revisions()
    ctx.update({'current_page' : 'revisions',
                'revisions' : revisions,
                })
    return r2r('documents/revisions.html', ctx, request)

def revise_part(obj, ctx, request):
    """ View to revise a part.
    
    :param obj: displayed part
    :type obj: :class:`.PartController`
    :param ctx: initial context
    :type ctx: dict
    :param request: riven request
  
    This view can create a new revision of the part, it required
    the following POST parameters:

    :post params:
        revision
            new revision of the part
        a valid :class:`.SelectParentFormset`
            Only required if *confirmation* is True, see below.
        a valid :class:`.SelectDocumentFormset`
            Only required if *confirmation* is True, see below.
        a valid :class:`.SelectParentFormset`
            Only required if *confirmation* is True, see below.

    A revised part may be attached to some documents.
    These documents are given by :meth:`.PartController.get_suggested_documents`.
    A revised part may also have some children from the original revision.
    A revised part may also replace some parts inside a parent BOM.
    These parents are given by :meth:`.PartController.get_suggested_parents`.

    If there is at least one suggested object, a confirmation is required.

    **Template:**
    
    :file:`parts/revisions.html`

    **Context:**

    ``RequestContext``

    ``confirmation``
        True if a confirmation is required to revise the part.

    ``revisions``
        list of revisions of the part
    
    ``add_revision_form``
        form to revise the part. Only set if the document is revisable.

    ``doc_formset``
        a :class:`.SelectDocmentFormset` of documents that the new revision
        may be attached to. Only set if *confirmation* is True.

    ``children_formset``
        a :class:`.SelectChildFormset` of parts that the new revision
        will be composed of. Only set if *confirmation* is True.
    
    ``parents_formset``
        a :class:`.SelectParentFormset` of parts that the new revision
        will be added to, it will replace the previous revisions
        in the parent's BOM.
        Only set if *confirmation* is True.
    """
    confirmation = False
    if obj.is_revisable():
        children = [c.link for c in obj.get_children(1)]
        parents = obj.get_suggested_parents()
        documents = obj.get_suggested_documents()
        confirmation = bool(children or parents or documents)

        if request.method == "POST" and request.POST:
            add_form = forms.AddRevisionForm(request.POST)
            valid_forms = True
            selected_children = []
            selected_parents = []
            selected_documents = []
            if confirmation:
                # children
                children_formset = forms.SelectChildFormset(request.POST,
                        prefix="children")
                if children_formset.is_valid():
                    for form in children_formset.forms:
                        link = form.cleaned_data["link"]
                        if link not in children: 
                            valid_forms = False
                            break
                        if form.cleaned_data["selected"]:
                            selected_children.append(link)
                else:
                    valid_forms = False
                if valid_forms:
                    # documents
                    doc_formset = forms.SelectDocumentFormset(request.POST,
                            prefix="documents")
                    if doc_formset.is_valid():
                        for form in doc_formset.forms:
                            doc = form.cleaned_data["document"]
                            if doc not in documents: 
                                valid_forms = False
                                break
                            if form.cleaned_data["selected"]:
                                selected_documents.append(doc)
                    else:
                        valid_forms = False
                if valid_forms:
                    # parents
                    parents_formset = forms.SelectParentFormset(request.POST,
                            prefix="parents")
                    if parents_formset.is_valid():
                        for form in parents_formset.forms:
                            parent = form.cleaned_data["new_parent"]
                            link = form.cleaned_data["link"]
                            if (link, parent) not in parents: 
                                valid_forms = False
                                break
                            if form.cleaned_data["selected"]:
                                selected_parents.append((link, parent))
                    else:
                        valid_forms = False
            if add_form.is_valid() and valid_forms:
                obj.revise(add_form.cleaned_data["revision"], selected_children,
                        selected_documents, selected_parents)
                return HttpResponseRedirect(".")
        else:
            add_form = forms.AddRevisionForm({"revision" : get_next_revision(obj.revision)})
            if confirmation:
                initial = [dict(link=link) for link in children]
                ctx["children_formset"] = forms.SelectChildFormset(prefix="children",
                        initial=initial)
                initial = [dict(document=d) for d in documents]
                ctx["doc_formset"] = forms.SelectDocumentFormset(prefix="documents",
                        initial=initial)
                initial = [dict(link=p[0], new_parent=p[1]) for p in parents]
                ctx["parents_formset"] = forms.SelectParentFormset(prefix="parents",
                        initial=initial)

        ctx["add_revision_form"] = add_form

    ctx["confirmation"] = confirmation
    revisions = obj.get_all_revisions()
    ctx.update({'current_page' : 'revisions',
                'revisions' : revisions,
                })
    return r2r('parts/revisions.html', ctx, request)

##########################################################################################
@handle_errors
def display_object_history(request, obj_type, obj_ref, obj_revi):
    """
    History view.
    
    This view displays an history of the selected object and its revisions.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/history/`
    :url: :samp:`/user/{username}/history/`
    :url: :samp:`/group/{group_name}/history/`
    
    .. include:: views_params.txt 

    **Template:**
    
    :file:`attribute.html`

    **Context:**

    ``RequestContext``

    ``object_history``
        list of :class:`.AbstractHistory`

    ``show_revisions``
        True if the template should show the revision of each history row
    
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if hasattr(obj, "get_all_revisions"):
        # display history of all revisions
        objects = [o.id for o in obj.get_all_revisions()]
        history = obj.HISTORY.objects.filter(plmobject__in=objects).order_by('-date')
        history = history.select_related("user", "plmobject__revision")
        ctx["show_revisions"] = True
    else:
        history = obj.HISTORY.objects.filter(plmobject=obj.object).order_by('-date')
        ctx["show_revisions"] = False
        history = history.select_related("user")
    ctx.update({'current_page' : 'history', 
                'object_history' : list(history)})
    return r2r('history.html', ctx, request)

#############################################################################################
###         All functions which manage the different html pages specific to part          ###
#############################################################################################
@handle_errors
def display_object_child(request, obj_type, obj_ref, obj_revi):
    """
    BOM view.
    
    That views displays the children of the selected object that must be a part.
    
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
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_children"):
        # TODO
        raise TypeError()
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
        display_form = forms.DisplayChildrenForm(initial={"date" : datetime.datetime.now(),
            "level" : "first", "state":"all"})
    max_level = 1 if level == "first" else -1
    only_official = state == "official"
    children = obj.get_children(max_level, date=date, only_official=only_official)
    if level == "last" and children:
        maximum = max(children, key=attrgetter("level")).level
        children = (c for c in children if c.level == maximum)
    children = list(children)
    # pcle
    extra_columns = []
    extension_data = defaultdict(dict)
    for PCLE in models.get_PCLEs(obj.object):
        fields = PCLE.get_visible_fields()
        if fields:
            extra_columns.extend((f, PCLE._meta.get_field(f).verbose_name) 
                    for f in fields)
            pcles = PCLE.objects.filter(link__in=(c.link.id for c in children))
            pcles = pcles.values("link_id", *fields)
            for pcle in pcles:
                extension_data[pcle["link_id"]].update(pcle)
    # decomposition
    if DecomposersManager.count() > 0:
        children_ids = (c.link.child_id for c in children)
        decomposable_children = DecomposersManager.get_decomposable_parts(children_ids)
        decomposition_msg = DecomposersManager.get_decomposition_message(obj)
    else:
        decomposition_msg = ""
        decomposable_children = []
    ctx.update({'current_page' : 'BOM-child',
                'children' : children,
                'extra_columns' : extra_columns,
                'extension_data' : extension_data,
                'decomposition_msg' : decomposition_msg,
                'decomposable_children' : decomposable_children,
                "display_form" : display_form, })
    return r2r('parts/bom.html', ctx, request)

##########################################################################################
@handle_errors(undo="..")
def edit_children(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which edits the chidren of the selected object.
    Possibility to modify the `.ParentChildLink.order`, the `.ParentChildLink.quantity` and to
    desactivate the `.ParentChildLink`
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_children"):
        # TODO
        raise TypeError()
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

##########################################################################################    
@handle_errors
def add_children(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for chidren creation of the selected object.
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if request.POST:
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
        add_child_form = forms.AddChildForm(obj.object)
        ctx['current_page'] = 'BOM-child'
    ctx.update({'link_creation': True,
                'add_child_form': add_child_form,
                'attach' : (obj, "add_child")})
    return r2r('parts/bom_add.html', ctx, request)
    
##########################################################################################    
@handle_errors
def display_object_parents(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the parent of the selected object.
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_parents"):
        # TODO
        raise TypeError()
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
        display_form = forms.DisplayChildrenForm(initial={"date" : datetime.datetime.now(),
            "level" : "first", "state" : "all"})
    max_level = 1 if level == "first" else -1
    only_official = state == "official"
    parents = obj.get_parents(max_level, date=date, only_official=only_official)
    if level == "last" and parents:
        maximum = max(parents, key=attrgetter("level")).level
        parents = (c for c in parents if c.level == maximum)
    ctx.update({'current_page':'parents',
                'parents' :  parents,
                'display_form' : display_form, })
    return r2r('parts/parents.html', ctx, request)

##########################################################################################
@handle_errors
def display_object_doc_cad(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the related documents and CAD of 
    the selected object.
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_attached_documents"):
        # TODO
        raise TypeError()
    if request.method == "POST":
        formset = forms.get_doc_cad_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_doc_cad(formset)
            return HttpResponseRedirect(".")
    else:
        formset = forms.get_doc_cad_formset(obj)
    dforms = dict((form.instance.id, form) for form in formset.forms)
    archive_form = forms.ArchiveForm()
    ctx.update({'current_page':'doc-cad',
                'all_docs': obj.get_attached_documents(),
                'forms' : dforms,
                'archive_form' : archive_form,
                'docs_formset': formset})
    return r2r('parts/doccad.html', ctx, request)


##########################################################################################    
@handle_errors
def add_doc_cad(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for link creation (:class:`DocumentPartLink` link) between the selected object and some documents or CAD.
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
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
    
#############################################################################################
###      All functions which manage the different html pages specific to documents        ###
#############################################################################################
@handle_errors
def display_related_part(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the related part of (:class:`DocumentPartLink` with) the selected object.
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_attached_parts"):
        # TODO
        raise TypeError()
    if request.method == "POST":
        formset = forms.get_rel_part_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_rel_part(formset)
            return HttpResponseRedirect(".")
    else:
        formset = forms.get_rel_part_formset(obj)
    rforms = dict((form.instance.id, form) for form in formset.forms)

    ctx.update({'current_page':'parts', 
                'all_parts': obj.get_attached_parts(),
                'forms' : rforms,
                'parts_formset': formset})
    return r2r('documents/parts.html', ctx, request)

##########################################################################################    
@handle_errors
def add_rel_part(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for link creation (:class:`DocumentPartLink` link) between the selected object and some parts.
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if request.POST:
        add_rel_part_form = forms.AddRelPartForm(request.POST)
        if add_rel_part_form.is_valid():
            part_obj = get_obj_from_form(add_rel_part_form, request.user)
            obj.attach_to_part(part_obj)
            ctx.update({'add_rel_part_form': add_rel_part_form, })
            return HttpResponseRedirect(obj.plmobject_url + "parts/")
    else:
        add_rel_part_form = forms.AddRelPartForm()
    ctx.update({'link_creation': True,
                'add_rel_part_form': add_rel_part_form,
                'attach' : (obj, "attach_part") })
    return r2r('documents/parts_add.html', ctx, request)

##########################################################################################
@handle_errors
def display_files(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the files (:class:`DocumentFile`) uploaded in the selected object.
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    if not hasattr(obj, "files"):
        raise TypeError()
    if request.method == "POST":
        formset = forms.get_file_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_file(formset)
            return HttpResponseRedirect(".")
    else:
        formset = forms.get_file_formset(obj)

    archive_form = forms.ArchiveForm()
    
    ctx.update({'current_page':'files', 
                'file_formset': formset,
                'archive_form' : archive_form,
                'deprecated_files' : obj.deprecated_files,
               })
    return r2r('documents/files.html', ctx, request)

##########################################################################################
@handle_errors(undo="..")
#@csrf_protect
def add_file(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for the files (:class:`DocumentFile`) addition in the selected object.
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if request.method == "POST":
        add_file_form = forms.AddFileForm(request.POST, request.FILES)
        if add_file_form.is_valid():
            obj.add_file(request.FILES["filename"])
            ctx.update({'add_file_form': add_file_form, })
            return HttpResponseRedirect(".")
    else:
        add_file_form = forms.AddFileForm()
    ctx.update({ 'add_file_form': add_file_form, })
    return r2r('documents/files_add.html', ctx, request)

##########################################################################################
@handle_errors
@csrf_protect
def up_progress(request, obj_type, obj_ref, obj_revi):
    """
    Show upload progress for a given path
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    ret = ""
    #if 'f_path' in request.GET:
    #f_path=request.GET['f_path']
    f = glob.glob("/tmp/*upload")
    ret = str(os.path.getsize(f[0]))
    if ret==request.GET['f_size']:
	ret += ":linking"
    else:
	ret += ":writing"
    return HttpResponse(ret)



#############################################################################################
###    All functions which manage the different html pages specific to part and document  ###
#############################################################################################
@handle_errors
def display_management(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the Users who manage the selected object (:class:`PLMObjectUserLink`).
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    object_management_list = models.PLMObjectUserLink.objects.filter(plmobject=obj)
    object_management_list = object_management_list.order_by("role")
    if not ctx["is_owner"]:
        link = object_management_list.filter(role="notified", user=request.user)
        ctx["is_notified"] = bool(link)
        if link:
            ctx["remove_notify_link"] = link[0]
        else:
            initial = { "type" : "User",
                        "username" : request.user.username
                      }
            form = forms.SelectUserForm(initial=initial)
            for field in ("type", "username"):
                form.fields[field].widget = HiddenInput() 
            ctx["notify_self_form"] = form
    ctx.update({'current_page':'management',
                'object_management': object_management_list})
    
    return r2r('management.html', ctx, request)

##########################################################################################
@handle_errors(undo="../..")
def replace_management(request, obj_type, obj_ref, obj_revi, link_id):
    """
    Manage html page for the modification of the Users who manage the selected object (:class:`PLMObjectUserLink`).
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    :param link_id: :attr:`.PLMObjectUserLink.id`
    :type link_id: str
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    link = models.PLMObjectUserLink.objects.get(id=int(link_id))
    if obj.object.id != link.plmobject.id:
        raise ValueError("Bad link id")
    
    if request.method == "POST":
        replace_management_form = forms.SelectUserForm(request.POST)
        if replace_management_form.is_valid():
            if replace_management_form.cleaned_data["type"] == "User":
                user_obj = get_obj_from_form(replace_management_form, request.user)
                obj.set_role(user_obj.object, link.role)
                if link.role == 'notified':
                    obj.remove_notified(link.user)
            return HttpResponseRedirect("../..")
    else:
        replace_management_form = forms.SelectUserForm()
    
    ctx.update({'current_page':'management', 
                'replace_management_form': replace_management_form,
                'link_creation': True,
                'attach' : (obj, "delegate")})
    return r2r('management_replace.html', ctx, request)

##########################################################################################    
@handle_errors(undo="../..")
def add_management(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for the addition of a "notification" link
    (:class:`PLMObjectUserLink`) between some Users and the selected object. 
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if request.method == "POST":
        add_management_form = forms.SelectUserForm(request.POST)
        if add_management_form.is_valid():
            if add_management_form.cleaned_data["type"] == "User":
                user_obj = get_obj_from_form(add_management_form, request.user)
                obj.set_role(user_obj.object, "notified")
            return HttpResponseRedirect("..")
    else:
        add_management_form = forms.SelectUserForm()
    
    ctx.update({'current_page':'management', 
                'replace_management_form': add_management_form,
                'link_creation': True,
                "attach" : (obj, "delegate")})
    return r2r('management_replace.html', ctx, request)

##########################################################################################    
@handle_errors
def delete_management(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for the deletion of a "notification" link (:class:`PLMObjectUserLink`) between some Users and the selected object.
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    """
    obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
    if request.method == "POST":
        try:
            link_id = request.POST["link_id"]
            link = models.PLMObjectUserLink.objects.get(id=int(link_id))
            obj.remove_notified(link.user)
        except (KeyError, ValueError, ControllerError):
            return HttpResponseForbidden()
    return HttpResponseRedirect("../")

##########################################################################################
###    Manage html pages for part / document creation and modification                 ###
##########################################################################################

@handle_errors
def create_object(request, from_registered_view=False, creation_form=None):
    """
    Manage html page for the creation of an instance of `models.PLMObject` subclass.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :return: a :class:`django.http.HttpResponse`
    """

    obj, ctx = get_generic_data(request)
    Form = forms.TypeFormWithoutUser
    # it is possible that the created object must be attached to a part
    # or a document
    # related_doc and related_part should be a plmobject id
    # If the related_doc/part is not a doc/part, we let python raise
    # an AttributeError, since an user should not play with the URL
    # and openPLM must be smart enough to produce valid URLs
    attach = related = None
    if "related_doc" in request.REQUEST:
        Form = forms.PartTypeForm
        doc = get_obj_by_id(int(request.REQUEST["related_doc"]), request.user)
        attach = doc.attach_to_part
        ctx["related_doc"] = request.REQUEST["related_doc"]
        related = ctx["related"] = doc
    elif "related_part" in request.REQUEST:
        Form = forms.DocumentTypeForm
        part = get_obj_by_id(int(request.REQUEST["related_part"]), request.user)
        attach = part.attach_to_document
        ctx["related_part"] = request.REQUEST["related_part"]
        related = ctx["related"] = part
    if "__next__" in request.REQUEST:
        redirect_to = request.REQUEST["__next__"]
        ctx["next"] = redirect_to
    else:
        # will redirect to the created object
        redirect_to = None

    type_form = Form(request.REQUEST)
    if type_form.is_valid():
        type_ = type_form.cleaned_data["type"]
        cls = models.get_all_plmobjects()[type_]
        if not from_registered_view:
            view = get_creation_view(cls)
            if view is not None:
                # view has been registered to create an object of type 'cls'
                return view(request)
    else:
        ctx["creation_type_form"] = type_form
        return r2r('create.html', ctx, request)

    if request.method == 'GET' and creation_form is None:
        creation_form = forms.get_creation_form(request.user, cls)
        if related is not None:
            creation_form.fields["group"].initial = related.group
            creation_form.fields["lifecycle"].initial = related.lifecycle
    elif request.method == 'POST':
        if creation_form is None:
            creation_form = forms.get_creation_form(request.user, cls, request.POST)
        if creation_form.is_valid():
            ctrl_cls = get_controller(type_)
            ctrl = ctrl_cls.create_from_form(creation_form, request.user)
            if attach is not None:
                try:
                    attach(ctrl)
                except (ControllerError, ValueError) as e: 
                    # crtl cannot be attached (maybe the state of the
                    # related object as changed)
                    # alerting the user using the messages framework since
                    # the response is redirected
                    message = _(u"Error: %(details)s") % dict(details=unicode(e))
                    messages.error(request, message)
                    # redirecting to the ctrl page that least its attached
                    # objects
                    if ctrl.is_document:
                        return HttpResponseRedirect(ctrl.plmobject_url + "parts/")
                    else:
                        return HttpResponseRedirect(ctrl.plmobject_url + "doc-cad/")
            return HttpResponseRedirect(redirect_to or ctrl.plmobject_url)
    ctx.update({
        'creation_form' : creation_form,
        'object_type' : type_,
        'creation_type_form' : type_form,
    })
    return r2r('create.html', ctx, request)

##########################################################################################
@handle_errors(undo="../attributes/")
def modify_object(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for the modification of the selected object.
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    cls = models.get_all_plmobjects()[obj_type]
    if request.method == 'POST' and request.POST:
        modification_form = forms.get_modification_form(cls, request.POST)
        if modification_form.is_valid():
            obj.update_from_form(modification_form)
            return HttpResponseRedirect(obj.plmobject_url + "attributes/")
    else:
        modification_form = forms.get_modification_form(cls, instance=obj.object)
    
    ctx['modification_form'] = modification_form
    return r2r('edit.html', ctx, request)

#############################################################################################
###         All functions which manage the different html pages specific to user          ###
#############################################################################################
@handle_errors
def modify_user(request, obj_ref):
    """
    Manage html page for the modification of the selected
    :class:`~django.contrib.auth.models.User`.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :class:`~django.contrib.auth.models.User`
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx = get_generic_data(request, "User", obj_ref)
    if obj.object != request.user:
        raise PermissionError("You are not the user")
    class_for_div="ActiveBox4User"
    if request.method == 'POST' and request.POST:
        modification_form = forms.OpenPLMUserChangeForm(request.POST)
        if modification_form.is_valid():
            obj.update_from_form(modification_form)
            return HttpResponseRedirect("/user/%s/" % obj.username)
    else:
        modification_form = forms.OpenPLMUserChangeForm(instance=obj.object)
    
    ctx.update({'class4div': class_for_div, 'modification_form': modification_form})
    return r2r('edit.html', ctx, request)
    
##########################################################################################
@handle_errors
def change_user_password(request, obj_ref):
    """
    Manage html page for the modification of the selected
    :class:`~django.contrib.auth.models.User` password.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_ref: :attr:`~django.contrib.auth.models.User.username`
    :return: a :class:`django.http.HttpResponse`
    """
    if request.user.username=='test':
        return HttpResponseRedirect("/user/%s/attributes/" % request.user)
    obj, ctx = get_generic_data(request, "User", obj_ref)
    if obj.object != request.user:
        raise PermissionError("You are not the user")

    if request.method == 'POST' and request.POST:
        modification_form = PasswordChangeForm(obj, request.POST)
        if modification_form.is_valid():
            obj.set_password(modification_form.cleaned_data['new_password2'])
            obj.save()
            return HttpResponseRedirect("/user/%s/" % obj.username)
    else:
        modification_form = PasswordChangeForm(obj)
    
    ctx.update({'class4div': "ActiveBox4User",
                'modification_form': modification_form})
    return r2r('users/password.html', ctx, request)

#############################################################################################
@handle_errors
def display_related_plmobject(request, obj_type, obj_ref, obj_revi):
    """
    View listing the related parts and documents of
    the selected :class:`~django.contrib.auth.models.User`.
    
    .. include:: views_params.txt 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_object_user_links"):
        # TODO
        raise TypeError()
    objs = obj.get_object_user_links().select_related("plmobject")
    objs = objs.values("role", "plmobject__type", "plmobject__reference",
            "plmobject__revision", "plmobject__name")
    ctx.update({'current_page':'parts-doc-cad',
        'object_user_link': objs,
        'last_edited_objects':  get_last_edited_objects(obj.object),
    })
    return r2r('users/plmobjects.html', ctx, request)

#############################################################################################
@handle_errors
def display_delegation(request, obj_ref):
    """
    Manage html page which displays the delegations of the selected 
    :class:`~django.contrib.auth.models.User`.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_ref: :attr:`~django.contrib.auth.models.User.username`
    :type obj_ref: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx = get_generic_data(request, "User", obj_ref)
    
    if not hasattr(obj, "get_user_delegation_links"):
        # TODO
        raise TypeError()
    if request.method == "POST":
        selected_link_id = request.POST.get('link_id')
        obj.remove_delegation(models.DelegationLink.objects.get(pk=int(selected_link_id)))
    links = obj.get_user_delegation_links().select_related("delegatee")
    ctx.update({'current_page':'delegation', 
                'user_delegation_link': links})
    
    return r2r('users/delegation.html', ctx, request)


##########################################################################################    
@handle_errors(undo="../../..")
def delegate(request, obj_ref, role, sign_level):
    """
    Manage html page for delegations modification of the selected
    :class:`~django.contrib.auth.models.User`.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :class:`~django.contrib.auth.models.User`
    :type obj_ref: str
    :param role: :attr:`.DelegationLink.role` if role is not "sign"
    :type role: str
    :param sign_level: used for :attr:`.DelegationLink.role` if role is "sign"
    :type sign_level: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx = get_generic_data(request, "User", obj_ref)
    
    if request.method == "POST":
        delegation_form = forms.SelectUserForm(request.POST)
        if delegation_form.is_valid():
            if delegation_form.cleaned_data["type"] == "User":
                user_obj = get_obj_from_form(delegation_form, request.user)
                if role == "notified" or role == "owner":
                    obj.delegate(user_obj.object, role)
                    return HttpResponseRedirect("../..")
                elif role == "sign":
                    if sign_level == "all":
                        obj.delegate(user_obj.object, "sign*")
                        return HttpResponseRedirect("../../..")
                    elif sign_level.isdigit():
                        obj.delegate(user_obj.object, level_to_sign_str(int(sign_level)-1))
                        return HttpResponseRedirect("../../..")
    else:
        delegation_form = forms.SelectUserForm()
    if role == 'sign':
        if sign_level.isdigit():
            role = _("signer level") + " " + str(sign_level)
        else:
            role = _("signer all levels")
    elif role == "notified":
        role = _("notified")
    
    ctx.update({'current_page':'delegation',
                'replace_management_form': delegation_form,
                'link_creation': True,
                'attach' : (obj, "delegate"),
                'role': role})
    return r2r('management_replace.html', ctx, request)
    
    
##########################################################################################
###             Manage html pages for file check-in / check-out / download             ###
##########################################################################################    
@handle_errors
def checkin_file(request, obj_type, obj_ref, obj_revi, file_id_value):
    """
    Manage html page for the files (:class:`DocumentFile`) checkin in the selected object.
    It computes a context dictionnary based on
    
    .. include:: views_params.txt 
    :param file_id_value: :attr:`.DocumentFile.id`
    :type file_id_value: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if request.POST:
        checkin_file_form = forms.AddFileForm(request.POST, request.FILES)
        if checkin_file_form.is_valid():
            obj.checkin(models.DocumentFile.objects.get(id=file_id_value),
                        request.FILES["filename"])
            return HttpResponseRedirect(obj.plmobject_url + "files/")
    else:
        checkin_file_form = forms.AddFileForm()
    ctx['add_file_form'] =  checkin_file_form
    return r2r('documents/files_add.html', ctx, request)

##########################################################################################
@handle_errors 
def download(request, docfile_id, filename=""):
    """
    View to download a document file.
    
    :param request: :class:`django.http.QueryDict`
    :param docfile_id: :attr:`.DocumentFile.id`
    :type docfile_id: str
    :return: a :class:`django.http.HttpResponse`
    """
    doc_file = models.DocumentFile.objects.get(id=docfile_id)
    ctrl = get_obj_by_id(int(doc_file.document.id), request.user)
    ctrl.check_readable()
    name = doc_file.filename.encode("utf-8", "ignore")
    mimetype = guess_type(name, False)[0]
    if not mimetype:
        mimetype = 'application/octet-stream'
    f, size = ctrl.get_content_and_size(doc_file)
    response = HttpResponse(f, mimetype=mimetype)
    response["Content-Length"] = size
    if not filename:
        response['Content-Disposition'] = 'attachment; filename="%s"' % name
    return response

def get_cad_files(part):
    """
    Returns an iterable of all :class:`.DocumentFile` related
    to *part* that contains a CAD file. It retrieves all non deprecated
    files of all documents parts to *part* and its children and
    filters these files according to their extension (see :meth:`.is_cad_file`).
    """
    children = part.get_children(-1, related=("child",))
    children_ids = set(c.link.child_id for c in children)
    children_ids.add(part.id)
    links = models.DocumentPartLink.objects.filter(part__in=children_ids)
    docs = links.values_list("document", flat=True)
    d_o_u = "document__owner__username"
    files = models.DocumentFile.objects.filter(deprecated=False,
                document__in=set(docs))
    # XXX : maybe its faster to build a complex query than retrieving
    # each file and testing their extension
    return (df for df in files.select_related(d_o_u) if is_cad_file(df.filename))


@handle_errors 
def download_archive(request, obj_type, obj_ref, obj_revi):
    """
    View to download all files from a document/part.

    .. include:: views_params.txt 
    """

    obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
    obj.check_readable()
    
    d_o_u = "document__owner__username"
    if obj.is_document:
        files = obj.files.select_related(d_o_u)
    elif obj.is_part and "cad" in request.GET:
        files = get_cad_files(obj)
    elif obj.is_part:
        links = obj.get_attached_documents()
        docs = (link.document for link in links)
        files = itertools.chain(*(doc.files.select_related(d_o_u)
            for doc in docs))
    else:
        return HttpResponseForbidden()

    form = forms.ArchiveForm(request.GET)
    if form.is_valid():
        format = form.cleaned_data["format"]
        name = "%s_%s.%s" % (obj_ref, obj_revi, format)
        mimetype = guess_type(name, False)[0]
        if not mimetype:
            mimetype = 'application/octet-stream'
        content = generate_archive(files, format)
        response = HttpResponse(content, mimetype=mimetype)
        #response["Content-Length"] = size
        response['Content-Disposition'] = 'attachment; filename="%s"' % name
        return response
    return HttpResponseForbidden()
##########################################################################################
@handle_errors 
def checkout_file(request, obj_type, obj_ref, obj_revi, docfile_id):
    """
    Manage html page for the files (:class:`DocumentFile`) checkout from the selected object.
    It locks the :class:`DocumentFile` and, after, calls :func:`.views.download`
    
    .. include:: views_params.txt 
    :param docfile_id: :attr:`.DocumentFile.id`
    :type docfile_id_value: str
    """
    obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
    doc_file = models.DocumentFile.objects.get(id=docfile_id)
    obj.lock(doc_file)
    return download(request, docfile_id)

##########################################################################################
###                     Manage html pages for navigate function                        ###
##########################################################################################    
@handle_errors
def navigate(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays a graphical picture the different links
    between :class:`~django.contrib.auth.models.User` and  :class:`.models.PLMObject`.
    This function uses Graphviz (http://graphviz.org/).
    Some filters let user defines which type of links he/she wants to display.
    It computes a context dictionary based on
    
    .. include:: views_params.txt 
    """
    ctx = get_navigate_data(request, obj_type, obj_ref, obj_revi)
    ctx["edges"] = simplejson.dumps(ctx["edges"])
    return r2r('navigate.html', ctx, request)

@handle_errors
def display_users(request, obj_ref):
    obj, ctx = get_generic_data(request, "Group", obj_ref)
    if request.method == "POST":
        formset = forms.get_user_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_users(formset)
            return HttpResponseRedirect(".")
    else:
        formset = forms.get_user_formset(obj)
    ctx["user_formset"] = formset
    ctx["pending_invitations"] = obj.invitation_set.filter(
            state=models.Invitation.PENDING)
    ctx['current_page'] = 'users' 
    ctx['in_group'] = bool(request.user.groups.filter(id=obj.id))
    return r2r("groups/users.html", ctx, request)

@handle_errors
def group_add_user(request, obj_ref):
    """
    View of the *Add user* page of a group.

    """

    obj, ctx = get_generic_data(request, "Group", obj_ref)
    if request.method == "POST":
        form = forms.SelectUserForm(request.POST)
        if form.is_valid():
            obj.add_user(User.objects.get(username=form.cleaned_data["username"]))
            return HttpResponseRedirect("..")
    else:
        form = forms.SelectUserForm()
    ctx["add_user_form"] = form
    ctx['current_page'] = 'users' 
    ctx['link_creation'] = True
    return r2r("groups/add_user.html", ctx, request)

@handle_errors
def group_ask_to_join(request, obj_ref):
    obj, ctx = get_generic_data(request, "Group", obj_ref)
    if request.method == "POST":
        obj.ask_to_join()
        return HttpResponseRedirect("..")
    else:
        form = forms.SelectUserForm()
    ctx["ask_form"] = ""
    ctx['current_page'] = 'users' 
    ctx['in_group'] = bool(request.user.groups.filter(id=obj.id))
    return r2r("groups/ask_to_join.html", ctx, request)

@handle_errors
def display_groups(request, obj_ref):
    """
    View of the *groups* page of an user.

    """

    obj, ctx = get_generic_data(request, "User", obj_ref)
    ctx["groups"] = models.GroupInfo.objects.filter(id__in=obj.groups.all())\
            .order_by("name").values("name", "description")

    ctx['current_page'] = 'groups' 
    return r2r("users/groups.html", ctx, request)

@handle_errors
def sponsor(request, obj_ref):
    """
    View of the *sponsor* page.
    """
    obj, ctx = get_generic_data(request, "User", obj_ref)
    if request.method == "POST":
        form = forms.SponsorForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            obj.sponsor(new_user)
            return HttpResponseRedirect("..")
    else:
        form = forms.SponsorForm(initial={"sponsor":obj.id}, sponsor=obj.id)
    ctx["sponsor_form"] = form
    ctx['current_page'] = 'delegation' 
    return r2r("users/sponsor.html", ctx, request)

@handle_errors
def sponsor_resend_mail(request, obj_ref):
    obj, ctx = get_generic_data(request, "User", obj_ref)
    if request.method == "POST":
        try:
            link_id = request.POST["link_id"]
            link = models.DelegationLink.objects.get(id=int(link_id))
            obj.resend_sponsor_mail(link.delegatee)
        except (KeyError, ValueError, ControllerError) as e:
            return HttpResponseForbidden()
    return HttpResponseRedirect("../../")

@handle_errors
def display_plmobjects(request, obj_ref):
    """
    View of the *objects* page of a group.
    """
    
    obj, ctx = get_generic_data(request, "Group", obj_ref)
    ctx["objects"] = obj.plmobject_group.order_by("type", "reference", "revision")
    ctx['current_page'] = 'objects'
    return r2r("groups/objects.html", ctx, request)

@handle_errors(undo="../../../users/")
def accept_invitation(request, obj_ref, token):
    token = long(token)
    obj, ctx = get_generic_data(request, "Group", obj_ref)
    inv = models.Invitation.objects.get(token=token)
    if request.method == "POST":
        form = forms.InvitationForm(request.POST)
        if form.is_valid() and inv == form.cleaned_data["invitation"]:
            obj.accept_invitation(inv)
            return HttpResponseRedirect("../../../users/")
    else:
        form = forms.InvitationForm(initial={"invitation" : inv})
    ctx["invitation_form"] = form
    ctx['current_page'] = 'users'
    ctx["invitation"] = inv
    return r2r("groups/accept_invitation.html", ctx, request)

 
@handle_errors(undo="../../../users/")
def refuse_invitation(request, obj_ref, token):
    token = long(token)
    obj, ctx = get_generic_data(request, "Group", obj_ref)
    inv = models.Invitation.objects.get(token=token)
    if request.method == "POST":
        form = forms.InvitationForm(request.POST)
        if form.is_valid() and inv == form.cleaned_data["invitation"]:
            obj.refuse_invitation(inv)
            return HttpResponseRedirect("../../../users/")
    else:
        form = forms.InvitationForm(initial={"invitation" : inv})
    ctx["invitation_form"] = form
    ctx["invitation"] = inv
    ctx['current_page'] = 'users'
    return r2r("groups/refuse_invitation.html", ctx, request)

@handle_errors
def send_invitation(request, obj_ref, token):
    """
    Views to (re)send an invitation.

    :param obj_ref: name of the group
    :param token: token that identify the invitation
    """
    token = long(token)
    obj, ctx = get_generic_data(request, "Group", obj_ref)
    inv = models.Invitation.objects.get(token=token)
    if request.method == "POST":
        if inv.guest_asked:
            obj.send_invitation_to_owner(inv)
        else:
            obj.send_invitation_to_guest(inv)
    return HttpResponseRedirect("../../../users/")

@handle_errors(undo="../..")
def import_csv_init(request, target="csv"):
    obj, ctx = get_generic_data(request)
    if request.method == "POST":
        csv_form = forms.CSVForm(request.POST, request.FILES)
        if csv_form.is_valid():
            f = request.FILES["file"]
            prefix = "openplmcsv" + request.user.username
            tmp = tempfile.NamedTemporaryFile(prefix=prefix, delete=False)
            for chunk in f.chunks():
                tmp.write(chunk)
            name = os.path.split(tmp.name)[1][len(prefix):]
            tmp.close()
            encoding = csv_form.cleaned_data["encoding"]
            return HttpResponseRedirect("/import/%s/%s/%s/" % (target, name,
                                        encoding))
    else:
        csv_form = forms.CSVForm()
    ctx["csv_form"] = csv_form
    ctx["step"] = 1
    ctx["target"] = target
    return r2r("import/csv.html", ctx, request)

@handle_errors(undo="../..")
def import_csv_apply(request, target, filename, encoding):
    obj, ctx = get_generic_data(request)
    ctx["encoding_error"] = False
    ctx["io_error"] = False
    Importer = csvimport.IMPORTERS[target]
    Formset = forms.get_headers_formset(Importer)
    try:
        path = os.path.join(tempfile.gettempdir(),
                            "openplmcsv" + request.user.username + filename)
        with open(path, "rb") as csv_file:
            importer = Importer(csv_file, request.user, encoding)
            preview = importer.get_preview()
        if request.method == "POST":
            headers_formset = Formset(request.POST)
            if headers_formset.is_valid():
                headers = headers_formset.headers
                try:
                    with open(path, "rb") as csv_file:
                        importer = Importer(csv_file, request.user, encoding)
                        importer.import_csv(headers)
                except csvimport.CSVImportError as exc:
                    ctx["errors"] = exc.errors.iteritems()
                else:
                    os.remove(path)
                    return HttpResponseRedirect("/import/done/")
        else:
            initial = [{"header": header} for header in preview.guessed_headers]
            headers_formset = Formset(initial=initial)
        ctx.update({
            "preview" :  preview,
            "preview_data" : itertools.izip((f["header"] for f in headers_formset.forms),
                preview.headers, *preview.rows),
            "headers_formset" : headers_formset,
        })
    except UnicodeError:
        ctx["encoding_error"] = True
    except (IOError, csv.Error):
        ctx["io_error"] = True
    ctx["has_critical_error"] = ctx["io_error"] or ctx["encoding_error"] \
            or "errors" in ctx
    ctx["csv_form"] = forms.CSVForm(initial={"encoding" : encoding})
    ctx["step"] = 2
    ctx["target"] = target
    return r2r("import/csv.html", ctx, request)


@handle_errors
def import_csv_done(request):
    obj, ctx = get_generic_data(request)
    return r2r("import/done.html", ctx, request)

class OpenPLMSearchView(SearchView):

    def extra_context(self):
        extra = super(OpenPLMSearchView, self).extra_context()
        obj, ctx = get_generic_data(self.request, search=False)
        ctx["type"] = self.request.session["type"]
        ctx["object_type"] = "Search"
        extra.update(ctx)
        return extra

    def get_query(self):
        query = super(OpenPLMSearchView, self).get_query() or "*"
        self.request.session["search_query"] = query
        return query

    def get_results(self):
        results = super(OpenPLMSearchView, self).get_results()
        # update request.session so that the left panel displays
        # the same results
        self.request.session["results"] = results[:30]
        self.request.session["search_count"] = results.count()
        from haystack import site
        for r in self.request.session.get("results"):
            r.searchsite = site
        self.request.session.save()
        return results

    @method_decorator(handle_errors)
    def __call__(self, request):
        return super(OpenPLMSearchView, self).__call__(request)

