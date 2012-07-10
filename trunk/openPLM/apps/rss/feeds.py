import base64

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login
from django.contrib.syndication.views import Feed
from django.utils.encoding import iri_to_uri
from django.utils.feedgenerator import Atom1Feed

from django.utils.translation import ugettext_lazy as _

from openPLM.plmapp.base_views import get_obj
from openPLM.plmapp import models


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
            if request.user.get_profile().restricted:
                return HttpResponseForbidden()
            # already logged in
            return super(HTTPAuthFeed, self).__call__(request, *args, **kwargs)
        # check HTTP auth credentials
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2:
                # only basic auth is supported
                if auth[0].lower() == "basic":
                    uname, passwd = base64.b64decode(auth[1]).split(':')
                    user = authenticate(username=uname, password=passwd)
                    if user is not None:
                        if user.is_active:
                            if user.get_profile().restricted:
                                return HttpResponseForbidden()
                            login(request, user)
                            request.user = user
                            return super(HTTPAuthFeed, self).__call__(request, *args, **kwargs)
        # failed authentication results in 401
        response = HttpResponse()
        response.status_code = 401
        response['WWW-Authenticate'] = 'Basic realm="%s"' % self.basic_auth_realm
        return response
        
        
# one feed per object
class RssFeed(HTTPAuthFeed):
    
    def get_object(self, request, obj_type, obj_ref, obj_revi):
        obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
        obj.check_readable()
        return obj
    
    def title(self,obj):
        if hasattr(obj,'is_part'):
            return obj.object.reference+"//"+obj.object.revision+"//"+obj.object.name
        elif hasattr(obj,'username'):
            return obj.object.username
        else:
            return obj.object.name
    
    def link(self, obj):
        if hasattr(obj,'plmobject_url'):
            return obj.plmobject_url
        else:
            return iri_to_uri(u"/user/%s/" % obj.username)
        
    def description(self, obj):
        ret = _("Updates on changes on ")
        if hasattr(obj,'is_part'):
            return ret +obj.object.reference+"//"+obj.object.revision+"//"+obj.object.name
        elif hasattr(obj,'username'):
            return ret + obj.object.username
        else:
            return ret + obj.object.name
            
    def items(self,obj):
        #return the history items
        if hasattr(obj,'get_all_revisions'):
            objects = [o.id for o in obj.get_all_revisions()]
            return obj.HISTORY.objects.filter(plmobject__in=objects).order_by('-date')[:10]
        else:
            return obj.HISTORY.objects.filter(plmobject=obj.object).order_by('-date')[:10]
   
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
        if isinstance(item, models.History):
            t = "object"
        elif isinstance(item, models.GroupHistory):
            t = "group"
        else:
            t = "user"
        return u"/history_item/%s/%d/" % (t, item.id)

class AtomFeed(RssFeed):
    feed_type = Atom1Feed
    subtitle = RssFeed.description

class TimelineRssFeed(RssFeed):

    def get_object(self, request):
        return request.user

    def title(self):
        return _("Timeline")

    def link(self, obj):
        return "/timeline/"

    def description(self, obj):
        return _("Timeline")

    def items(self, obj):
        q = Q(plmobject__owner__username=settings.COMPANY)
        q |= Q(plmobject__group__in=obj.groups.all())
        history = models.History.objects.filter(q).order_by('-date')
        history = history.select_related("user", "plmobject__type", "plmobject__reference",
            "plmobject__revision")
        return history[:10]

class TimelineAtomFeed(TimelineRssFeed):
    feed_type = Atom1Feed
    subtitle = TimelineRssFeed.description


