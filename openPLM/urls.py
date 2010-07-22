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
    (r'^login/', login, {'template_name': 'DisplayLoginPage.htm', }),
    (r'^logout/', logout, {'next_page': '/login/', }),
    (r'^home/', display_home_page),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/$', display_object),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/attributes/$', display_object_attributes),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/lifecycle/$', display_object_lifecycle),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/revisions/$', display_object_revisions),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/history/$', display_object_history),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/BOM-child/$', display_object_child),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/BOM-child/edit/$', edit_children),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/BOM-child/add/$', add_children),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/parents/$', display_object_parents),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/doc-cad/$', display_object_doc_cad),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/doc-cad/add/$', add_doc_cad),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/parts/$', display_related_part),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/parts/add/$', add_rel_part),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/files/$', display_files),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/files/add/$', add_file),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/files/checkin/([^/]+)/$', checkin_file),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/modify/$', modify_object),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/navigate/$', navigate),
    (r'^object/create/$', create_object),

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
)
