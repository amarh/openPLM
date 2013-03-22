
from django.conf.urls import *

import openPLM.apps.richpage.views

object_pattern = '(?P<obj_type>Page)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

object_url = r'^object/' + object_pattern
urlpatterns = patterns('',
    (object_url + r'files/$', 'openPLM.apps.richpage.views.display_files'),
    (object_url + r'edit_content/$', 'openPLM.apps.richpage.views.edit_content'),
)

