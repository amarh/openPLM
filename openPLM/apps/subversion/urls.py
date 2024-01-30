
from django.conf.urls import *
from django.urls import re_path
import openPLM.apps.subversion.views as subViews

object_pattern = '(?P<obj_type>SubversionRepository)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

object_url = r'^object/' + object_pattern
urlpatterns = [
    re_path(object_url + r'files/$', subViews.display_files),
    re_path(object_url + r'logs/$', subViews.logs),
    re_path(object_url + r'logs/ajax/$', subViews.ajax_logs),


]