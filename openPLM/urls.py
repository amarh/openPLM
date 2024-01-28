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


urlpatterns =[]
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

object_pattern = '(?P<obj_type>\w+)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

object_url = r'^object/' + object_pattern
user_url = r'^user/(?P<obj_ref>[^/]+)/'
group_url = r'^group/(?P<obj_ref>[^/]+)/'
user_dict = {'obj_type':'User', 'obj_revi':'-'}
group_dict = {'obj_type':'Group', 'obj_revi':'-'}

import_url = r'^import/(?P<target>%s)/' % ("|".join(IMPORTERS.keys()))

urlpatterns = [
    re_path(r'^admin/',admin.site.urls),
    re_path (r'^i18n/setlang/',openPLM.plmapp.views.main.set_language),
    re_path(r'^(?:home/)?$', display_home_page),
    re_path(r'^accounts/?$', login, {'template_name': 'login.html', 'redirect_field_name': 'next'},"login"),
    re_path(r'^(?:accounts/)?login/', login, {'template_name': 'login.html', 'redirect_field_name': 'next'}),
    re_path(r'^(?:accounts/)?logout/', logout, {'next_page': '/login/', }),
    re_path(r'^object/create/$', create_object),
    re_path(r'^comments/post/', comment_post_wrapper),
    re_path(r'^comments/', include('django_comments.urls')),
    re_path(import_url + '$', import_csv_init),
    re_path(import_url + '(?P<filename>[\w]+)/(?P<encoding>[\w]+)/$',import_csv_apply),
    re_path('^import/done/$', import_csv_done),
    re_path(r'^browse/(?P<type>object|part|topassembly|document|user|group)?/',openPLM.plmapp.views.main.browse),
    re_path(r'^perform_search/$',async_search),
    re_path('^timeline/', display_object_history, {"timeline" : True}),
    re_path('^history_item/(?P<type>object|group|user)/(?P<hid>\d+)/', redirect_history),
    re_path('^redirect_name/(?P<type>part|doc)/(?P<name>.+)/$', redirect_from_name),]

urlpatterns +=[
    re_path(r'create/$', ajax_creation_form),
    re_path(r'complete/(?P<obj_type>\w+)/(?P<field>\w+)/$', ajax_autocomplete),
    re_path(r'thumbnails/(?P<date>\d{4}-[01]\d-[0-3]\d:[012]\d:\d\d:\d\d/)?%s?$' % object_pattern, ajax_thumbnails),
    re_path(r'navigate/%s?$' % object_pattern, ajax_navigate),
    re_path(r'richtext_preview/%s?$' % object_pattern, ajax_richtext_preview),
    re_path(r'add_child/(?P<part_id>\d+)/?', ajax_add_child),
    re_path(r'can_add_child/(?P<part_id>\d+)/?', ajax_can_add_child),
    re_path(r'attach/(?P<plmobject_id>\d+)/?', ajax_attach),
    re_path(r'can_attach/(?P<plmobject_id>\d+)/?', ajax_can_attach),
]
urlpatterns += [
    re_path(r'$', display_object),
    re_path(r'attributes/$', display_object_attributes),
    re_path(r'lifecycle/(?:apply/)?$', display_object_lifecycle),
    re_path(r'revisions/$', display_object_revisions),
    re_path(r'history/$', display_object_history),
    re_path(r'BOM-child/$', display_children),
    re_path(r'BOM-child/edit/$', edit_children),
    re_path(r'BOM-child/add/$', add_child),
    re_path(r'BOM-child/replace/(?P<link_id>\d+)/$', replace_child),
    re_path(r'BOM-child/diff/$', compare_bom),
    re_path(r'parents/$', display_parents),
    re_path(r'doc-cad/$', display_doc_cad),
    re_path(r'doc-cad/add/$', add_doc_cad),
    re_path(r'doc-cad/delete/$', delete_doc_cad),
    re_path(r'parts/$', display_parts),
    re_path(r'parts/add/$', add_part),
    re_path(r'parts/delete/$', delete_part),
    re_path(r'alternates/$', alternates),
    re_path(r'alternates/add/$', add_alternate),
    re_path(r'alternates/delete/$', delete_alternate),
    re_path(r'files/$', display_files),
    re_path(r'files/add/$', add_file),
    re_path(r'files/up/$', up_file),
    re_path(r'files/_up/$', up_progress),
    re_path(r'files/get_checkin/(?P<file_id_value>[^/]+)/$',get_checkin_file),
    re_path(r'files/checkin/(?P<file_id_value>[^/]+)/$', checkin_file),
    re_path(r'files/checkout/(?P<docfile_id>[^/]+)/$', checkout_file),
    re_path(r'modify/$', modify_object),
    re_path(r'management/add/$', add_management),
    re_path(r'management/add-reader/$', add_management, dict(reader=True)),
    re_path(r'management/add-signer(?P<level>\d+)/$', add_management),
    re_path(r'management/replace/(?P<link_id>\d+)/$', replace_management),
    re_path(r'management/delete/$', delete_management),
    re_path(r'navigate/$', navigate),
    re_path(r'(?:files/|doc-cad/)?archive/$', download_archive),
    re_path(r'public/$', public),
    re_path(r'clone/$', clone),
]

