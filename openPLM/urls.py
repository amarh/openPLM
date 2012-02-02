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

import sys

from django.conf import settings

# import custom application models
for app in settings.INSTALLED_APPS:
    if app.startswith("openPLM"):
        __import__("%s.models" % app, globals(), locals(), [], -1)

import openPLM.plmapp.search_indexes

from django.conf.urls.defaults import include, patterns, url
from openPLM.plmapp.views import *
import openPLM.plmapp.views.api as api
from django.contrib.auth.views import login, logout
from openPLM.plmapp.csvimport import IMPORTERS

from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('')
# add custom application urls
for app in settings.INSTALLED_APPS:
    if app.startswith("openPLM"):
        try:
            __import__("%s.urls" % app, globals(), locals(), [], -1)
            mod_patterns = getattr(sys.modules["%s.urls" % app], "urlpatterns")
            urlpatterns += mod_patterns
        except ImportError:
            pass

def patterns2(view_prefix, url_prefix, *urls):
    urls2 = []
    for u in urls:
        u2 = list(u)
        u2[0] = url_prefix + u2[0]
        urls2.append(tuple(u2))
    return patterns(view_prefix, *urls2)

object_pattern = '(?P<obj_type>\w+)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

object_url = r'^object/' + object_pattern
user_url = r'^user/(?P<obj_ref>[^/]+)/'
group_url = r'^group/(?P<obj_ref>[^/]+)/'
user_dict = {'obj_type':'User', 'obj_revi':'-'}
group_dict = {'obj_type':'Group', 'obj_revi':'-'}

import_url = r'^import/(?P<target>%s)/' % ("|".join(IMPORTERS.keys()))

urlpatterns += patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),

    (r'^(?:home/)?$', display_home_page),
    (r'^accounts/?$', login, {'template_name': 'DisplayLoginPage.htm', 'redirect_field_name': 'next'}),
    (r'^(?:accounts/)?login/', login, {'template_name': 'DisplayLoginPage.htm', 'redirect_field_name': 'next'}),
    (r'^(?:accounts/)?logout/', logout, {'next_page': '/login/', }),
    (r'^object/create/$', create_object),
    (r'^comments/', include('django.contrib.comments.urls')),
    (import_url + '$', import_csv_init),
    (import_url + '(?P<filename>[\w]+)/(?P<encoding>[\w]+)/$',
        import_csv_apply),
    ('^import/done/$', import_csv_done),
    )

urlpatterns += patterns2('', 'ajax/', 
    (r'search/$', ajax_search_form),
    (r'complete/(?P<obj_type>\w+)/(?P<field>\w+)/$', ajax_autocomplete),
    (r'thumbnails/%s?$' % object_pattern, ajax_thumbnails),
    (r'navigate/%s?$' % object_pattern, ajax_navigate),
    (r'add_child/(?P<part_id>\d+)/?', ajax_add_child),
    (r'can_add_child/(?P<part_id>\d+)/?', ajax_can_add_child),
    (r'attach/(?P<plmobject_id>\d+)/?', ajax_attach),
    (r'can_attach/(?P<plmobject_id>\d+)/?', ajax_can_attach),
)

urlpatterns += patterns2('', object_url,
    (r'$', display_object),
    (r'attributes/$', display_object_attributes),
    (r'lifecycle/$', display_object_lifecycle),
    (r'revisions/$', display_object_revisions),
    (r'history/$', display_object_history),
    (r'BOM-child/$', display_object_child),
    (r'BOM-child/edit/$', edit_children),
    (r'BOM-child/add/$', add_children),
    (r'parents/$', display_object_parents),
    (r'doc-cad/$', display_object_doc_cad),
    (r'doc-cad/add/$', add_doc_cad),
    (r'parts/$', display_related_part),
    (r'parts/add/$', add_rel_part),
    (r'files/$', display_files),
    (r'files/add/$', add_file),
    (r'files/checkin/(?P<file_id_value>[^/]+)/$', checkin_file),
    (r'files/checkout/(?P<docfile_id>[^/]+)/$', checkout_file),
    (r'modify/$', modify_object),
    (r'management/$', display_management),
    (r'management/add/$', add_management),
    (r'management/replace/(?P<link_id>\d+)/$', replace_management),
    (r'management/delete/$', delete_management),
    (r'navigate/$', navigate),
    (r'(?:files/|doc-cad/)?archive/$', download_archive),
)


