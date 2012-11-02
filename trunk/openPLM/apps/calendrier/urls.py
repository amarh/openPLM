
from django.conf.urls.defaults import *
import openPLM.apps.calendrier.views as views

object_pattern = '(?P<obj_type>\w+)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}
object_url = r'^object/' + object_pattern
user_url = r'^user/(?P<obj_ref>[^/]+)/'
group_url = r'^group/(?P<obj_ref>[^/]+)/'
date_url = r'calendar/(?:(?P<year>\d{1,4})/(?:(?P<month>\d\d?)/)?)?$'


urlpatterns = patterns('',
    (r'^timeline/' + date_url, views.history_calendar, {"timeline" : True}),
    (object_url + r'history/' + date_url, views.history_calendar),
    (user_url + r'history/' + date_url, views.history_calendar, {"obj_type" : "User"}),
    (group_url + r'history/' + date_url, views.history_calendar, {"obj_type" : "Group"}),

    
    ('^timeline/', views.history, {"timeline" : True,} ),
    (object_url + r'history/', views.history, ),
    (user_url + r'history/', views.history, {"obj_type" : "User" }),
    (group_url + r'history/', views.history, { "obj_type" : "Group" }),
    )
