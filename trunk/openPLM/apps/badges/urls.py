from django.conf.urls import *

import meta_badges
from openPLM.apps.badges import views

user_url = r'^user/(?P<obj_ref>[^/]+)/'
user_dict = {'obj_type':'User', 'obj_revi':'-'}

urlpatterns = patterns('',
    url(r'^badges/$', views.overview, name="badges_overview"),
    url(r'^badges/(?P<slug>[A-Za-z0-9_-]+)/$', views.detail, name="badge_detail"),
    (user_url+'badges/$', views.display_userbadges, user_dict),
    )