urlpatterns += [
    re_path(r'$', display_object, user_dict),
    re_path(r'attributes/$', display_object_attributes, user_dict),
    re_path(r'history/$', display_object_history, user_dict),
    re_path(r'parts-doc-cad/$', display_related_plmobject, user_dict),
    re_path(r'delegation/(?:delete/)?$', display_delegation),
    re_path(r'delegation/sponsor/$', sponsor),
    re_path(r'delegation/sponsor/mail/$', sponsor_resend_mail),
    re_path(r'delegation/delegate/(?P<role>[^/]+)/$', delegate,{'sign_level':'none'}),
    re_path(r'delegation/delegate/(?P<role>[^/]+)/(?P<sign_level>\d+|all)/$', delegate),
    re_path(r'modify/$', modify_user),
    re_path(r'password/$', change_user_password),
    re_path(r'navigate/$', navigate, user_dict),
    re_path(r'groups/$', display_groups),
    # same as document files urls
    re_path(r'files/$', upload_and_create),
    re_path(r'files/add/$', add_file, user_dict),
    re_path(r'files/up/$', up_file, user_dict),
    re_path(r'files/_up/$', up_progress, user_dict),]



urlpatterns += [
    path('', display_object, group_dict),
    path('attributes/', display_object_attributes, group_dict),
    path('history/', display_object_history, group_dict),
    path('objects/', display_plmobjects),
    path('navigate/', navigate, group_dict),
    path('users/', display_users),
    path('users/add/', group_add_user),
    path('users/join/', group_ask_to_join),
    re_path(r'invitation/accept/(?P<token>\d+)/$', accept_invitation),
    re_path(r'invitation/refuse/(?P<token>\d+)/$', refuse_invitation),
    re_path(r'invitation/send/(?P<token>\d+)/$', send_invitation),
]

urlpatterns +=[
	# In order to take into account the css file
    #re_path(r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root' : 'media/'}),
    re_path(r'^file/(?P<docfile_id>\d+)/$', download),
    re_path(r'^file/(?P<docfile_id>\d+)/(?:.*)$', download),
    re_path(r'^file/public/(?P<docfile_id>\d+)/$', public_download),
    re_path(r'^file/public/(?P<docfile_id>\d+)/(?:.*)$', public_download),
    re_path(r'^file/revisions/(?P<docfile_id>\d+)/', file_revisions)
]



# urls related to the api
api_url = r'^api/object/(?P<doc_id>\d+)/'
api_urlpatterns =[
    path(api_url,include([path('login/', api.api_login),
            path('needlogin/', api.need_login),
            path('testlogin/', api.test_login),
            path('types/', api.get_all_types),
            path('parts/', api.get_all_parts),
            path('doc/', api.get_all_docs),
            path('search/', api.search),
            path('search/<str:editable_only>/<str:with_file_only>/true |false',api.search),
            path('create/', api.create),
            path('search_fields/<str:typename>/', api.get_search_fields),
            re_path(r'^creation_fields/(?P<typename>[\w_]+)/', api.get_creation_fields),
            path('get/<int:obj_id>/', api.get_object),
            path('object/<int:part_id>/attached_documents/', api.get_attached_documents),
            path(r'lock_files/', api.lock_files),
            ])
        )]

urlpatterns+=api_urlpatterns

urlpatterns +=[
    path('files/', api.get_files),
    path('files/<str:all_files>)/', api.get_files),
    path('revise/', api.revise),
    path('add_file/', api.add_file),
    re_path(r'^add_file/thumbnail/$', api.add_file, {"thumbnail" : True}),
    re_path(r'^attach_to_part/(?P<part_id>\d+)/$', api.attach_to_part),
    re_path(r'^next_?revision/$', api.next_revision),
    re_path(r'^is_?revisable/$', api.is_revisable),
    re_path(r'^(?:lock|checkout)/(?P<df_id>\d+)/$', api.check_out),
    re_path(r'^unlock/(?P<df_id>\d+)/$', api.unlock),
    re_path(r'^is_?locked/(?P<df_id>\d+)/$', api.is_locked),
    re_path(r'^checkin/(?P<df_id>\d+)/$', api.check_in),
    re_path(r'^checkin/(?P<df_id>\d+)/thumbnail/$', api.check_in, {"thumbnail" : True}),
    re_path(r'^add_thumbnail/(?P<df_id>\d+)/$', api.add_thumbnail),
    path('attached_parts/', api.get_attached_parts),
]

from haystack.views import search_view_factory
from openPLM.plmapp.forms import SimpleSearchForm

urlpatterns +=[re_path(r'^search/', search_view_factory(
        view_class=OpenPLMSearchView,
        template="search/search.html",
        form_class=SimpleSearchForm
    ), name='haystack_search'),]

