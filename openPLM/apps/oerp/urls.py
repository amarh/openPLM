from django.conf.urls import *
from django.urls import re_path
urlpatterns = [
    re_path(r'^object/([^/]+)/([^/]+)/([^/]+)/ERP/$', 'erp_summary'),
    re_path(r'^object/([^/]+)/([^/]+)/([^/]+)/ERP/publish/$', 'erp_summary', {"publish" : True}),
    re_path(r'^object/([^/]+)/([^/]+)/([^/]+)/ERP/update_cost/$', 'erp_summary', {"update" : True}),
]
