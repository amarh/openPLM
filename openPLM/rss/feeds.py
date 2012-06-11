#import base64

from django.http import HttpResponse

from django.contrib.auth import authenticate, login
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from django.utils.translation import ugettext_lazy as _

from openPLM.plmapp.base_views import get_generic_data

def make_desc(action, details, username):
    """
    Create a description with item attributes:
    """
    ret=""
    if action not in details:
        if username not in details:
            return details+" "+action+" by "+username
        else:
            return details.split(username)[0]+" "+action+" by "+username
    else:
        return details

# inspired by http://djangosnippets.org/snippets/2291/
class HTTPAuthFeed(Feed):
    basic_auth_realm = 'My Page'
    
    def __call__(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            # already logged in
            return super(HTTPAuthFeed, self).__call__(request, *args, **kwargs)
        
        # failed authentication results in 401
        response = HttpResponse()
        response.status_code = 401
        response['WWW-Authenticate'] = 'Basic realm="%s"' % self.basic_auth_realm
        return response
        
        
#Un flux par objet
class RssFeed(HTTPAuthFeed):
    
    def get_object(self, request, obj_type, obj_ref, obj_revi):
        obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
        return obj
    
    def title(self,obj):
        return obj.object.reference+"//"+obj.object.revision+"//"+obj.object.name
    
    def link(self, obj):
        return obj.plmobject_url
        
    def description(self, obj):
        return _("Updates on changes on ")+obj.object.reference+"//"+obj.object.revision+"//"+obj.object.name
            
    def items(self,obj):
        #return the history items
        objects = [o.id for o in obj.get_all_revisions()]
        return obj.HISTORY.objects.filter(plmobject__in=objects).order_by('-date')[:10]
   
    def item_title(self, item):
        i_date = item.date.strftime("%B %d, %Y") 
        i_action = item.action
        return "%s - %s" % (i_date,i_action)
        
    def item_description(self, item):
        i_details = item.details.lower()
        i_action = item.action.lower()
        i_user = item.user.username.lower()
        return make_desc(i_action, i_details, i_user)
    
    def item_link(self, item):
        return item.plmobject.plmobject_url+"#"+str(item.id)

class AtomFeed(RssFeed):
    feed_type = Atom1Feed
    subtitle = RssFeed.description

