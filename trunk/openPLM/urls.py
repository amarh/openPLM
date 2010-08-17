import sys

from django.conf import settings
from django.conf.urls.defaults import *
from openPLM.plmapp.views import *
import openPLM.plmapp.api as api
from django.contrib.auth.views import login, logout

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),

    (r'^bollox/', display_bollox),
    (r'^(?:accounts/)?login/', login, {'template_name': 'DisplayLoginPage.htm', }),
    (r'^(?:accounts/)?logout/', logout, {'next_page': '/login/', }),
    (r'^home/', display_home_page),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/$', display_object),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/attributes/$', display_object_attributes),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/lifecycle/$', display_object_lifecycle),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/revisions/$', display_object_revisions),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/history/$', display_object_history),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/BOM-child/$', display_object_child),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/BOM-child/edit/$', edit_children),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/BOM-child/add/$', add_children),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/parents/$', display_object_parents),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/doc-cad/$', display_object_doc_cad),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/doc-cad/add/$', add_doc_cad),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/parts/$', display_related_part),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/parts/add/$', add_rel_part),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/files/$', display_files),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/files/add/$', add_file),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/files/checkin/([^/]+)/$', checkin_file),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/modify/$', modify_object),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/management/$', display_management),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/management/add/$', add_management),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/management/replace/$', replace_management),
    (r'^object/(?P<obj_type>[^/]+)/(?P<obj_ref>[^/]+)/(?P<obj_revi>[^/]+)/navigate/$', navigate),
    (r'^object/create/$', create_object),
    (r'^user/(?P<obj_ref>[^/]+)/$', display_object, {'obj_type':'User', 'obj_revi':'-'}),
    (r'^user/(?P<obj_ref>[^/]+)/attributes/$', display_object_attributes, {'obj_type':'User', 'obj_revi':'-'}),
    (r'^user/(?P<obj_ref>[^/]+)/lifecycle/$', display_object_lifecycle, {'obj_type':'User', 'obj_revi':'-'}),
    (r'^user/(?P<obj_ref>[^/]+)/history/$', display_object_history, {'obj_type':'User', 'obj_revi':'-'}),
    (r'^user/(?P<obj_ref>[^/]+)/modify/$', modify_user, {'obj_type':'User', 'obj_revi':'-'}),
    (r'^user/(?P<obj_ref>[^/]+)/password/$', change_user_password, {'obj_type':'User', 'obj_revi':'-'}),
    
	# In order to take into account the css file
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root' : 'media/'}),    
    (r'^file/(?P<docfile_id>\d+)/$', download),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/files/checkout/([^/]+)/$', checkout_file),
    (r'^docs/(?P<path>.*)$', 'django.views.static.serve', {'document_root' : 'docs/'}),    

)


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
    (r'^api/object/(?P<doc_id>\d+)/files/(?P<all_files>all/)?$', api.get_files),
    (r'^api/object/(?P<doc_id>\d+)/revise/$', api.revise),
    (r'^api/object/(?P<doc_id>\d+)/add_file/$', api.add_file),
    (r'^api/object/(?P<doc_id>\d+)/attach_to_part/(?P<part_id>\d+)/$', api.attach_to_part),
    (r'^api/object/(?P<doc_id>\d+)/next_?revision/$', api.next_revision),
    (r'^api/object/(?P<doc_id>\d+)/is_?revisable/$', api.is_revisable),
    (r'^api/object/(?P<doc_id>\d+)/(?:lock|checkout)/(?P<df_id>\d+)/$', api.check_out),
    (r'^api/object/(?P<doc_id>\d+)/unlock/(?P<df_id>\d+)/$', api.unlock),
    (r'^api/object/(?P<doc_id>\d+)/is_?locked/(?P<df_id>\d+)/$', api.is_locked),
    (r'^api/object/(?P<doc_id>\d+)/checkin/(?P<df_id>\d+)/$', api.check_in),
    (r'^api/object/(?P<doc_id>\d+)/add_thumbnail/(?P<df_id>\d+)/$', api.add_thumbnail),
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
