from django.conf.urls import *
from openPLM.apps.urldoc.views import display_URLDoc
from django.urls import re_path
object_pattern = '(?P<obj_type>\w+)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}


object_url = r'^object/' + object_pattern


urlpatterns = [
    re_path(object_url+'content/$', display_URLDoc),
]