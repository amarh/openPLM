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
Ajax views.
"""

import time
import datetime
import urlparse


from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.forms import widgets
from json import JSONEncoder
from django.views.decorators.cache import cache_page
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string

import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PLMObjectController
import openPLM.plmapp.forms as forms
from openPLM.plmapp.views.base import get_obj, get_obj_by_id, get_obj_from_form, \
        json_view, get_navigate_data, secure_required, get_creation_view
from openPLM.plmapp.filters import richtext

from openPLM.plmapp.navigate import TIME_FORMAT

ajax_login_required = user_passes_test(lambda u: (u.is_authenticated()
    and not u.profile.restricted))

@ajax_login_required
@json_view
def ajax_creation_form(request):
    """
    Simple view which returns the html of a creation form with the data
    of :attr:`request.GET` as initial values.

    The request must contains a get parameter *type* with a valid type,
    otherwise, a :class:`.HttpResponseForbidden` is returned.
    """
    tf = forms.TypeForm(request.GET)
    if tf.is_valid():
        type_ = tf.cleaned_data["type"]
        request.session["type"] = type_
        request.session.save()
        cls = models.get_all_users_and_plmobjects()[type_]
        view = get_creation_view(cls)
        if view is not None:
            return {"reload" : True}
        initial = dict(request.GET.iteritems())
        if "pfiles" in request.GET:
            initial["pfiles"] = request.GET.getlist("pfiles")
        if "reference" in initial:
            # gets a new reference if the type switches from a part to a document
            # and vice versa, see ticket #99
            ref = initial["reference"]
            if (ref.startswith("DOC_") and type_ in models.get_all_parts()) or \
               (ref.startswith("PART_") and type_ in models.get_all_documents()):
                del initial["reference"]
        form = forms.get_creation_form(request.user, cls, initial=initial)
        return {"reload" : False, "form" : form.as_table(),
                "type" : type_, "form_media": form.media.render(), }
    else:
        return HttpResponseForbidden()



@secure_required
@ajax_login_required
@cache_page(60 * 60)
def ajax_autocomplete(request, obj_type, field):
    """
    Simple ajax view for JQquery.UI.autocomplete. This returns the possible
    completions (in JSON format) for *field*. The request must contains
    a get parameter named *term* which should be the string used to filter
    the results. *obj_type* must be a valid typename.

    :param str obj_type: a valid typename (like ``"part"``)
    :param str field: a valid field (like ``"name"``)
    """
    if not request.GET.get('term'):
       return HttpResponse(content_type='text/plain')
    term = request.GET.get('term')
    limit = 50
    try:
        cls = models.get_all_users_and_plmobjects()[obj_type]
    except KeyError:
        return HttpResponseForbidden()
    if hasattr(cls, "attributes"):
        if field not in cls(__fake__=True).attributes:
            return HttpResponseForbidden()
    elif cls == models.User:
        if field not in ("email", "first_name", "last_name"):
            return HttpResponseForbidden()
        if getattr(settings, "HIDE_EMAILS", False) and field == "email":
            return HttpResponseForbidden()
    if field not in cls._meta.get_all_field_names():
        return HttpResponseForbidden()
    results = cls.objects.filter(**{"%s__icontains" % field : term})
    results = results.values_list(field, flat=True).order_by(field).distinct()
    json = JSONEncoder().encode(list(str(r) for r in results[:limit]))
    return HttpResponse(json, content_type='application/json')

@ajax_login_required
@json_view
def ajax_thumbnails(request, obj_type, obj_ref, obj_revi, date=None):
    """
    Ajax view to get files and thumbnails of a document.

    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    """
    obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
    files = []
    doc = "|".join((obj_type, obj_ref, obj_revi))
    if date:
        d = datetime.datetime(*time.strptime(date, TIME_FORMAT)[:6])
        fileset = obj.documentfile_set.filter(ctime__lte=d).exclude(end_time__gt=d)
    else:
        fileset = obj.files
    missing_url = urlparse.urljoin(settings.STATIC_URL, "img/image-missing.png")
    for f in fileset:
        if f.thumbnail:
            img = f.thumbnail.url
        else:
            img = missing_url
        files.append({
            "name": f.filename,
            "url": "/file/%d/" % f.id,
            "img": img,
            "revision" : f.revision,
            "deleted" : f.deleted,
            "deprecated" : f.deprecated,
        })
    return dict(files=files, doc=doc)


@ajax_login_required
@json_view
def ajax_navigate(request, obj_type, obj_ref, obj_revi):
    context = get_navigate_data(request, obj_type, obj_ref, obj_revi)
    data = {
            "width" : context["img_width"],
            "height" : context["img_height"],
            "divs" : context["map_areas"],
            "form" : context["filter_object_form"].as_ul(),
            "edges" : context["edges"],
            "add_buttons" : render_to_string("navigate/add_buttons.html", context),
            "past" : context["past"],
            }
    return data

@ajax_login_required
@json_view
def ajax_add_child(request, part_id):
    part = get_obj_by_id(part_id, request.user)
    data = {}
    if request.GET:
        form = forms.AddChildForm(part.object, initial=request.GET)
    else:
        form = forms.AddChildForm(part.object, request.POST)
        if form.is_valid():
            child = get_obj_from_form(form, request.user)
            part.add_child(child, form.cleaned_data["quantity"],
                           form.cleaned_data["order"],
                           form.cleaned_data["unit"],
                           **form.extensions)
            return {"result" : "ok"}
        else:
            data["result"] = "error"
            data["error"] = "invalid form"
    form.fields["type"].widget = widgets.TextInput()
    for field in ("type", "reference", "revision"):
        form.fields[field].widget.attrs['readonly'] = 'on'
    data.update({
            "parent" : {
                "id" : part.id,
                "type" : part.type,
                "reference" : part.reference,
                "revision" : part.revision,
                },
            "form" : form.as_table()
           })
    return data

@ajax_login_required
@json_view
def ajax_can_add_child(request, part_id):
    part = get_obj_by_id(part_id, request.user)
    data = {"can_add" : False}
    if part.is_part and request.GET:
        form = forms.AddPartForm(request.GET)
        if form.is_valid():
            child = get_obj_from_form(form, request.user)
            data["can_add"] = part.can_add_child(child)
    return data

@ajax_login_required
@json_view
def ajax_attach(request, plmobject_id):
    plmobject = get_obj_by_id(plmobject_id, request.user)
    data = {}
    if request.GET:
        form = forms.PLMObjectForm(initial=request.GET)
    else:
        form = forms.PLMObjectForm(request.POST)
        if form.is_valid():
            attached = get_obj_from_form(form, request.user)
            if hasattr(plmobject, "attach_to_document"):
                plmobject.attach_to_document(attached)
            elif hasattr(plmobject, "attach_to_part"):
                plmobject.attach_to_part(attached)
            return {"result" : "ok"}
        else:
            data["result"] = "error"
            data["error"] = "invalid form"
    for field in ("type", "reference", "revision"):
        form.fields[field].widget.attrs['readonly'] = 'on'
    data.update({
            "plmobject" : {
                "id" : plmobject.id,
                "type" : plmobject.type,
                "reference" : plmobject.reference,
                "revision" : plmobject.revision,
                },
            "form" : form.as_table()
           })
    return data

@ajax_login_required
@json_view
def ajax_can_attach(request, plmobject_id):
    plmobject = get_obj_by_id(plmobject_id, request.user)
    data = {"can_attach" : False}
    if isinstance(plmobject, PLMObjectController) and request.GET:
        form = forms.PLMObjectForm(request.GET)

        if form.is_valid():
            attached = get_obj_from_form(form, request.user)
            if attached.check_readable(False):
                if hasattr(plmobject, "can_attach_document"):
                    data["can_attach"] = plmobject.can_attach_document(attached)
                elif hasattr(plmobject, "can_attach_part"):
                    data["can_attach"] = plmobject.can_attach_part(attached)
    return data


@ajax_login_required
@json_view
def ajax_richtext_preview(request, obj_type, obj_ref, obj_revi):
    """
    Ajax view to get an HTML preview of a raw content (in richtext
    syntax).

    GET paramerer:

        ``content``
            raw content to be rendered

    This view returns a JSON response with one key, ``html``, the rendered
    content that can be included in a div element.
    """
    content = request.GET["content"]
    if obj_type in ("create", "object"):
        return {"html": richtext(content, None)}
    obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
    obj.check_readable()
    return {"html": richtext(content, obj)}

