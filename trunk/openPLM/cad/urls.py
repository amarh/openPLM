from django.conf.urls.defaults import *
import openPLM.cad.views as views

urlpatterns = patterns('',
    (r'^object/([^/]+)/([^/]+)/([^/]+)/freecad/$', views.freecad),
                      )
