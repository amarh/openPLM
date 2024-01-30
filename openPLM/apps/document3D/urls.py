from django.conf.urls import *
import openPLM.apps.document3D.views as views
import openPLM.apps.document3D.api as api3D
from openPLM.plmapp.views import public
from django.urls import re_path,include,path


object_pattern = '(?P<obj_type>Document3D)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}
object_url = r'^object/' + object_pattern

urlpatterns = [
    re_path(r'^object/Document3D/([^/]+)/([^/]+)/3D/$', views.display_3d),
    re_path(object_url + r'public/$', public, {"template" : "public_3d.html"}),
    re_path(r'^object/Document3D/([^/]+)/([^/]+)/public/3D/$', views.display_public_3d),
    re_path(r'^3D/public/(\d+)$', views.public_3d_js),
    re_path(r'^object/([^/]+)/([^/]+)/([^/]+)/decompose/([^/]+)/$', views.display_decompose),
    re_path(r'^ajax/decompose/([^/]+)/$', views.ajax_part_creation_form),
]

api_url = r'^api/object/(?P<doc_id>\d+)/'

urlpatterns +=[ 
    re_path(api_url+r'add_zip_file/(?P<unlock>True|False|true|false)/$', api3D.add_zip_file),
    re_path(api_url+r'add_zip_file/thumbnail/(?P<thumbnail_extension>[\w]+)/(?P<unlock>True|False|true|false)/$', api3D.add_zip_file, {"thumbnail" : True}),
    re_path(api_url+r'prepare_multi_check_out/$', api3D.prepare_multi_check_out),
    re_path(api_url+r'decomposed_documents/(?P<type_check_out>[\w\,]+)/$', api3D.get_decomposition_documents),
    re_path(api_url+r'add_assembly/', api3D.add_assembly),
    re_path(api_url+r'get_assembly/', api3D.get_assembly),
    re_path(api_url+r'update_assembly/', api3D.update_assembly),
]

urlpatterns += [
    path('api/doc(?:ument)?s3D/', api3D.get_all_3D_docs),
]