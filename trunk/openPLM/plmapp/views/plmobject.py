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

import itertools
from collections import defaultdict
from mimetypes import guess_type

from django.forms import HiddenInput
from django.http import (HttpResponseRedirect, Http404,
    HttpResponseForbidden, StreamingHttpResponse)
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

import openPLM.plmapp.models as models
import openPLM.plmapp.forms as forms
from openPLM.plmapp.utils.archive import generate_archive, ARCHIVE_FORMATS
from openPLM.plmapp.views.base import (get_obj, get_obj_from_form,
    handle_errors, get_generic_data, get_id_card_data)
from openPLM.plmapp.exceptions import ControllerError
from openPLM.plmapp.utils import level_to_sign_str, get_next_revision, r2r


@handle_errors(restricted_access=False)
def redirect_from_name(request, type, name):
    if type == "part":
        cls = models.Part
    elif type == "doc":
        cls = models.Document
    else:
        raise Http404("type not found")
    try:
        obj = cls.objects.order_by("-ctime").filter(name=name)[0]
    except IndexError:
        raise Http404(_(u"No object has the name %(name)s") % name)
    return HttpResponseRedirect(obj.plmobject_url)


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
        if obj.is_part:
            actions += (("promote_assembly", obj.promote_assembly),)
        if password_form.is_valid():
            for action_name, method in actions:
                if action_name in request.POST:
                    method()
                    if 'cancel' in request.POST:
                        message = _(u"The %(object_type)s has been successfully cancelled." % dict(object_type=obj_type))
                        messages.info(request, message)
                    elif 'promote' in request.POST:
                        message = _(u"The %(object_type)s has been successfully promoted." % dict(object_type=obj_type))
                        messages.info(request, message)
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
    for link in obj.users.now().order_by("ctime").select_related("user"):
        roles[link.role].append(link)
    lcs = obj.lifecycle.to_states_list()
    for i, st in enumerate(lcs):
        links = roles.get(level_to_sign_str(i), [])
        object_lifecycle.append((st, st == state, links))
    is_signer = obj.check_permission(obj.get_current_sign_level(), False)
    is_promotable = obj.is_promotable()
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
    previous_alternates = []
    alternates = obj.get_alternates() if obj.is_part else []
    if is_signer and can_approve and lcs[-1] != state:
        if lcs.next_state(state) == obj.lifecycle.official_state.name:
            revisions = obj.get_previous_revisions()
            for rev in revisions:
                if rev.is_official:
                    deprecated.append(rev)
                elif rev.is_draft or rev.is_proposed:
                    cancelled.append(rev)
            if obj.is_part and not alternates and revisions:
                previous_alternates = type(obj)(revisions[-1].part, None).get_alternates()

    # promote assembly
    if obj.is_part and can_approve and is_signer and not is_promotable:
        promote_assembly = (obj.is_draft or obj.is_proposed) and obj.parentchildlink_parent.now().exists()
        # TODO: more restrictions
    else:
        promote_assembly = False

    ctx.update({
        'cancelled_revisions' : cancelled,
        'deprecated_revisions' : deprecated,
        'alternates' : alternates,
        'previous_alternates' : previous_alternates,
        'current_page' : 'lifecycle',
        'object_lifecycle' : object_lifecycle,
        'is_signer' : is_signer,
        'is_signer_dm' : is_signer_dm,
        'is_promotable' : is_promotable,
        'can_approve' : can_approve,
        'can_cancel' : obj.can_cancel(),
        'promote_assembly' : promote_assembly,
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
    links = list(obj.users.now().select_related("user"))
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
    add_form = None
    if obj.is_revisable():
        if request.method == "POST":
            add_form = forms.AddRevisionForm(obj, request.user, request.POST)
        else:
            initial = { "revision": get_next_revision(obj.revision) }
            add_form = forms.AddRevisionForm(obj, request.user, initial=initial)
    ctx["add_revision_form"] = add_form
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
    add_form = ctx["add_revision_form"]
    if add_form is not None:
        parts = obj.get_suggested_parts()
        confirmation = bool(parts)

        if request.method == "POST" and request.POST:
            selected_parts = []
            valid_forms = True
            if confirmation:
                part_formset = forms.SelectPartFormset(request.POST)
                ctx["part_formset"] = part_formset
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
                obj.revise(add_form.cleaned_data["revision"], selected_parts,
                        group=add_form.cleaned_data["group"])
                return HttpResponseRedirect(".")
        else:
            if confirmation:
                ctx["part_formset"] = forms.SelectPartFormset(queryset=parts)
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
    add_form = ctx["add_revision_form"]
    if add_form is not None:
        children = [c.link for c in obj.get_children(1)]
        parents = obj.get_suggested_parents()
        documents = obj.get_suggested_documents()
        confirmation = bool(children or parents or documents)

        if request.method == "POST" and request.POST:
            valid_forms = True
            selected_children = []
            selected_parents = []
            selected_documents = []
            if confirmation:
                # children
                children_formset = forms.SelectChildFormset(request.POST,
                        prefix="children")
                ctx["children_formset"] = children_formset
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
                    ctx["doc_formset"] = doc_formset
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
                    ctx["parents_formset"] = parents_formset
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
                        selected_documents, selected_parents,
                        group=add_form.cleaned_data["group"])
                return HttpResponseRedirect(".")
        else:
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

    ctx["confirmation"] = confirmation
    revisions = obj.get_all_revisions()
    ctx.update({'current_page' : 'revisions',
                'revisions' : revisions,
                })
    return r2r('parts/revisions.html', ctx, request)


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
        set to (*obj*, :samp:`"add_{role}"`)
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    link = obj.users.now().get(id=int(link_id))

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
            message = _(u"Role %(add_role)s granted." % dict(add_role=role))
            messages.info(request, message)
            return HttpResponseRedirect("../../lifecycle/")
    else:
        add_management_form = forms.SelectUserForm()

    ctx.update({'current_page':'lifecycle',
                'replace_manager_form': add_management_form,
                'link_creation': True,
                'role' : role,
                "attach" : (obj, "add_" + role)})
    return r2r('management_replace.html', ctx, request)


@handle_errors
def delete_management(request, obj_type, obj_ref, obj_revi, reader=False, level=None):
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
            link = obj.users.now().get(id=link_id)
            obj.remove_user(link)
            messages.info(request, _(u"The user you have selected has been successfully deleted."))
        except (KeyError, ValueError, ControllerError):
            return HttpResponseForbidden()
    return HttpResponseRedirect("../../lifecycle/")


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

    archive_format = request.GET.get("format")
    if archive_format in ARCHIVE_FORMATS:
        name = "%s_%s.%s" % (obj_ref, obj_revi, archive_format)
        content_type = guess_type(name, False)[0]
        if not content_type:
            content_type = 'application/octet-stream'
        content = generate_archive(files, archive_format)
        response = StreamingHttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename="%s"' % name
        return response
    return HttpResponseForbidden()


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
        not_auto_cloned_fields = ['reference','revision', 'group','lifecycle',
                'auto', 'pfiles']
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

