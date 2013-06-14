import base64

from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login
from django.contrib.syndication.views import Feed
from django.utils.encoding import iri_to_uri
from django.utils.html import strip_tags
from django.utils.feedgenerator import Atom1Feed
from django.utils.translation import ugettext_lazy as _

from openPLM.plmapp.views.base import get_obj
from openPLM.plmapp.models import timeline_histories


def make_desc(action, details, username):
    """
    Create a description with item attributes:
    """
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
            if request.user.profile.restricted:
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
                            if user.profile.restricted:
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
        return strip_tags(obj.title)

    def link(self, obj):
        if hasattr(obj,'plmobject_url'):
            return obj.plmobject_url
        else:
            return iri_to_uri(u"/user/%s/" % obj.username)

    def description(self, obj):
        ret = _("Updates on changes on %(title)s")
        return ret % {"title" : self.title(obj)}

    def items(self,obj):
        return obj.histories[:10]

    def item_title(self, item):
        return u"%s - %s" % (item. action, strip_tags(item.title))

    def item_description(self, item):
        i_details = item.details.lower()
        i_action = item.action.lower()
        i_user = item.user.username.lower()
        return make_desc(i_action, i_details, i_user)

    def item_link(self, item):
        return item.get_redirect_url()


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
        return timeline_histories(obj, None, None, None, None)[:10]

class TimelineAtomFeed(TimelineRssFeed):
    feed_type = Atom1Feed
    subtitle = TimelineRssFeed.description


