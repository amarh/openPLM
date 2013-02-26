from django.conf.urls import *

urlpatterns = patterns('openPLM.apps.oerp.views',
    (r'^object/([^/]+)/([^/]+)/([^/]+)/ERP/$', 'erp_summary'),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/ERP/publish/$', 'erp_summary', {"publish" : True}),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/ERP/update_cost/$', 'erp_summary', {"update" : True}),
)
