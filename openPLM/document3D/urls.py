from django.conf.urls.defaults import *
import openPLM.document3D.views as views



def patterns2(view_prefix, url_prefix, *urls):
    urls2 = []
    for u in urls:
        u2 = list(u)
        u2[0] = url_prefix + u2[0]
        urls2.append(tuple(u2))
    return patterns(view_prefix, *urls2)

object_pattern = '(?P<obj_type>\w+)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}
object_url = r'^object/' + object_pattern

urlpatterns = patterns('',
    (r'^object/Document3D/([^/]+)/([^/]+)/3D/$', views.display_3d),
    (r'^object/([^/]+)/([^/]+)/([^/]+)/decompose/([^/]+)/$', views.display_decompose),
    (r'^ajax/decompose/([^/]+)/$', views.ajax_part_creation_form),
)


