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

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import (HttpResponseRedirect, Http404,
                        HttpResponseForbidden, HttpResponseBadRequest)
from django.utils.translation import ugettext_lazy as _

import openPLM.plmapp.models as models
import openPLM.plmapp.forms as forms
from openPLM.plmapp.views.base import (get_obj_from_form,
    handle_errors, get_generic_data, register_creation_view)
from openPLM.plmapp.exceptions import ControllerError, PermissionError
from openPLM.plmapp.utils import level_to_sign_str, r2r


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
            new_user.profile.language = form.cleaned_data["language"]
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
    url = request.user.profile.plmobject_url + "delegation/sponsor/"
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
            msg = _("Mail resent to %(name)s") % {"name": link.delegatee.get_full_name()}
            messages.info(request, msg)
        except (KeyError, ValueError, ControllerError):
            return HttpResponseForbidden()
    return HttpResponseRedirect("../../")


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
        modification_form = forms.OpenPLMUserChangeForm(request.POST, request.FILES)
        if modification_form.is_valid():
            obj.update_from_form(modification_form)
            messages.success(request, _(u"Your profile has been modified."))
            return HttpResponseRedirect("/user/%s/" % obj.username)
    else:
        modification_form = forms.OpenPLMUserChangeForm(instance=obj.object)

    ctx["modification_form"] = modification_form
    return r2r('edit.html', ctx, request)



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
            messages.info(request, _(u"Your password has been modified successfully."))
            return HttpResponseRedirect("/user/%s/" % obj.username)
    else:
        modification_form = PasswordChangeForm(obj)

    ctx["modification_form"] = modification_form
    return r2r('users/password.html', ctx, request)

