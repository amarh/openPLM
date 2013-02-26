
from django.conf.urls import *

import openPLM.apps.gdoc.views

object_pattern = '(?P<obj_type>GoogleDocument)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

object_url = r'^object/' + object_pattern
urlpatterns = patterns('',
    (r'^oauth2callback', 'openPLM.apps.gdoc.views.auth_return'),
    (object_url + r'files/$', 'openPLM.apps.gdoc.views.display_files'),
    (object_url + r'revisions/$', 'openPLM.apps.gdoc.views.display_object_revisions'),
)

