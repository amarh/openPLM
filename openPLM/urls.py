############################################################################
# openPLM - open source PLM
# Copyright 2010 Philippe Joulaud, Pierre Cosquer
#/
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
import sys
from django.contrib.auth.views import LoginView
from django.contrib import admin
from django.urls import re_path,include,path
from django.conf import settings
# import custom application models

for app in settings.INSTALLED_APPS:
    if app.startswith("openPLM") and app != "openPLM.apps.pdfgen":
        __import__("%s.models" % app, globals(), locals(), [], 0)

import openPLM.plmapp.search_indexes
from django.conf.urls import *
from openPLM.plmapp.views import *
import openPLM.plmapp.views.api as api
from django.contrib.auth import login, logout
from openPLM.plmapp.csvimport import IMPORTERS
from openPLM.plmapp.utils import can_generate_pdf
import importlib
app_models = importlib.import_module(f"{app}.models")

from django.contrib import admin
admin.autodiscover()
from django.urls import path, re_path, include
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from openPLM.plmapp.views import (
    display_home_page,
    create_object,
    comment_post_wrapper,
    import_csv_init,
    import_csv_apply,
    import_csv_done,
    browse,
    async_search,
    display_object_history,
    redirect_history,
    redirect_from_name,
)

from django.urls import path, re_path, include
from django.contrib import admin
from openPLM.plmapp.views import (
    display_object,
    display_object_attributes,
    display_object_lifecycle,
    display_object_revisions,
    display_object_history,
    display_children,
    edit_children,
    add_child,
    replace_child,
    compare_bom,
    display_parents,
    display_doc_cad,
    add_doc_cad,
    delete_doc_cad,
    display_parts,
    add_part,
    delete_part,
    alternates,
    add_alternate,
    delete_alternate,
    display_files,
    add_file,
    up_file,
    up_progress,
    get_checkin_file,
    checkin_file,
    checkout_file,
    modify_object,
    add_management,
    display_delegation,
    sponsor,
    sponsor_resend_mail,
    delegate,
    modify_user,
    change_user_password,
    navigate,
    download_archive,
    public,
    clone,
    display_related_plmobject,
    display_users,
    group_add_user,
    group_ask_to_join,
    accept_invitation,
    refuse_invitation,
    send_invitation,
    download,
    public_download,
    file_revisions,
)
from openPLM.plmapp.views.main import User_login,user_logout
import openPLM.plmapp.views.ajax as ajax
import openPLM.plmapp.views.api as api
from openPLM.plmapp.csvimport import IMPORTERS
from openPLM.plmapp.utils import can_generate_pdf

admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls)]

urlpatterns+=[
    path('i18n/setlang/', openPLM.plmapp.views.main.set_language),
    path('(?:home/)?$', display_home_page),
    path('accounts/', User_login),
    re_path(r'^(?:accounts/)?login/', User_login),
    path('(?:accounts/)?logout/',user_logout),
    path('object/create/', create_object),
    path('comments/post/', comment_post_wrapper),
    path('comments/', include('django_comments.urls')),
    re_path(r'^import/(?P<target>%s)/$' % "|".join(IMPORTERS.keys()), import_csv_init),
    re_path(r'^import/(?P<target>%s)/(?P<filename>[\w]+)/(?P<encoding>[\w]+)/$' % "|".join(IMPORTERS.keys()), import_csv_apply),
    path('import/done/', import_csv_done),
    re_path(r'^browse/(?P<type>object|part|topassembly|document|user|group)?/', browse),
    path('perform_search/', async_search),
    re_path(r'^timeline/', display_object_history, {"timeline": True}),
    re_path(r'^history_item/(?P<type>object|group|user)/(?P<hid>\d+)/', redirect_history),
    re_path(r'^redirect_name/(?P<type>part|doc)/(?P<name>.+)/$', redirect_from_name),
]
object_pattern = '(?P<obj_type>\w+)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}
urlpatterns += [
   # path('ajax/create/', api.ajax_creation_form),
    path('ajax/complete/(?P<obj_type>\w+)/(?P<field>\w+)/$', ajax.ajax_autocomplete),
    re_path(r'ajax/thumbnails/(?P<date>\d{4}-[01]\d-[0-3]\d:[012]\d:\d\d:\d\d/)?%s?$' % object_pattern,ajax.ajax_thumbnails),
    re_path(r'ajax/navigate/%s?$' % object_pattern, ajax.ajax_navigate),
    re_path(r'ajax/richtext_preview/%s?$' % object_pattern, ajax.ajax_richtext_preview),
    re_path(r'ajax/add_child/(?P<part_id>\d+)/?', ajax.ajax_add_child),
    re_path(r'ajax/can_add_child/(?P<part_id>\d+)/?',ajax.ajax_can_add_child),
    re_path(r'ajax/attach/(?P<plmobject_id>\d+)/?',ajax.ajax_attach),
    re_path(r'ajax/can_attach/(?P<plmobject_id>\d+)/?',ajax.ajax_can_attach),
]

