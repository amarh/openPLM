from django.conf.urls.defaults import *

urlpatterns = patterns('openPLM.oerp.views',
        (r'^object/([^/]+)/([^/]+)/([^/]+)/ERP/(?:publish/)?$', 'erp_summary'),
    )
