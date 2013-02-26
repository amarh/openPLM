from django.conf.urls import *
from openPLM.apps.rss.feeds import *

object_pattern = '(?P<obj_type>\w+)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

object_url = r'^object/' + object_pattern
user_url = r'^user/(?P<obj_ref>[^/]+)/'
group_url = r'^group/(?P<obj_ref>[^/]+)/'
user_dict = {'obj_type':'User', 'obj_revi':'-'}
group_dict = {'obj_type':'Group', 'obj_revi':'-'}


urlpatterns = patterns('',
    (object_url+'rss/$', RssFeed()),
    (user_url+'rss/$', RssFeed(),user_dict),
    (group_url+'rss/$', RssFeed(), group_dict),
    (object_url+'atom/$', AtomFeed()),
    (user_url+'rss/$', AtomFeed(),user_dict),
    (group_url+'rss/$', AtomFeed(), group_dict),
    (r'^(?:timeline/)?rss/$', TimelineRssFeed()),
    (r'^(?:timeline/)?atom/$', TimelineAtomFeed()),
)
