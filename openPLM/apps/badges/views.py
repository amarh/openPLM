from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from openPLM.plmapp.base_views import get_generic_data
from openPLM.plmapp.views.main import r2r

from openPLM.apps.badges.models import Badge
import meta_badges

def overview(request, extra_context={}):
    obj, ctx = get_generic_data(request, search=False)
    
    badges = Badge.objects.active().order_by("level")
    
    ctx.update(extra_context)
    ctx["badges"]=badges
    ctx["object_type"]=_("Badges")
    return r2r("badges/overview.html",ctx,request)

def detail(request, slug, extra_context={}):
    obj, ctx = get_generic_data(request, search=False)
    badge = get_object_or_404(Badge, id=slug)
    users = badge.user.all()
    
    ctx.update(extra_context)
    ctx["badge"]=badge
    ctx["users"]=users
    object_type = _(u"Badge : %s")
    ctx["object_type"]=object_type %(badge.title)
    return r2r("badges/detail.html", ctx, request)
    
def display_userbadges(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    badges = Badge.objects.active().filter(user=obj.object).order_by("level")
    
    ctx.update({
        'current_page' : 'badges', 
        'badges' : badges,
        })
    
    return r2r("user/badges_overview.html", ctx, request)
