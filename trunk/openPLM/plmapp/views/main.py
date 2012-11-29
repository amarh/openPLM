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

"""
Introduction
=============

This module contains all views to display html pages.

All URLs are linked with django's standard views or with plmapp view functions hereafter.
Each of them receives an httprequest object.
Then treat data with the help of different controllers and different models.
Then adress a html template with a context dictionary via an httpresponse.

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
import glob
import datetime
import tempfile
import itertools
from collections import defaultdict
from mimetypes import guess_type

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.views import redirect_to_login
from django.contrib.comments.views.comments import post_comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import F, Q
from django.forms import HiddenInput
from django.http import (HttpResponseRedirect, HttpResponse, Http404,
                        HttpResponsePermanentRedirect, HttpResponseForbidden,
                        HttpResponseBadRequest)
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.utils import simplejson
from django.views.i18n import set_language as dj_set_language
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from haystack.views import SearchView

import openPLM.plmapp.csvimport as csvimport
import openPLM.plmapp.models as models
import openPLM.plmapp.forms as forms
from openPLM.plmapp.archive import generate_archive
from openPLM.plmapp.base_views import init_ctx, get_obj, get_obj_from_form, \
    get_obj_by_id, handle_errors, get_generic_data, get_navigate_data, \
    get_creation_view, register_creation_view, secure_required
from openPLM.plmapp.controllers import get_controller 
from openPLM.plmapp.decomposers.base import DecomposersManager
from openPLM.plmapp.exceptions import ControllerError, PermissionError
from openPLM.plmapp.utils import level_to_sign_str, get_next_revision
from openPLM.plmapp.filehandlers.progressbarhandler import ProgressBarUploadHandler


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

@handle_errors
def comment_post_wrapper(request):
    # from http://thejaswi.info/tech/blog/2008/11/20/part-2-django-comments-authenticated-users/
    # Clean the request to prevent form spoofing
    user = request.user
    if user.is_authenticated() and not user.get_profile().restricted:
        if not (user.get_full_name() == request.POST['name'] or \
                user.email == request.POST['email']):
            return HttpResponse("You registered user...trying to spoof a form...eh?")
        return post_comment(request)
    return HttpResponse("You anonymous cheater...trying to spoof a form?")

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

@handle_errors(restricted_access=False)
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
    if not obj.restricted:
        # always empty if restricted -> do not hit the database
        pending_invitations_owner = obj.invitation_inv_owner. \
                filter(state=models.Invitation.PENDING).order_by("group__name").\
                select_related("guest", "owner", "group")
        ctx["pending_invitations_owner"] = pending_invitations_owner
        pending_invitations_guest = obj.invitation_inv_guest. \
                filter(state=models.Invitation.PENDING).order_by("group__name").\
                select_related("guest", "owner", "group")
        ctx["pending_invitations_guest"] = pending_invitations_guest
        ctx["display_group"] = True

    return r2r("home.html", ctx, request)

#############################################################################################
###All functions which manage the different html pages related to a part, a doc and a user###
#############################################################################################
@handle_errors(restricted_access=False)
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
    ctx["is_contributor"] = obj._user.get_profile().is_contributor
    ctx.update({'current_page' : 'attributes',
                'object_attributes' : object_attributes_list})
    if isinstance(obj.object, models.PLMObject):
        if obj.is_part:
            ctx["attach"] = (obj, "attach_doc")
            ctx["link_creation_action"] = u"%sdoc-cad/add/" % obj.plmobject_url
        elif obj.is_document:
            ctx["attach"] = (obj, "attach_part")
            ctx["link_creation_action"] = u"%sparts/add/" % obj.plmobject_url
    return r2r('attributes.html', ctx, request)

##########################################################################################
@handle_errors(restricted_access=False)
def display_object(request, obj_type, obj_ref, obj_revi):
    """
    Generic object view.

    Permanently redirects to the attribute page of the given object if it
    is a part, a user or a group and to the files page if it is a document.

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
    Lifecycle data of the given object (a part or a document).
  
    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/lifecycle/[apply/]`
    
    .. include:: views_params.txt 
  
    POST requests must have a "demote", "promote", "publish" or "unpublish"
    key and must validate the :class:`.ConfirmPasswordForm` form.
    If the form is valid, the object is promoted, demoted, published, unpublished
    according to the request.

    **Template:**
    
    :file:`lifecycle.html`

    **Context:**

    ``RequestContext``

    ``action``
        Only for unsuccessful POST requests.
        Name of the action ("demote" or "promote") that the user tries to do.
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if obj.is_cancelled:
        return r2r("lifecycle_cancelled.html", ctx, request)
    if request.method == 'POST':
        password_form = forms.ConfirmPasswordForm(request.user, request.POST)
        actions = (("demote", obj.demote), ("promote", obj.approve_promotion),
                   ("discard", obj.discard_approvals),
                   ("publish", obj.publish), ("unpublish", obj.unpublish),
                   ("cancel", obj.safe_cancel),
                  )
        if password_form.is_valid():
            for action_name, method in actions:
                if action_name in request.POST:
                    method()
                    break
            return HttpResponseRedirect("..")
        for action_name, method in actions:
            if action_name in request.POST:
                ctx["action"] = action_name
                break
    else: 
        password_form = forms.ConfirmPasswordForm(request.user)
    ctx['password_form'] = password_form
    ctx['in_group'] = obj.check_in_group(request.user, raise_=False)
    ctx.update(get_management_data(obj, request.user))
    ctx.update(get_lifecycle_data(obj))
    return r2r('lifecycle.html', ctx, request)
    
    
def get_lifecycle_data(obj):
    """
    Returns a dictionary containing lifecycle data of *obj*.

    **Dictionary content**
    
    ``object_lifecycle``
        List of tuples (state name, *boolean*, signer role). The boolean is
        True if the state name equals to the current state. The signer role
        is a dict {"role" : name of the role, "user__username" : name of the
        signer}

    ``is_signer``
        True if the current user has the permission to promote this object

    ``is_signer_dm``
        True if the current user has the permission to demote this object
    
    ``signers_data``
        List of tuple (signer, nb_signer). The signer is a dict which contains
        management data for the signer and indicates wether a signer exists or not.
        
    ``password_form``
        A form to ask the user password

    ``cancelled_revisions``
        List of plmobjects that will be cancelled if the object is promoted
    
    ``deprecated_revisions``
        List of plmobjects that will be deprecated if the object is promoted
    """
    ctx = {}
    state = obj.state.name
    object_lifecycle = []
    roles = defaultdict(list)
    for link in obj.plmobjectuserlink_plmobject.now().order_by("ctime").select_related("user"):
        roles[link.role].append(link)
    lcs = obj.lifecycle.to_states_list()
    for i, st in enumerate(lcs):
        links = roles.get(level_to_sign_str(i), [])
        object_lifecycle.append((st, st == state, links))
    is_signer = obj.check_permission(obj.get_current_sign_level(), False)
    can_approve = obj.can_approve_promotion()
    is_signer_dm = obj.check_permission(obj.get_previous_sign_level(), False)
    if obj.can_edit_signer():
        ctx["can_edit_signer"] = True
    else:
        ctx["can_edit_signer"] = False
        ctx["approvers"] = set(obj.get_approvers())

    # warning if a previous revision will be cancelled/deprecated
    cancelled = []
    deprecated = []
    if is_signer and can_approve:
        if lcs[-1] != state:
            if lcs.next_state(state) == obj.lifecycle.official_state.name:
                for rev in obj.get_previous_revisions():
                    if rev.is_official:
                        deprecated.append(rev)
                    elif rev.is_draft or rev.is_proposed:
                        cancelled.append(rev)
    ctx["cancelled_revisions"] = cancelled
    ctx["deprecated_revisions"] = deprecated

    ctx.update({
        'current_page' : 'lifecycle', 
        'object_lifecycle' : object_lifecycle,
        'is_signer' : is_signer, 
        'is_signer_dm' : is_signer_dm,
        'is_promotable' : obj.is_promotable(),
        'can_approve' : can_approve,
        'can_cancel' : obj.can_cancel(),
    })
    return ctx
    
def get_management_data(obj, user):
    """
    Returns a dictionary containing management data for *obj*.

    :param user: User who runs the request
    
    **Dictionary content**

    ``notified_list``
        List of notification :class:`.PLMObjectUserLink` related to *obj*

    ``owner_list``
        List of owner :class:`.PLMObjectUserLink` related to *obj*

    ``reader_list``
        List of restricted reader :class:`.PLMObjectUserLink` related to *obj*

    If *user* does not own *obj*:

        ``is_notified``
            True if *user* receives notifications when *obj* changes
        
        ``remove_notify_link``
            (set if *is_notified* is True)
            Notification :class:`.PLMObjectUserLink` between *obj* and *user*

        ``can_notify``
            True if *user* can ask to receive notifications when *obj* changes

        ``notify_self_form``
            (set if *can_notify* is True)
            form to notify *user*
    """
    ctx = {}
    # evaluates now PLMObjectLinks to make one sql query
    links = list(obj.plmobjectuserlink_plmobject.now().select_related("user"))
    if not obj.check_permission("owner", False):
        link = [l for l in links if l.role == models.ROLE_NOTIFIED and l.user == user]
        ctx["is_notified"] = bool(link)
        if link:
            ctx["remove_notify_link"] = link[0]
        else:
            if obj.check_in_group(user, False):
                initial = dict(type="User", username=user.username)
                form = forms.SelectUserForm(initial=initial)
                for field in ("type", "username"):
                    form.fields[field].widget = HiddenInput() 
                ctx["notify_self_form"] = form
                ctx["can_notify"] = True
            else:
                ctx["can_notify"] = False
    ctx.update({
        'notified_list' : [l for l in links if l.role == models.ROLE_NOTIFIED],
        'owner_list' :[l for l in links if l.role == models.ROLE_OWNER],
        'reader_list' :[l for l in links if l.role == models.ROLE_READER],
    })
    return ctx
    

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

def get_id_card_data(doc_ids):
    """
    Get informations to display in the id-cards of all Document which id is in doc_ids
    
    :param doc_ids: list of Document ids to treat
    
    :return: a Dictionnary which contains the following informations
    
        * ``thumbnails``
            list of tuple (document,thumbnail)
            
        * ``num_files``
            list of tuple (document, number of file)
    """
    ctx = { "thumbnails" : {}, "num_files" : {} }
    if doc_ids:
        thumbnails = models.DocumentFile.objects.filter(deprecated=False,
                    document__in=doc_ids, thumbnail__isnull=False)
        ctx["thumbnails"].update(thumbnails.values_list("document", "thumbnail"))
        num_files = dict.fromkeys(doc_ids, 0)
        for doc_id in models.DocumentFile.objects.filter(deprecated=False,
            document__in=doc_ids).values_list("document", flat=True):
            num_files[doc_id] += 1
        ctx["num_files"] = num_files
    return ctx

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
                            # a user should not be able to go here if he 
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
    
    ctx.update(get_id_card_data([r.id for r in revisions]))
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
ITEMS_PER_HISTORY = 50

def redirect_history(request, type, hid):
    """
    Redirects to the history page that contains the history item
    numbered *hid*.
    """
    H = {"group" : models.GroupHistory,
         "user" : models.UserHistory,
         "object" : models.History,}[type]
    h = H.objects.get(id=int(hid))
    items = H.objects.filter(plmobject=h.plmobject, date__gte=h.date).count() - 1
    page = items // ITEMS_PER_HISTORY + 1
    url = u"%shistory/?page=%d#%s" % (h.plmobject.plmobject_url, page, hid)
    return HttpResponseRedirect(url)


@handle_errors
def display_object_history(request, obj_type="-", obj_ref="-", obj_revi="-", timeline=False,
        template="history.html"):
    """
    History view.
    
    This view displays a history of the selected object and its revisions.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/history/`
    :url: :samp:`/user/{username}/history/`
    :url: :samp:`/group/{group_name}/history/`
    :url: :samp:`/timeline/`
    
    .. include:: views_params.txt 

    **Template:**
    
    :file:`history.html`

    **Context:**

    ``RequestContext``

    ``object_history``
        list of :class:`.AbstractHistory`

    ``show_revisions``
        True if the template should show the revision of each history row
    
    ``show_identifiers``
        True if the template should show the type, reference and revision
        of each history row
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if timeline:
        # global timeline: shows objects owned by the company and readable objects
        history = models.timeline_histories(obj)
        ctx['object_type'] = _("Timeline")
    elif hasattr(obj, "get_all_revisions"):
        # display history of all revisions
        history = obj.histories
        ctx["show_revisions"] = True
    else:
        ctx["show_revisions"] = False
        history = obj.histories
    paginator = Paginator(history, ITEMS_PER_HISTORY)
    page = request.GET.get('page', 1)
    try:
        history = paginator.page(page)
    except PageNotAnInteger:
        history = paginator.page(1)
        page = 1
    except EmptyPage:
        history = paginator.page(paginator.num_pages)
    ctx.update({
        'current_page' : 'history', 
        'object_history' : history,
        'show_identifiers' : timeline,
        })
    return r2r(template, ctx, request)