# add custom application urls
for app in settings.INSTALLED_APPS:
    if app.startswith("openPLM"):
        try:
            __import__("%s.urls" % app, globals(), locals(), [], 0)
            mod_patterns = getattr(sys.modules["%s.urls" % app], "urlpatterns")
            urlpatterns += mod_patterns
        except ImportError:
            pass

"""def patterns2(view_prefix, url_prefix, *urls):
    urls2 = []
    for u in urls:
        u2 = u.name
        u2[0] = url_prefix + u2[0]
        urls2.append(tuple(u2))
    return urls"""



object_url = r'^object/' + object_pattern
user_url = r'^user/(?P<obj_ref>[^/]+)/'
group_url = r'^group/(?P<obj_ref>[^/]+)/'
user_dict = {'obj_type':'User', 'obj_revi':'-'}
group_dict = {'obj_type':'Group', 'obj_revi':'-'}

import_url = r'^import/(?P<target>%s)/' % ("|".join(IMPORTERS.keys()))


admin.autodiscover()

urlpatterns += [
    # Object URLs
    path(object_url + '$', display_object),
    path(object_url + 'attributes/', display_object_attributes),
    path(object_url + 'lifecycle/apply/', display_object_lifecycle),
    path(object_url + 'lifecycle/', display_object_lifecycle),
    path(object_url + 'revisions/', display_object_revisions),
    path(object_url + 'history/', display_object_history),
    path(object_url + 'BOM-child/', display_children),
    path(object_url + 'BOM-child/edit/', edit_children),
    path(object_url + 'BOM-child/add/', add_child),
    re_path(object_url + 'BOM-child/replace/(?P<link_id>\d+)/$', replace_child),
    path(object_url + 'BOM-child/diff/', compare_bom),
    path(object_url + 'parents/', display_parents),
    path(object_url + 'doc-cad/', display_doc_cad),
    path(object_url + 'doc-cad/add/', add_doc_cad),
    path(object_url + 'doc-cad/delete/', delete_doc_cad),
    path(object_url + 'parts/', display_parts),
    path(object_url + 'parts/add/', add_part),
    path(object_url + 'parts/delete/', delete_part),
    path(object_url + 'alternates/', alternates),
    path(object_url + 'alternates/add/', add_alternate),
    path(object_url + 'alternates/delete/', delete_alternate),
    path(object_url + 'files/', display_files),
    path(object_url + 'files/add/', add_file),
    path(object_url + 'files/up/', up_file),
    path(object_url + 'files/_up/', up_progress),
    re_path(object_url + 'files/get_checkin/(?P<file_id_value>[^/]+)/$', get_checkin_file),
    re_path(object_url + 'files/checkin/(?P<file_id_value>[^/]+)/$', checkin_file),
    re_path(object_url + 'files/checkout/(?P<docfile_id>[^/]+)/$', checkout_file),
    path(object_url + 'modify/', modify_object),
    path(object_url + 'management/add/', add_management),
    path(object_url + 'management/add-reader/', add_management, {'reader': True}),
    re_path(object_url + 'management/add-signer(?P<level>\d+)/$', add_management),
    re_path(object_url + 'management/replace/(?P<link_id>\d+)/$', replace_management),
    path(object_url + 'management/delete/', delete_management),
    path(object_url + 'navigate/', navigate),
    re_path(object_url + '(?:files/|doc-cad/)?archive/$', download_archive),
    path(object_url + 'public/', public),
    path(object_url + 'clone/', clone),

    # User URLs
    path(user_url + '$', display_object, user_dict),
    path(user_url + 'attributes/', display_object_attributes, user_dict),
    path(user_url + 'history/', display_object_history, user_dict),
    path(user_url + 'parts-doc-cad/', display_related_plmobject, user_dict),
    path(user_url + 'delegation/delete/', display_delegation),
    path(user_url + 'delegation/sponsor/', sponsor),
    path(user_url + 'delegation/sponsor/mail/', sponsor_resend_mail),
    re_path(user_url + 'delegation/delegate/(?P<role>[^/]+)/$', delegate, {'sign_level': 'none'}),
    re_path(user_url + 'delegation/delegate/(?P<role>[^/]+)/(?P<sign_level>\d+|all)/$', delegate),
    path(user_url + 'modify/', modify_user),
    path(user_url + 'password/', change_user_password),
    path(user_url + 'navigate/', navigate, user_dict),
    path(user_url + 'groups/', display_groups),
    path(user_url + 'files/', upload_and_create),
    path(user_url + 'files/add/', add_file, user_dict),
    path(user_url + 'files/up/', up_file, user_dict),
    path(user_url + 'files/_up/', up_progress, user_dict),
    
    
    # Group URLs
        path(group_url+'', display_object, group_dict),
        path(group_url+'attributes/', display_object_attributes, group_dict),
        path(group_url+'history/', display_object_history, group_dict),
        path(group_url+'objects/', display_plmobjects),
        path(group_url+'navigate/', navigate, group_dict),
        path(group_url+'users/', display_users),
        path(group_url+'users/add/', group_add_user),
        path(group_url+'users/join/', group_ask_to_join),
        re_path(group_url+r'invitation/accept/(?P<token>\d+)/$', accept_invitation),
        re_path(group_url+r'invitation/refuse/(?P<token>\d+)/$', refuse_invitation),
        re_path(group_url+r'invitation/send/(?P<token>\d+)/$', send_invitation),
    
    
    # Media URLs
   # path('media/<path>', django.views.static.serve, {'document_root': 'media/'}),
    re_path(r'file/(?P<docfile_id>\d+)/$', download),
    re_path(r'file/(?P<docfile_id>\d+)/(?:.*)$', download),
    re_path(r'file/public/(?P<docfile_id>\d+)/$', public_download),
    re_path(r'file/public/(?P<docfile_id>\d+)/(?:.*)$', public_download),
    re_path(r'file/revisions/(?P<docfile_id>\d+)/', file_revisions),
]

