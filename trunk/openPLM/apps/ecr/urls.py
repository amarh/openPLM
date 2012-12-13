
from django.conf.urls.defaults import *
import openPLM.apps.cad.views as views
import openPLM.plmapp.views as pviews

ecr = r'^/ECR/(?P<obj_ref>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}



urlpatterns = patterns('',
                      )