#############################################################################################
###         All functions which manage the different html pages specific to part          ###
#############################################################################################

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
        display_form = forms.DisplayChildrenForm(initial={"date" : datetime.datetime.now(),
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

##########################################################################################
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

##########################################################################################    
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
    now = datetime.datetime.now()
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

    
##########################################################################################    
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
        display_form = forms.DisplayChildrenForm(initial=dict(date=datetime.datetime.now(),
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


##########################################################################################
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

    ``archive_form``
        a form to download an archive containing all attached files

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
    archive_form = forms.ArchiveForm()
    ctx.update({'current_page':'doc-cad',
                'documents': obj.get_attached_documents(),
                'forms' : dforms,
                'archive_form' : archive_form,
                'docs_formset': formset})
    return r2r('parts/doccad.html', ctx, request)


##########################################################################################    
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
    
#############################################################################################
###      All functions which manage the different html pages specific to documents        ###
#############################################################################################
@handle_errors
def display_parts(request, obj_type, obj_ref, obj_revi):
    """
    Attached parts view.
    
    That view displays the parts attached to the selected object that must be a document.
    
    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/parts/`
    
    .. include:: views_params.txt

    **Template:**
    
    :file:`documents/parts.html`

    **Context:**

    ``RequestContext``
   
    ``parts``
        a queryset of :class:`.DocumentPartLink` bound to the document

    ``parts_formset``
        a formset to detach parts

    ``forms``
        a dictionary (link_id -> form) to get the form related to a link
        (a part may not be "detachable")
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_attached_parts"):
        return HttpResponseBadRequest("object must be a document")
    if request.method == "POST":
        formset = forms.get_rel_part_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_rel_part(formset)
            return HttpResponseRedirect(".")
    else:
        formset = forms.get_rel_part_formset(obj)
    rforms = dict((form.instance.id, form) for form in formset.forms)

    ctx.update({'current_page':'parts', 
                'parts': obj.get_attached_parts(),
                'forms' : rforms,
                'parts_formset': formset})
    return r2r('documents/parts.html', ctx, request)

##########################################################################################    
@handle_errors
def add_part(request, obj_type, obj_ref, obj_revi):
    """
    View to attach a part to a document.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/parts/add/`
    
    .. include:: views_params.txt

    **Template:**
    
    :file:`documents/parts_add.html`

    **Context:**

    ``RequestContext``
   
    ``add_part_form``
        a form to attach a part (:class:`.AddPartForm`)

    ``link_creation``
        Set to True

    ``attach``
        set to (*obj*, "attach_part")
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if request.POST:
        add_part_form = forms.AddPartForm(request.POST)
        if add_part_form.is_valid():
            part_obj = get_obj_from_form(add_part_form, request.user)
            obj.attach_to_part(part_obj)
            return HttpResponseRedirect(obj.plmobject_url + "parts/")
    else:
        add_part_form = forms.AddPartForm()
    ctx.update({'link_creation': True,
                'add_part_form': add_part_form,
                'attach' : (obj, "attach_part") })
    return r2r('documents/parts_add.html', ctx, request)

##########################################################################################
@handle_errors
def display_files(request, obj_type, obj_ref, obj_revi):
    """
    Files view.
    
    That view displays files of the given document. 
    
    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/files/`
    
    .. include:: views_params.txt

    **Template:**
    
    :file:`documents/files.html`

    **Context:**

    ``RequestContext``
   
    ``file_formset``
        a formset to remove files

    ``archive_form``
        form to download all files in a single archive (tar, zip)
    
    ``add_file_form``
        form to add a file
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    if not hasattr(obj, "files"):
        return HttpResponseBadRequest("object must be a document")
    if request.method == "POST":
        if request.FILES:
            # from a browser where js is disabled
            return add_file(request, obj_type, obj_ref, obj_revi)
        formset = forms.get_file_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_file(formset)
            return HttpResponseRedirect(".")
    else:
        formset = forms.get_file_formset(obj)
    add_file_form = forms.AddFileForm()
    archive_form = forms.ArchiveForm()
    
    ctx.update({'current_page':'files', 
                'file_formset': formset,
                'archive_form' : archive_form,
                'deprecated_files' : obj.deprecated_files.filter(last_revision__isnull=True),
                'add_file_form': add_file_form,
               })
    return r2r('documents/files.html', ctx, request)

##########################################################################################
@csrf_protect
@handle_errors(undo="..")
def add_file(request, obj_type, obj_ref, obj_revi):
    """
    That view displays the form to upload a file. 

    .. note::

        This view show a simple form (no javascript) and is here
    
    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/files/add/`
    
    .. include:: views_params.txt

    **Template:**
    
    :file:`documents/files_add_noscript.html`

    **Context:**

    ``RequestContext``

    ``add_file_form``
        form to add a file
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if request.method == "POST":
        add_file_form = forms.AddFileForm(request.POST, request.FILES)
        if add_file_form.is_valid():
            for fkey, f in request.FILES.iteritems():
                obj.add_file(request.FILES[fkey])
            return HttpResponseRedirect(obj.plmobject_url + "files/")
    else:
        if 'file_name' in request.GET:
            f_name = request.GET['file_name'].encode("utf-8")
            if obj.has_standard_related_locked(f_name):
                return HttpResponse("true:Native file has a standard related locked file.")
            else:
                return HttpResponse("false:")
        add_file_form = forms.AddFileForm()
    ctx['add_file_form'] = add_file_form 
    return r2r('documents/files_add_noscript.html', ctx, request)

##########################################################################################

@csrf_exempt
def up_file(request, obj_type, obj_ref, obj_revi):
    """
    This view process the file(s) upload.
    
    The upload is done asynchronously.
    
    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/files/up/`
    
    .. include:: views_params.txt
    
    :post params:
        files
            uploaded files
    
    :get params:
        list of pair (filename, id)
    
    The response contains "failed" if the submitted form is not valid.
    """
    request.upload_handlers.insert(0, ProgressBarUploadHandler(request))
    return _up_file(request, obj_type, obj_ref, obj_revi)

@csrf_protect
@handle_errors
def _up_file(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if request.method == "POST":
        add_file_form = forms.AddFileForm(request.POST, request.FILES)
        if add_file_form.is_valid():
            for key, f_id in request.GET.iteritems():
                obj.add_file(request.FILES[key])
            return HttpResponse(".")
        else:
            return HttpResponse("failed")

@handle_errors
@csrf_protect
def up_progress(request, obj_type, obj_ref, obj_revi):
    """
    Show upload progress for a given progress_id
    
    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/files/_up/`
    
    .. include:: views_params.txt
    
    :get params:
        X-Progress-ID
            progress id to search
        
        f_size
            size of the original file
            
    The response contains the uploaded size and a status :

        * waiting if the corresponding file has not been created yet
        
        * writing if the file is being written
        
        * linking if the size of the uploaded file equals the size of the original
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    ret = ""
    p_id = request.GET['X-Progress-ID']
    tempdir = settings.FILE_UPLOAD_TEMP_DIR or tempfile.gettempdir()
    f = glob.glob(os.path.join(tempdir, "*%s_upload" % p_id))
    if f:
        ret = str(os.path.getsize(f[0]))
    if not ret:
        ret = "0:waiting"
    else:
        if ret == request.GET['f_size']:
            ret += ":linking"
        else:
            ret += ":writing"
    return HttpResponse(ret)


#############################################################################################
###    All functions which manage the different html pages specific to part and document  ###
#############################################################################################

@handle_errors(undo="../../../lifecycle/")
def replace_management(request, obj_type, obj_ref, obj_revi, link_id):
    """
    View to replace a manager (owner, signer, reader...) by another one.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/management/replace/{link_id}/`
    
    .. include:: views_params.txt
    :param link_id: id of the :class:`.PLMObjectUserLink` being replaced

    **Template:**
    
    :file:`management_replace.html`

    **Context:**

    ``RequestContext``
   
    ``replace_manager_form``
        a form to select the new manager (a user)

    ``link_creation``
        Set to True

    ``role``
        role of the link being replace

    ``attach``
        set to (*obj*, :samp`"add_{role}"`)
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    link = models.PLMObjectUserLink.current_objects.get(id=int(link_id))
    if obj.object.id != link.plmobject.id:
        raise ValueError("Bad link id")
    
    if request.method == "POST":
        replace_manager_form = forms.SelectUserForm(request.POST)
        if replace_manager_form.is_valid():
            if replace_manager_form.cleaned_data["type"] == "User":
                user_obj = get_obj_from_form(replace_manager_form, request.user)
                if link.role.startswith(models.ROLE_SIGN):
                    obj.replace_signer(link.user, user_obj.object, link.role)
                else:
                    obj.set_role(user_obj.object, link.role)
                    if link.role == models.ROLE_NOTIFIED:
                        obj.remove_notified(link.user)
                    elif link.role == models.ROLE_READER:
                        obj.remove_reader(link.user)
            return HttpResponseRedirect("../../../lifecycle/")
    else:
        replace_manager_form = forms.SelectUserForm()
    
    ctx.update({'current_page':'lifecycle', 
                'replace_manager_form': replace_manager_form,
                'link_creation': True,
                'role' : link.role,
                'attach' : (obj, "add_" + link.role)})
    return r2r('management_replace.html', ctx, request)

##########################################################################################    
@handle_errors(undo="../../lifecycle/")
def add_management(request, obj_type, obj_ref, obj_revi, reader=False, level=None):
    """
    View to add a manager (notified user or restricted reader).

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/management/add/`

    or 

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/management/add-reader/`

    .. include:: views_params.txt
    :param reader: True to add a restricted reader instead of a notified user

    **Template:**
    
    :file:`management_replace.html`

    **Context:**

    ``RequestContext``
   
    ``replace_manager_form``
        a form to select the new manager (a user)

    ``link_creation``
        Set to True

    ``role``
        role of the new user (:const:`.ROLE_NOTIFIED` or :const:`.ROLE_READER`)

    ``attach``
        set to (*obj*, :samp:`"add_{role}"`)

    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if level is None:
        role =  models.ROLE_READER if reader else models.ROLE_NOTIFIED
    else:
        role = level_to_sign_str(int(level))
    if request.method == "POST":
        add_management_form = forms.SelectUserForm(request.POST)
        if add_management_form.is_valid():
            if add_management_form.cleaned_data["type"] == "User":
                user_obj = get_obj_from_form(add_management_form, request.user)
                obj.set_role(user_obj.object, role)
            return HttpResponseRedirect("../../lifecycle/")
    else:
        add_management_form = forms.SelectUserForm()
    
    ctx.update({'current_page':'lifecycle', 
                'replace_manager_form': add_management_form,
                'link_creation': True,
                'role' : role,
                "attach" : (obj, "add_" + role)})
    return r2r('management_replace.html', ctx, request)

##########################################################################################    
@handle_errors
def delete_management(request, obj_type, obj_ref, obj_revi):
    """
    View to remove a notified user or a restricted user.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/management/delete/`

    The request must be a POST request containing the key ``link_id``.
    It should be the id of one of the :class:`.PLMObjectUserLink` related to
    the object.
    The role of this link must be :const:`.ROLE_NOTIFIED` or :class:`.ROLE_READER`.

    Redirects to :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/management/lifecycle/`
    in case of a success.
    """
    obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
    if request.method == "POST":
        try:
            link_id = int(request.POST["link_id"])
            link = models.PLMObjectUserLink.current_objects.get(id=link_id)
            obj.remove_user(link)
        except (KeyError, ValueError, ControllerError):
            return HttpResponseForbidden()
    return HttpResponseRedirect("../../lifecycle/")

##########################################################################################
###    Manage html pages for part / document creation and modification                 ###
##########################################################################################

@handle_errors
def create_object(request, from_registered_view=False, creation_form=None):
    """
    View to create a :class:`.PLMObject` or a :class:`.GroupInfo`.

    :url: ``/object/create/`` 

    Requests (POST and GET) must contain a ``type`` variable that validates a
    :class:`.TypeForm`.

    POST requests must validate the creation form, fields depend on the
    given type. If the creation form is valid, an object is created and
    in case of success, this view redirects to the created object.
    
    Requests may contain a ``__next__`` variable. A successful creation will
    redirect to this URL. Some special strings are replaced:

        * ``##type##`` with the created object's type
        * ``##ref##`` with the created object's reference
        * ``##rev##`` with the created object's reference

    Requests may also contain other special variables (at most one of
    them):

        ``related_doc``
            Id of a document. The created part will be attached to this
            document. Object's type is restricted to part types.
            Two context variables (``related_doc`` and ``related``)
            are set to the document controller.

        ``related_part``
            Id of a part. The created document will be attached to this
            part. Object's type is restricted to document types.
            Two context variables (``related_part`` and ``related``)
            are set to the part controller.

        ``related_parent``
            Id of a part. Object's type is restricted to part types.
            Two context variables (``related_parent`` and ``related``)
            are set to the part controller.

    .. note::
        If *from_registered_view* is False, this view delegates its
        treatment to a registered view that handles creation of
        objects of the given type.
        (see :func:`.get_creation_view` and :func:`.register_creation_view`)

    :param from_registered_view: True if this function is called by another
         creation view
    :param creation_form: a creation form that will be used instead of the
         default one
    
    **Template:**
    
    :file:`create.html`

    **Context:**

    ``RequestContext``
   
    ``creation_form``
    
    ``creation_type_form``
        :class:`.TypeForm` to select the type of the created object

    ``object_type``
        type of the created object

    ``next``
        value of the ``__next__`` request variable if given
    """

    obj, ctx = get_generic_data(request)
    Form = forms.TypeForm
    # it is possible that the created object must be attached to a part
    # or a document
    # related_doc and related_part should be a plmobject id
    # If the related_doc/part is not a doc/part, we let python raise
    # an AttributeError, since a user should not play with the URL
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
    elif "related_parent" in request.REQUEST:
        Form = forms.PartTypeForm
        parent = get_obj_by_id(int(request.REQUEST["related_parent"]), request.user)
        ctx["related_parent"] = request.REQUEST["related_parent"]
        related = ctx["related"] = parent

    if "__next__" in request.REQUEST:
        redirect_to = request.REQUEST["__next__"]
        ctx["next"] = redirect_to
    else:
        # will redirect to the created object
        redirect_to = None

    type_form = Form(request.REQUEST)
    if type_form.is_valid():
        type_ = type_form.cleaned_data["type"]
        cls = models.get_all_users_and_plmobjects()[type_]
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
            creation_form.initial["lifecycle"] = related.lifecycle
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
            if redirect_to:
                redirect_to = redirect_to.replace("##ref##", ctrl.reference)
                redirect_to = redirect_to.replace("##rev##", ctrl.revision)
                redirect_to = redirect_to.replace("##type##", ctrl.type)
            return HttpResponseRedirect(redirect_to or ctrl.plmobject_url)
    ctx.update({
        'creation_form' : creation_form,
        'object_type' : type_,
        'creation_type_form' : type_form,
    })
    return r2r('create.html', ctx, request)

##########################################################################################
@handle_errors(undo="../attributes/", restricted_access=False)
def modify_object(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for the modification of the selected object.
    It computes a context dictionary based on
    
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


@handle_errors(undo="../attributes/")
def clone(request, obj_type, obj_ref, obj_revi,creation_form=None):
    """
    Manage html page to display the cloning form of the selected object
    (part or document) or clone it.
    
    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/clone/`
    
    .. include:: views_params.txt 
    
    **Template:**
    
    :file:`clone.html`
    
    :param creation_form: the creation form that will be used to clone the object
    
    If the object is a part :
    
    :post params:
        a valid :class:`.SelectDocumentFormset`
            Only required if *is_linked* is True, see below.
        a valid :class:`.SelectChildFormset`
            Only required if *is_linked* is True, see below.

    A cloned part may be attached to some documents.
    These documents are given by :meth:`.PartController.get_suggested_documents`.
    A cloned part may also have some children from the original revision.


    If the object is a document :
    
    :post params:
        a valid :class:`.SelectPartFormset`
            Only required if *is_linked* is True, see below.
            
    A cloned document may be attached to some parts, given by :meth:`.DocumentController.get_suggested_parts`.


    **Context:**

    ``RequestContext``

    ``is_linked``
        True if the object is linked (attached) to other object , at least one.
    
    ``creation_form``
        form to clone the object. Fields in this form are set according to the current object.

    ``doc_formset``
        a :class:`.SelectDocmentFormset` of documents that the new object, if it is a part,
        may be attached to. Only set if *is_linked* is True.

    ``children_formset``
        a :class:`.SelectChildFormset` of parts that the new object, if it is a part,
        may be linked with. Only set if *is_linked* is True.
    
    ``parts_formset``
        a :class:`.SelectPartFormset` of parts that the new object, if it is a document,
        may be attached to. Only set if *is_linked* is True.
    
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    obj.check_clone()
    cls = models.get_all_users_and_plmobjects()[obj_type]
    is_linked = True
    if issubclass(cls, models.Part):
        children = [c.link for c in obj.get_children(1)]
        documents = obj.get_suggested_documents()
        is_linked = ctx['is_linked'] = bool(children or documents)
    else:
        parts = obj.get_suggested_parts()
        is_linked = ctx['is_linked'] = bool(parts)
        
    formsets ={}
    
    if request.method == 'GET':
        # generate and fill the creation form
        not_auto_cloned_fields =['reference','revision','group','lifecycle','auto']
        creation_form = forms.get_creation_form(request.user, cls)
        if bool(request.user.groups.filter(id=obj.group.id)):
            creation_form.fields["group"].initial = obj.group.id
        if not obj.is_cancelled:
            creation_form.initial["lifecycle"] = obj.lifecycle
        for f in creation_form.fields:
            if f not in not_auto_cloned_fields:
                creation_form.fields[f].initial = getattr(obj, f)
                
        # generate the links form
        if issubclass(cls, models.Part) and is_linked:
            initial = [dict(link=link) for link in children]
            formsets["children_formset"] = forms.SelectChildFormset(prefix="children",
                initial=initial)
            initial = [dict(document=d) for d in documents]
            formsets["doc_formset"] = forms.SelectDocumentFormset(prefix="documents",
                initial=initial)
        else:
            if issubclass(cls, models.Document) and is_linked :
                formsets["part_formset"] = forms.SelectPartFormset(queryset=parts)
                
    elif request.method == 'POST':
        if issubclass(cls, models.Part) and is_linked:
            formsets.update({
                "children_formset":forms.SelectChildFormset(request.POST,
                    prefix="children"),
                "doc_formset": forms.SelectDocumentFormset(request.POST,
                    prefix="documents"),
            })
        elif is_linked:
            formsets["part_formset"]=forms.SelectPartFormset(request.POST)
        if creation_form is None:
            creation_form = forms.get_creation_form(request.user, cls, request.POST)
        if creation_form.is_valid():
            if is_linked :
                valid_forms = False
                if issubclass(cls, models.Part):
                    valid_forms, selected_children, selected_documents = clone_part(request.user, request.POST, children, documents)
                    if valid_forms :
                        new_ctrl = obj.clone(creation_form, request.user, selected_children, selected_documents)
                        return HttpResponseRedirect(new_ctrl.plmobject_url)
                    else :
                        formsets.update({
                            "children_formset":forms.SelectChildFormset(request.POST,
                                prefix="children"),
                            "doc_formset": forms.SelectDocumentFormset(request.POST,
                                prefix="document"),
                        })
                elif issubclass(cls, models.Document) and is_linked:
                    valid_forms, selected_parts = clone_document(request.user, request.POST, parts)
                    if valid_forms:
                        new_ctrl = obj.clone(creation_form, request.user, selected_parts)
                        return HttpResponseRedirect(new_ctrl.plmobject_url) 
                    else :
                        formsets["part_formset"]=forms.SelectPartFormset(request.POST)
            else:
                if issubclass(cls, models.Part):
                    new_ctrl = obj.clone(creation_form, request.user, [], [])
                else:
                    new_ctrl = obj.clone(creation_form, request.user, [])
                return HttpResponseRedirect(new_ctrl.plmobject_url)
    ctx['creation_form'] = creation_form
    ctx.update(formsets)
    return r2r('clone.html', ctx, request)

def clone_part(user, data, children, documents):
    """
    Analyze the formsets in data to return list of selected children and documents.
    
    :param user: user who is cloning the part
    :param data: posted data (see post params in :func:`.clone`)
    :param children: list of children linked to the originial part
    :param documents: list of documents attached to the original part
    
    :return:
        valid_forms
            True if all formsets are valid
        selected_children
            list of children to add to the new part
        selected_documents
            list of documents to attach to the new part
    """
    valid_forms = True
    selected_children = []
    selected_documents = []
    if children :
        # children
        children_formset = forms.SelectChildFormset(data,
            prefix="children")
        if children_formset.is_valid():
            for form in children_formset.forms:
                link = form.cleaned_data["link"]
                if link not in children: 
                    valid_forms = False
                    form.errors['link']=[_("It's not a valid child.")]
                    break
                if form.cleaned_data["selected"]:
                    selected_children.append(link)
        else:
            valid_forms = False
    if valid_forms and documents :
        # documents
        doc_formset = forms.SelectDocumentFormset(data,
            prefix="documents")
        if doc_formset.is_valid():
            for form in doc_formset.forms:
                doc = form.cleaned_data["document"]
                if doc not in documents: 
                    valid_forms = False
                    form.errors['document']=[_("It's not a valid document.")]
                    break
                if form.cleaned_data["selected"]:
                    selected_documents.append(doc)
        else:
            valid_forms = False
    return valid_forms, selected_children, selected_documents
                        
def clone_document(user, data, parts):
    """
    Analyze the formsets in data to return list of selected parts.
    
    :param user: user who is cloning the document
    :param data: posted data (see post params in :func:`.clone`)
    :param parts: list of parts attached to the original document
    
    :return:
        valid_forms
            True if all formsets are valid
        selected_parts
            list of parts to attach to the new document
    """
    valid_forms= True
    selected_parts = []
    
    if parts:
        part_formset = forms.SelectPartFormset(data)
        if part_formset.is_valid():
            for form in part_formset.forms:
                part = form.instance
                if part not in parts: 
                    # invalid data
                    # a user should not be able to go here if he 
                    # does not write by hand its post request
                    # so we do not need to generate an error message
                    valid_forms = False
                    form.errors.append_("It's not a valid part.")
                    break
                if form.cleaned_data["selected"]:
                    selected_parts.append(part)
        else:
            valid_forms = False
    return valid_forms, selected_parts
    
#############################################################################################
###         All functions which manage the different html pages specific to user          ###
#############################################################################################
@handle_errors(restricted_access=False)
def modify_user(request, obj_ref):
    """
    Manage html page for the modification of the selected
    :class:`~django.contrib.auth.models.User`.
    It computes a context dictionary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :class:`~django.contrib.auth.models.User`
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx = get_generic_data(request, "User", obj_ref)
    obj.check_update_data()
    if request.method == 'POST' and request.POST:
        modification_form = forms.OpenPLMUserChangeForm(request.POST)
        if modification_form.is_valid():
            obj.update_from_form(modification_form)
            return HttpResponseRedirect("/user/%s/" % obj.username)
    else:
        modification_form = forms.OpenPLMUserChangeForm(instance=obj.object)
    
    ctx["modification_form"] = modification_form
    return r2r('edit.html', ctx, request)
    
##########################################################################################
@handle_errors(restricted_access=False)
def change_user_password(request, obj_ref):
    """
    Manage html page for the modification of the selected
    :class:`~django.contrib.auth.models.User` password.
    It computes a context dictionary based on
    
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
    
    ctx["modification_form"] = modification_form
    return r2r('users/password.html', ctx, request)

#############################################################################################
@handle_errors(restricted_access=False)
def display_related_plmobject(request, obj_type, obj_ref, obj_revi):
    """
    View listing the related parts and documents of
    the selected :class:`~django.contrib.auth.models.User`.
    
    .. include:: views_params.txt 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_object_user_links"):
        return HttpResponseBadRequest("object must be a user")
    objs = obj.get_object_user_links().select_related("plmobject")
    objs = objs.values("role", "plmobject__type", "plmobject__reference",
            "plmobject__revision", "plmobject__name")
    ctx.update({
        'current_page':'parts-doc-cad',
        'object_user_link': objs,
    })
    if not obj.restricted:
        ctx['last_edited_objects'] = get_last_edited_objects(obj.object)
    return r2r('users/plmobjects.html', ctx, request)

#############################################################################################
@handle_errors
def display_delegation(request, obj_ref):
    """
    Delegation view.

    This view displays all delegations of the given user.
    """
    obj, ctx = get_generic_data(request, "User", obj_ref)
    if obj.restricted:
        raise Http404
    if not hasattr(obj, "get_user_delegation_links"):
        return HttpResponseBadRequest("object must be a user")
    if request.method == "POST":
        selected_link_id = request.POST.get('link_id')
        obj.remove_delegation(models.DelegationLink.objects.get(pk=int(selected_link_id)))
        return HttpResponseRedirect("..")
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
    It computes a context dictionary based on
    
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
                'replace_manager_form': delegation_form,
                'link_creation': True,
                'attach' : (obj, "delegate"),
                'role': role})
    return r2r('management_replace.html', ctx, request)
    
    
##########################################################################################
###             Manage html pages for file check-in / check-out / download             ###
########################################################################################## 

@csrf_exempt
def get_checkin_file(request, obj_type, obj_ref, obj_revi, file_id_value):
    """
    Process to the checkin asynchronously in order to show progress 
    when the checked-in file is uploaded.
    
    Calls :func:`.checkin_file` .
    """
    request.upload_handlers.insert(0, ProgressBarUploadHandler(request))
    return checkin_file(request, obj_type, obj_ref, obj_revi,file_id_value)
   
@handle_errors(undo="../..")
@csrf_protect
def checkin_file(request, obj_type, obj_ref, obj_revi, file_id_value):
    """
    Manage html page for the files (:class:`DocumentFile`) checkin in the selected object.
    It computes a context dictionary based on
    
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
    return r2r('documents/files_add_noscript.html', ctx, request)

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
    return serve(ctrl, doc_file, filename)

@secure_required
def public_download(request, docfile_id, filename=""):
    """
    View to download a published document file.

    It returns an :class: `HttpResponseForbidden` if the document is
    not published.
    
    :param request: :class:`django.http.QueryDict`
    :param docfile_id: :attr:`.DocumentFile.id`
    :type docfile_id: str
    :return: a :class:`django.http.HttpResponse`
    """
    doc_file = models.DocumentFile.objects.get(id=docfile_id)
    ctrl = get_obj_by_id(int(doc_file.document.id), request.user)
    if request.user.is_authenticated():
        if not ctrl.published and not ctrl.check_restricted_readable(False):
            raise Http404
    elif not ctrl.published:
        return HttpResponseForbidden()
    return serve(ctrl, doc_file, filename)


def serve(ctrl, doc_file, filename):
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
        files = obj.get_cad_files()
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

@handle_errors 
def file_revisions(request, docfile_id):
    """
    View to download a document file.
    
    :param request: :class:`django.http.QueryDict`
    :param docfile_id: :attr:`.DocumentFile.id`
    :type docfile_id: str
    :return: a :class:`django.http.HttpResponse`
    """
    doc_file = models.DocumentFile.objects.get(id=docfile_id)
    ctrl = get_obj_by_id(int(doc_file.document.id), request.user)
    obj, ctx = get_generic_data(request, doc_file.document.type, doc_file.document.reference,
            doc_file.document.revision)
    last_revision = doc_file.last_revision if doc_file.last_revision else doc_file
    doc_files = last_revision.older_files.order_by("-revision")
    ctx["last_revision"] = last_revision
    ctx["doc_files"] = doc_files
    return r2r("documents/file_revisions.html", ctx, request)


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
    """
    View of the *user* page of a group.
     
    """
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
            state=models.Invitation.PENDING).select_related("guest", "owner")
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
    """
    View of the *user join* page of a group
    
    """
    obj, ctx = get_generic_data(request, "Group", obj_ref)
    if request.method == "POST":
        obj.ask_to_join()
        return HttpResponseRedirect("..")
    else:
        form = forms.SelectUserForm()
    ctx["ask_form"] = ""
    ctx['current_page'] = 'users' 
    ctx['in_group'] = request.user.groups.filter(id=obj.id).exists()
    return r2r("groups/ask_to_join.html", ctx, request)

@handle_errors
def display_groups(request, obj_ref):
    """
    View of the *groups* page of a user.

    """
    obj, ctx = get_generic_data(request, "User", obj_ref)
    ctx["groups"] = models.GroupInfo.objects.filter(id__in=obj.groups.all())\
            .order_by("name")
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
            new_user.get_profile().language = form.cleaned_data["language"]
            role = form.cleaned_data["role"]
            obj.sponsor(new_user, role=="contributor", role=="restricted")
            return HttpResponseRedirect("..")
    else:
        form = forms.SponsorForm(initial=dict(sponsor=obj.id, language=obj.language),
                sponsor=obj.id)
    ctx["sponsor_form"] = form
    ctx['current_page'] = 'delegation' 
    return r2r("users/sponsor.html", ctx, request)

@handle_errors
def create_user(request):
    url = request.user.get_profile().plmobject_url + "delegation/sponsor/" 
    return HttpResponseRedirect(url)
register_creation_view(User, create_user)

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
    objects = obj.plmobject_group.order_by("type", "reference", "revision")
    ctx.update(get_pagination(request.GET, objects, "object"))
    ctx['current_page'] = 'objects'
    return r2r("groups/objects.html", ctx, request)

@handle_errors(undo="../../../users/")
def accept_invitation(request, obj_ref, token):
    """
    Manage page to accept invitation or request to join a group.
    """
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
    """
    Manage page to refuse invitation or request to join a group.
    """
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
    """
    Manage page to import a csv file.
    """
    if not request.user.get_profile().is_contributor:
        raise PermissionError("You are not a contributor.")
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
    """
    View that display a preview of an uploaded csv file.
    """
    obj, ctx = get_generic_data(request)
    if not request.user.get_profile().is_contributor:
        raise PermissionError("You are not a contributor.")
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
        ctx["object_type"] = _("Search")
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

def get_pagination(r_GET, object_list, type):
    """
    Returns a dictionary with pagination data.

    Called in view which returns a template where object id cards are displayed.
    """
    # TODO: move topassembly/children stuff to a Manager
    ctx = {}
    sort = r_GET.get("sort", "children" if type == "topassembly" else "recently-added")
    if sort == "name" :
        sort_critera = "username" if type == "user" else "name"
    elif type in ("part", "topassembly") and sort == "children":
        object_list = object_list.with_children_counts() 
        sort_critera = "-num_children,reference,revision"
    elif type == "part" and sort == "most-used":
        object_list = object_list.with_parents_counts() 
        sort_critera = "-num_parents,reference,revision"
    else:
        sort_critera = "-date_joined" if type == "user" else "-ctime"
    object_list = object_list.order_by(*sort_critera.split(","))
 
    paginator = Paginator(object_list, 24) # Show 24 objects per page
 
    page = r_GET.get('page', 1)
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        objects = paginator.page(1)
        page = 1
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        objects = paginator.page(paginator.num_pages)
    ctx["thumbnails"] = {}
    ctx["num_files"] = {}

    if type in ("object", "document"):
         ids = objects.object_list.values_list("id", flat=True)
         ctx.update(get_id_card_data(ids))
    ctx.update({
         "objects" : objects,
         "sort" : sort,
    })
    return ctx


@secure_required
def browse(request, type="object"):
    user = request.user
    if user.is_authenticated() and not user.get_profile().restricted:
        # only authenticated users can see all groups and users
        obj, ctx = get_generic_data(request, search=False)
        try:
            cls = {
                "object" : models.PLMObject.objects, 
                "part" : models.Part.objects,
                "topassembly" : models.Part.top_assemblies,
                "document" : models.Document.objects,
                "group" : models.GroupInfo.objects,
                "user" : User.objects,
            }[type]
        except KeyError:
            raise Http404
        object_list = cls.all()
        # this only relevant for authenticated users
        ctx["state"] = state = request.GET.get("state", "all")
        if type in ("object", "part", "topassembly", "document"):
            ctx["plmobjects"] = True
            if state == "official":
                object_list = object_list.\
                        exclude(lifecycle=models.get_cancelled_lifecycle()).\
                        filter(state=F("lifecycle__official_state"))
            elif state == "published":
                object_list = object_list.filter(published=True)
        else:
            ctx["plmobjects"] = False
    else:
        try:
            cls = {
                "object" : models.PLMObject.objects, 
                "part" : models.Part.objects,
                "topassembly" : models.Part.top_assemblies,
                "document" : models.Document.objects,
            }[type]
        except KeyError:
            raise Http404
        ctx = init_ctx("-", "-", "-")
        ctx.update({
            'is_readable' : True,
            'plmobjects' : True,
            'restricted' : True,
            'object_menu' : [],
            'navigation_history' : [],
        })
        query = Q(published=True)
        if user.is_authenticated():
            readable = user.plmobjectuserlink_user.now().filter(role=models.ROLE_READER)
            query |= Q(id__in=readable.values_list("plmobject_id", flat=True))
        object_list = cls.filter(query)

    ctx.update(get_pagination(request.GET, object_list, type))
    ctx.update({
        "object_type" : _("Browse"),
        "type" : type,
    })
    return r2r("browse.html", ctx, request)

@secure_required
def public(request, obj_type, obj_ref, obj_revi, template="public.html"):
    """
    .. versionadded:: 1.1

    Public view of the given object, this view is accessible to anonymous
    users. The object must be a published part or document.

    Redirects to the login page if the object is not published and the user
    is not authenticated.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/public/`

    .. include:: views_params.txt 

    **Template:**
    
    :file:`public.html`

    **Context:**

    ``RequestContext``

    ``obj``
        the controller
    
    ``object_attributes``
        list of tuples(verbose attribute name, value)

    ``revisions``
        list of published related revisions

    ``attached``
        list of published attached documents and parts
    """
    # do not call get_generic_data to avoid the overhead due
    # to a possible search and the update of the navigation history
    obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
    if not (obj.is_part or obj.is_document):
        raise Http404
    if not obj.published and request.user.is_anonymous():
        return redirect_to_login(request.get_full_path())
    elif not obj.published and not obj.check_restricted_readable(False):
        raise Http404

    ctx = init_ctx(obj_type, obj_ref, obj_revi)
    attrs = obj.published_attributes
    object_attributes = []
    for attr in attrs:
        item = obj.get_verbose_name(attr)
        object_attributes.append((item, getattr(obj, attr)))
    object_attributes.insert(4, (obj.get_verbose_name("state"), obj.state.name))
    if request.user.is_anonymous():
        test = lambda x: x.published
    else:
        readable = request.user.plmobjectuserlink_user.now().filter(role=models.ROLE_READER)\
                .values_list("plmobject_id", flat=True)
        test = lambda x: x.published or x.id in readable

    revisions = [rev for rev in obj.get_all_revisions() if test(rev)]
    if obj.is_part:
        attached = [d.document for d in obj.get_attached_documents() if test(d.document)]
    else:
        attached = [d.part for d in obj.get_attached_parts() if test(d.part)]
    ctx.update({
        'is_readable' : True,
        # disable the menu and the navigation_history
        'object_menu' : [],
        'navigation_history' : [],
        'obj' : obj,
        'object_attributes': object_attributes,
        'revisions' : revisions,
        'attached' : attached,
    })

    return r2r(template, ctx, request)


@handle_errors
def async_search(request):
    """Perform search_request asynchronously"""
    obj,ctx = get_generic_data(request)
    if request.GET["navigate"]=="true" :
        ctx["navigate_bool"]=True
    return r2r("render_search.html",ctx,request)

