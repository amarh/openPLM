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
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pierre.cosquer@insa-rennes.fr
################################################################################

import urlparse

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.simplejson import JSONEncoder
from django.views.decorators.cache import cache_page
from django.http import HttpResponse, HttpResponseForbidden

import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PLMObjectController
import openPLM.plmapp.forms as forms
from openPLM.plmapp.base_views import get_obj, get_obj_by_id, get_obj_from_form, \
        json_view, get_navigate_data, secure_required 

@secure_required
@login_required
def ajax_search_form(request):
    """
    Simple view which returns the html of a search form with the data
    of :attr:`request.GET` as initial values.
    
    The request must contains a get parameter *type* with a valid type,
    otherwise, a :class:`.HttpResponseForbidden` is returned.
    """
    tf = forms.TypeForm(request.GET)
    if tf.is_valid():
        cls = models.get_all_users_and_plmobjects()[tf.cleaned_data["type"]]
        form = forms.get_search_form(cls, request.GET)
        return HttpResponse(form.as_table())
    else:
        return HttpResponseForbidden()

@secure_required
@login_required
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
       return HttpResponse(mimetype='text/plain')
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
    if field not in cls._meta.get_all_field_names():
        return HttpResponseForbidden()
    results = cls.objects.filter(**{"%s__icontains" % field : term})
    results = results.values_list(field, flat=True).order_by(field).distinct()
    json = JSONEncoder().encode(list(str(r) for r in results[:limit]))  
    return HttpResponse(json, mimetype='application/json')

@login_required
@json_view
def ajax_thumbnails(request, obj_type, obj_ref, obj_revi):
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
    for f in obj.files:
        if f.thumbnail:
            img = f.thumbnail.url 
        else:
            img = urlparse.urljoin(settings.MEDIA_URL, "img/image-missing.png")
        files.append((f.filename, "/file/%d/" % f.id, img))
    return dict(files=files, doc=doc)


@login_required
@json_view
def ajax_navigate(request, obj_type, obj_ref, obj_revi):
    context = get_navigate_data(request, obj_type, obj_ref, obj_revi)
    data = {
            "img" : context["picture_path"],
            "width" : context["img_width"],
            "height" : context["img_height"],
            "divs" : context["map_areas"],
            "left" : context["x_img_position"],
            "top" : context["y_img_position"],
            "form" : context["filter_object_form"].as_ul(),
            "center_x" : context["center_x"],
            "center_y" : context["center_y"],
            }
    return data

@login_required
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

@login_required
@json_view
def ajax_can_add_child(request, part_id):
    part = get_obj_by_id(part_id, request.user)
    data = {"can_add" : False}
    if part.is_part and request.GET:
        form = forms.AddRelPartForm(request.GET)
        if form.is_valid():
            child = get_obj_from_form(form, request.user)
            data["can_add"] = part.can_add_child(child)
    return data

@login_required
@json_view
def ajax_attach(request, plmobject_id):
    plmobject = get_obj_by_id(plmobject_id, request.user)
    data = {}
    if request.GET:
        form = forms.AddRelPartForm(initial=request.GET)
    else:
        form = forms.AddRelPartForm(request.POST)
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

@login_required
@json_view
def ajax_can_attach(request, plmobject_id):
    plmobject = get_obj_by_id(plmobject_id, request.user)
    data = {"can_attach" : False}
    if isinstance(plmobject, PLMObjectController) and request.GET:
        form = forms.AddRelPartForm(request.GET)
        if form.is_valid():
            attached = get_obj_from_form(form, request.user)
            if attached.check_readable(False):
                if hasattr(plmobject, "can_attach_document"):
                    data["can_attach"] = plmobject.can_attach_document(attached)
                elif hasattr(plmobject, "can_attach_part"):
                    data["can_attach"] = plmobject.can_attach_part(attached)
    return data