urlpatterns += patterns2('', user_url, 
    (r'$', display_object, user_dict),
    (r'attributes/$', display_object_attributes, user_dict),
    (r'history/$', display_object_history, user_dict),
    (r'parts-doc-cad/$', display_related_plmobject, user_dict),
    (r'delegation/$', display_delegation),
    (r'delegation/sponsor/$', sponsor),
    (r'delegation/delegate/(?P<role>[^/]+)/$', delegate,
                    {'sign_level':'none'}),
    (r'delegation/delegate/(?P<role>[^/]+)/(?P<sign_level>\d+|all)/$', delegate),
    (r'modify/$', modify_user),
    (r'password/$', change_user_password),
    (r'navigate/$', navigate, user_dict),
    (r'groups/$', display_groups),
)

urlpatterns += patterns2('', group_url, 
    (r'$', display_object, group_dict),
    (r'attributes/$', display_object_attributes, group_dict),
    (r'history/$', display_object_history, group_dict),
    (r'objects/$', display_plmobjects),
    (r'users/$', display_users),
    (r'users/add/$', group_add_user),
    (r'users/join/$', group_ask_to_join),
    (r'invitation/accept/(?P<token>\d+)/$', accept_invitation),
    (r'invitation/refuse/(?P<token>\d+)/$', refuse_invitation),
    #(r'navigate/$', navigate, group_dict),
)
urlpatterns += patterns('',
	# In order to take into account the css file
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root' : 'media/'}),    
    (r'^file/(?P<docfile_id>\d+)/$', download),
    (r'^file/(?P<docfile_id>\d+)/(?P<filename>.*)$', download),
)

# urls related to the api
api_url = r'^api/object/(?P<doc_id>\d+)/'
urlpatterns += patterns2('', '^api/',
    (r'login/', api.api_login),
    (r'needlogin/', api.need_login),
    (r'testlogin/', api.test_login),
    (r'types/$', api.get_all_types),
    (r'parts/$', api.get_all_parts),
    (r'doc(?:ument)?s/$', api.get_all_docs),
    (r'search/$', api.search),
    (r'search/(?P<editable_only>true|false)/$', api.search),
    (r'search/(?P<editable_only>true|false)/(?P<with_file_only>true|false)/$',
     api.search),
    (r'create/$', api.create),
    (r'search_fields/(?P<typename>[\w_]+)/$', api.get_search_fields),
    (r'creation_fields/(?P<typename>[\w_]+)/$', api.get_creation_fields),
    )

urlpatterns += patterns2('', api_url,
    (r'files/$', api.get_files),
    (r'files/(?P<all_files>all)/$', api.get_files),
    (r'revise/$', api.revise),
    (r'add_file/$', api.add_file),
    (r'add_file/thumbnail/$', api.add_file, {"thumbnail" : True}),
    (r'attach_to_part/(?P<part_id>\d+)/$', api.attach_to_part),
    (r'next_?revision/$', api.next_revision),
    (r'is_?revisable/$', api.is_revisable),
    (r'(?:lock|checkout)/(?P<df_id>\d+)/$', api.check_out),
    (r'unlock/(?P<df_id>\d+)/$', api.unlock),
    (r'is_?locked/(?P<df_id>\d+)/$', api.is_locked),
    (r'checkin/(?P<df_id>\d+)/$', api.check_in),
    (r'checkin/(?P<df_id>\d+)/thumbnail/$', api.check_in, {"thumbnail" : True}),
    (r'add_thumbnail/(?P<df_id>\d+)/$', api.add_thumbnail),
)

from haystack.views import search_view_factory
from openPLM.plmapp.forms import SimpleSearchForm

urlpatterns += patterns('haystack.views',
    url(r'^search/', search_view_factory(
        view_class=OpenPLMSearchView,
        template="search/search.htm",
        form_class=SimpleSearchForm
    ), name='haystack_search'),
)

