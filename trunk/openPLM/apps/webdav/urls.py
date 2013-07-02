from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    # workaround against dummy queries from windows clients
    url(r'^dav/(?:[^/]+/)*(?:[dD]esktop.ini|AutoRun.inf|Thumbs.db|folder.(?:jpg|gif))$', 'openPLM.apps.webdav.views.not_found'),

    url(r'^dav/(?P<local_path>.*)$', 'openPLM.apps.webdav.views.openplm_webdav'),
)
