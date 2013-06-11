from django.conf.urls import *
import openPLM.apps.document3D.views as views
import openPLM.apps.document3D.api as api3D
from openPLM.plmapp.views import public

def patterns2(view_prefix, url_prefix, *urls):
    urls2 = []
    for u in urls:
        u2 = list(u)
        u2[0] = url_prefix + u2[0]
        urls2.append(tuple(u2))
    return patterns(view_prefix, *urls2)

object_pattern = '(?P<obj_type>Document3D)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}
object_url = r'^object/' + object_pattern

urlpatterns = patterns('',
    (r'^object/Document3D/([^/]+)/([^/]+)/3D/$', views.display_3d),
    (object_url + r'public/$', public, {"template" : "public_3d.html"}),
    (r'^object/Document3D/([^/]+)/([^/]+)/public/3D/$', views.display_public_3d),
    (r'^3D/public/(\d+)$', views.public_3d_js),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/decompose/([^/]+)/$', views.display_decompose),
    (r'^ajax/decompose/([^/]+)/$', views.ajax_part_creation_form),


)

api_url = r'^api/object/(?P<doc_id>\d+)/'

urlpatterns += patterns2('', api_url,
    (r'add_zip_file/(?P<unlock>True|False|true|false)/$', api3D.add_zip_file),
    (r'add_zip_file/thumbnail/(?P<thumbnail_extension>[\w]+)/(?P<unlock>True|False|true|false)/$', api3D.add_zip_file, {"thumbnail" : True}),
    (r'prepare_multi_check_out/$', api3D.prepare_multi_check_out),
    (r'decomposed_documents/(?P<type_check_out>[\w\,]+)/$', api3D.get_decomposition_documents),
    (r'add_assembly/', api3D.add_assembly),
    (r'get_assembly/', api3D.get_assembly),
    (r'update_assembly/', api3D.update_assembly),
)



urlpatterns += patterns2('', '^api/',
    (r'doc(?:ument)?s3D/$', api3D.get_all_3D_docs),
    )


