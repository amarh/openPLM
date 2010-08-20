import sys

from django.conf import settings
from django.conf.urls.defaults import *
from openPLM.plmapp.views import *
import openPLM.plmapp.api as api
from django.contrib.auth.views import login, logout

from django.contrib import admin
admin.autodiscover()

object_url = r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/'
user_url = r'^user/(?P<obj_ref>[^/]+)/'
user_dict = {'obj_type':'User', 'obj_revi':'-'}
urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),

    (r'^bollox/', display_bollox),
    (r'^(?:accounts/)?login/', login, {'template_name': 'DisplayLoginPage.htm', }),
    (r'^(?:accounts/)?logout/', logout, {'next_page': '/login/', }),
    (r'^home/', display_home_page),
    (r'^object/create/$', create_object),
    
    (object_url + r'$', display_object),
    (object_url + r'attributes/$', display_object_attributes),
    (object_url + r'lifecycle/$', display_object_lifecycle),
    (object_url + r'revisions/$', display_object_revisions),
    (object_url + r'history/$', display_object_history),
    (object_url + r'BOM-child/$', display_object_child),
    (object_url + r'BOM-child/edit/$', edit_children),
    (object_url + r'BOM-child/add/$', add_children),
    (object_url + r'parents/$', display_object_parents),
    (object_url + r'doc-cad/$', display_object_doc_cad),
    (object_url + r'doc-cad/add/$', add_doc_cad),
    (object_url + r'parts/$', display_related_part),
    (object_url + r'parts/add/$', add_rel_part),
    (object_url + r'files/$', display_files),
    (object_url + r'files/add/$', add_file),
    (object_url + r'files/checkin/([^/]+)/$', checkin_file),
    (object_url + r'files/checkout/([^/]+)/$', checkout_file),
    (object_url + r'modify/$', modify_object),
    (object_url + r'management/$', display_management),
    (object_url + r'management/add/$', add_management),
    (object_url + r'management/replace/(?P<link_id>\d+)/$', replace_management),
    (object_url + r'management/delete/(?P<link_id>\d+)/$', delete_management),
    (object_url + r'navigate/$', navigate),

    (user_url + r'$', display_object, user_dict),
    (user_url + r'attributes/$', display_object_attributes, user_dict),
    (user_url + r'history/$', display_object_history, user_dict),
    (user_url + r'parts-doc-cad/$', display_related_plmobject, user_dict),
    (user_url + r'delegation/$', display_delegation, user_dict),
    (user_url + r'delegation/delegate/(?P<role>[^/]+)/$', delegate,\
                    {'obj_type':'User', 'obj_revi':'-', 'sign_level':'none'}),
    (user_url + r'delegation/delegate/(?P<role>[^/]+)/(?P<sign_level>\d+|all)/$', delegate,\
                    {'obj_type':'User', 'obj_revi':'-'}),
    (user_url + r'delegation/stop_delegate/(?P<role>[^/]+)/$', stop_delegate,\
                    {'obj_type':'User', 'obj_revi':'-', 'sign_level':'none'}),
    (user_url + r'delegation/stop_delegate/(?P<role>[^/]+)/(?P<sign_level>\d+|all)/$', stop_delegate,\
                    {'obj_type':'User', 'obj_revi':'-'}),
    (user_url + r'modify/$', modify_user, user_dict),
    (user_url + r'password/$', change_user_password, user_dict),
    (user_url + r'navigate/$', navigate, user_dict),
    
	# In order to take into account the css file
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root' : 'media/'}),    
    (r'^file/(?P<docfile_id>\d+)/$', download),
    (r'^docs/(?P<path>.*)$', 'django.views.static.serve', {'document_root' : 'docs/'}),    

)

# urls related to the api
api_url = r'^api/object/(?P<doc_id>\d+)/'
urlpatterns += patterns('',
    (r'^api/login/', api.api_login),
    (r'^api/needlogin/', api.need_login),
    (r'^api/testlogin/', api.test_login),
    (r'^api/types/$', api.get_all_types),
    (r'^api/parts/$', api.get_all_parts),
    (r'^api/docs/$', api.get_all_docs),
    (r'^api/search/$', api.search),
    (r'^api/create/$', api.create),
    (r'^api/search_fields/(?P<typename>[\w_]+)/$', api.get_advanced_search_fields),
    (r'^api/creation_fields/(?P<typename>[\w_]+)/$', api.get_creation_fields),
    (api_url + r'files/(?P<all_files>all/)?$', api.get_files),
    (api_url + r'revise/$', api.revise),
    (api_url + r'add_file/$', api.add_file),
    (api_url + r'attach_to_part/(?P<part_id>\d+)/$', api.attach_to_part),
    (api_url + r'next_?revision/$', api.next_revision),
    (api_url + r'is_?revisable/$', api.is_revisable),
    (api_url + r'(?:lock|checkout)/(?P<df_id>\d+)/$', api.check_out),
    (api_url + r'unlock/(?P<df_id>\d+)/$', api.unlock),
    (api_url + r'is_?locked/(?P<df_id>\d+)/$', api.is_locked),
    (api_url + r'checkin/(?P<df_id>\d+)/$', api.check_in),
    (api_url + r'add_thumbnail/(?P<df_id>\d+)/$', api.add_thumbnail),
)


# add custom application urls
for app in settings.INSTALLED_APPS:
    if app.startswith("openPLM"):
        try:
            __import__("%s.urls" % app, globals(), locals(), [], -1)
            patterns = getattr(sys.modules["%s.urls" % app], "urlpatterns")
            urlpatterns += patterns
        except ImportError:
            pass

