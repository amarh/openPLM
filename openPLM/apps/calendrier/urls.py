
from django.conf.urls import *
import openPLM.apps.calendrier.views as views
from django.urls import re_path,include,path
object_pattern = '(?P<obj_type>\w+)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}
object_url = r'^object/' + object_pattern
user_url = r'^user/(?P<obj_ref>[^/]+)/'
group_url = r'^group/(?P<obj_ref>[^/]+)/'
date_url = r'calendar/(?:(?P<year>\d{1,4})/(?:(?P<month>\d\d?)/)?)?$'
ics_url = date_url[:-1] + "ics/$"

urlpatterns = [
    re_path(r'^timeline/' + date_url, views.history_calendar, {"timeline" : True}),
    re_path(object_url + r'history/' + date_url, views.history_calendar),
    re_path(user_url + r'history/' + date_url, views.history_calendar, {"obj_type" : "User"}),
    re_path(group_url + r'history/' + date_url, views.history_calendar, {"obj_type" : "Group"}), 
    re_path('^timeline/$', views.history, {"timeline" : True,} ),
    re_path(object_url + r'history/$', views.history, ),
    re_path(user_url + r'history/$', views.history, {"obj_type" : "User" }),
    re_path(group_url + r'history/$', views.history, { "obj_type" : "Group" }),
]
if views.ICAL_INSTALLED:
    urlpatterns +=[ 
        re_path('^timeline/' + ics_url , views.TimelineCalendarFeed()),
        re_path(object_url + r'history/' + ics_url, views.CalendarFeed()),
        re_path(user_url + r'history/' + ics_url, views.CalendarFeed(), {"obj_type" : "User", "obj_revi" : "-"}),
        re_path(group_url + r'history/' + ics_url, views.CalendarFeed(), { "obj_type" : "Group",
            "obj_revi" : "-"}),
    ]

