from django.conf.urls.defaults import *
from plmapp.views import *
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^openPLM/', include('openPLM.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
     (r'^admin/', include(admin.site.urls)),

    (r'^object/([^/]+)/([^/]+)/([^/]+)/$', DisplayObject),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/attributes/$', DisplayObject),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/lifecycle/$', DisplayObjectLifecycle),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/revisions/$', DisplayObjectRevisions),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/history/$', DisplayObjectHistory),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/BOM-child/$', DisplayObjectChild),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/parents/$', DisplayObjectParents),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/doc-cad/$', DisplayObjectDocCad),
	# In order to take into account the css file
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root' : 'media/'})
)
