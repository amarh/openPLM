from django.conf.urls.defaults import *
import openPLM.bicycle.views as views

urlpatterns = patterns('',
    (r'^object/Bicycle/([^/]+)/([^/]+)/attributes/$', views.attributes),
                      )
