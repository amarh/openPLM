from django.conf.urls import *
from django.views.generic import RedirectView

import openPLM.apps.richpage.views

object_pattern = '(?P<obj_type>Page)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

object_url = r'^object/' + object_pattern
urlpatterns = patterns('',
    (object_url +'$', RedirectView.as_view(url="/object/%(obj_type)s/%(obj_ref)s/%(obj_revi)s/page/",
     permanent=True)),
    (object_url + r'page/$', 'openPLM.apps.richpage.views.display_page'),
    (object_url + r'edit_content/$', 'openPLM.apps.richpage.views.edit_content'),
)

