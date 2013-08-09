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

from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

import openPLM.plmapp.models as models
import openPLM.plmapp.forms as forms
from openPLM.plmapp.views.base import handle_errors, get_generic_data, get_pagination
from openPLM.plmapp.utils import r2r


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
            guest = User.objects.get(username=form.cleaned_data["username"])
            obj.add_user(guest)
            msg = _("Invitation sent to %(name)s") % {"name": guest.get_full_name()}
            messages.info(request, msg)
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
        msg = _("Invitation asked to %(name)s") % {"name": obj.owner.get_full_name()}
        messages.info(request, msg)
        return HttpResponseRedirect("..")
    ctx["ask_form"] = ""
    ctx['current_page'] = 'users'
    ctx['in_group'] = request.user.groups.filter(id=obj.id).exists()
    return r2r("groups/ask_to_join.html", ctx, request)


@handle_errors
def display_plmobjects(request, obj_ref):
    """
    View of the *objects* page of a group.
    """

    obj, ctx = get_generic_data(request, "Group", obj_ref)
    objects = obj.plmobject_group.exclude_cancelled()
    ctx.update(get_pagination(request, objects, "object"))
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
            msg = _("Invitation accepted")
            messages.success(request, msg)
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
            msg = _("Invitation refused")
            messages.info(request, msg)
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
            msg = _("Invitation asked to %(name)s")
            name = inv.owner.get_full_name()
        else:
            obj.send_invitation_to_guest(inv)
            msg = _("Invitation sent to %(name)s")
            name = inv.guest.get_full_name()
        messages.info(request, msg % {"name": name})
    return HttpResponseRedirect("../../../users/")

