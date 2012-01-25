
from django.conf.urls.defaults import *

import openPLM.subversion.views

object_pattern = '(?P<obj_type>SubversionRepository)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

object_url = r'^object/' + object_pattern
urlpatterns = patterns('',
    (object_url + r'files/$', 'openPLM.subversion.views.display_files'),
    (object_url + r'logs/$', 'openPLM.subversion.views.logs'),
    (object_url + r'logs/ajax/$', 'openPLM.subversion.views.ajax_logs'),
)

