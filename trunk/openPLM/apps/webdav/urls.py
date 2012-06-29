from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    url(r'^dav/(?P<local_path>.*)$', 'openPLM.apps.webdav.views.openplm_webdav'),
)
