from django.conf.urls.defaults import *
from openPLM.plmapp.views import *
from django.contrib.auth.views import login, logout

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),

    (r'^bollox/', display_bollox),
    (r'^login/', login, {'template_name': 'DisplayLoginPage.htm', }),
    (r'^logout/', logout, {'next_page': 'http://www.google.fr', }),
    (r'^home/', display_home_page),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/$', display_object),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/attributes/$', display_object),
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
    (r'^object/([^/]+)/([^/]+)/([^/]+)/modify/$', modify_object),
    (r'^object/create/$', create_object),

	# In order to take into account the css file
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root' : 'media/'})
)
