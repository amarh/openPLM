from django.conf.urls.defaults import *
from openPLM.rss.feeds import *

object_pattern = '(?P<obj_type>\w+)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

object_url = r'^object/' + object_pattern
user_url = r'^user/(?P<obj_ref>[^/]+)/'
group_url = r'^group/(?P<obj_ref>[^/]+)/'
user_dict = {'obj_type':'User', 'obj_revi':'-'}
group_dict = {'obj_type':'Group', 'obj_revi':'-'}


urlpatterns = patterns('',
    (object_url+'rss/$', RssFeed()),
    (object_url+'atom/$', AtomFeed()),
)