# API URLs
api_url = r'^api/object/(?P<doc_id>\d+)/'

urlpatterns += [
    path('api/login/', api.api_login),
    path('api/needlogin/', api.need_login),
    path('api/testlogin/', api.test_login),
    path('api/types/', api.get_all_types),
    path('api/parts/', api.get_all_parts),
    path('api/docs/', api.get_all_docs),
    path('api/search/', api.search),
    re_path(r'api/search/(?P<editable_only>true|false)/$', api.search),
    re_path(r'api/search/(?P<editable_only>true|false)/(?P<with_file_only>true|false)/$', api.search),
    path('api/create/', api.create),
    re_path(r'api/search_fields/(?P<typename>[\w_]+)/$', api.get_search_fields),
    re_path(r'api/creation_fields/(?P<typename>[\w_]+)/$', api.get_creation_fields),
    re_path(r'api/get/(?P<obj_id>\d+)/', api.get_object),
    re_path(r'api/object/(?P<part_id>\d+)/attached_documents/', api.get_attached_documents),
    path('api/lock_files/', api.lock_files),
]

urlpatterns += [
        path(api_url+'files/', api.get_files),
        re_path(api_url+r'files/(?P<all_files>all)/$', api.get_files),
        path(api_url+'revise/', api.revise),
        path(api_url+'add_file/', api.add_file),
        re_path(api_url+r'add_file/thumbnail/$', api.add_file, {"thumbnail": True}),
        re_path(api_url+r'attach_to_part/(?P<part_id>\d+)/$', api.attach_to_part),
        path(api_url+'next_revision/', api.next_revision),
        path(api_url+'is_revisable/', api.is_revisable),
        re_path(api_url+r'(?:lock|checkout)/(?P<df_id>\d+)/$', api.check_out),
        re_path(api_url+r'unlock/(?P<df_id>\d+)/$', api.unlock),
        re_path(api_url+r'is_locked/(?P<df_id>\d+)/$', api.is_locked),
        re_path(api_url+r'checkin/(?P<df_id>\d+)/$', api.check_in),
        re_path(api_url+r'checkin/(?P<df_id>\d+)/thumbnail/$', api.check_in, {"thumbnail": True}),
        re_path(api_url+r'add_thumbnail/(?P<df_id>\d+)/$', api.add_thumbnail),
        path(api_url+'attached_parts/', api.get_attached_parts),
]











from haystack.views import search_view_factory
from openPLM.plmapp.forms import SimpleSearchForm

urlpatterns +=[re_path(r'^search/', search_view_factory(
        view_class=OpenPLMSearchView,
        template="search/search.html",
        form_class=SimpleSearchForm
    ), name='haystack_search'),]

urlpatterns += [ path('/calender',include('apps.calendrier.urls')),
                #path('/document',include('apps.document3D.urls')),
                path('/ecr',include('apps.ecr.urls')),
                path('/rss',include('apps.rss.urls')),
                path('/subversion',include('apps.subversion.urls')),
] 