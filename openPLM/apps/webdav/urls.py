from django.urls import re_path
urlpatterns = [
    # workaround against dummy queries from windows clients
    re_path(r'^dav/(?:[^/]+/)*(?:[dD]esktop.ini|AutoRun.inf|Thumbs.db|folder.(?:jpg|gif))$', 'openPLM.apps.webdav.views.not_found'),
    re_path(r'^dav/(?P<local_path>.*)$', 'openPLM.apps.webdav.views.openplm_webdav'),
]