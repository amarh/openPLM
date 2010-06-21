from django.conf.urls.defaults import *
from openPLM.plmapp.views import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # (r'^object2/$', DisplayObject2),
    (r'^admin/', include(admin.site.urls)),
    (r'^home/', DisplayHomePage),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/$', DisplayObject),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/attributes/$', DisplayObject),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/lifecycle/$', DisplayObjectLifecycle),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/revisions/$', DisplayObjectRevisions),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/history/$', DisplayObjectHistory),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/BOM-child/$', DisplayObjectChild),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/BOM-child/edit/$', edit_children),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/parents/$', DisplayObjectParents),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/doc-cad/$', DisplayObjectDocCad),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/modify/$', ModifyObject),
    (r'^object/create/$', CreateObject),
    # (r'^object/register/$', RegisterObject),
	# In order to take into account the css file
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root' : 'media/'})
)
