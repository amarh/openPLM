from django.conf.urls import *
from openPLM.apps.rss.feeds import *
from django.urls import re_path
object_pattern = '(?P<obj_type>\w+)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

object_url = r'^object/' + object_pattern
user_url = r'^user/(?P<obj_ref>[^/]+)/'
group_url = r'^group/(?P<obj_ref>[^/]+)/'
user_dict = {'obj_type':'User', 'obj_revi':'-'}
group_dict = {'obj_type':'Group', 'obj_revi':'-'}


urlpatterns = [
    re_path(object_url+'rss/$', RssFeed()),
    re_path(user_url+'rss/$', RssFeed(),user_dict),
    re_path(group_url+'rss/$', RssFeed(), group_dict),
    re_path(object_url+'atom/$', AtomFeed()),
    re_path(user_url+'rss/$', AtomFeed(),user_dict),
    re_path(group_url+'rss/$', AtomFeed(), group_dict),
    re_path(r'^(?:timeline/)?rss/$', TimelineRssFeed()),
    re_path(r'^(?:timeline/)?atom/$', TimelineAtomFeed()),

]