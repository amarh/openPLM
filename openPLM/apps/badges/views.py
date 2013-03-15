from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from openPLM.plmapp.views.base import get_generic_data, handle_errors
from openPLM.plmapp.utils import r2r

from openPLM.apps.badges.models import Badge


@handle_errors
def overview(request, extra_context={}):
    """
    Badges view :
        display all badges available in OpenPLM

    :url: :samp:`/badges/`
    
    **Template:**
    
    :file:`badges/overview.html`

    **Context:**

    ``RequestContext``
 
    ``badges``
        List of all badges available

    ``object_type``
        Name of the page

    """
    obj, ctx = get_generic_data(request, search=False)
    
    badges = Badge.objects.active().order_by("level")
    
    ctx.update(extra_context)
    ctx["badges"]=badges
    ctx["object_type"]=_("Badges")
    return r2r("badges/overview.html",ctx,request)

@handle_errors
def detail(request, slug, extra_context={}):
    """
    Badge description view.

    :url: :samp:`/badges/{{slug}}`
    
    **Template:**
    
    :file:`badges/detail.html`

    **Context:**

    ``RequestContext``
 
    ``badge``
        Badge object corresponding to the id given in
        *slug*.

    ``users``
        List of users who won the badge
        
    ``object_type``
        component of the title of the page. Here the name
        of the badge.

    """
    obj, ctx = get_generic_data(request, search=False)
    badge = get_object_or_404(Badge, id=slug)
    users = badge.user.all()
    
    ctx.update(extra_context)
    ctx["badge"]=badge
    ctx["users"]=users
    object_type = _(u"Badge : %s")
    ctx["object_type"]=object_type %(badge.title)
    return r2r("badges/detail.html", ctx, request)


@handle_errors    
def display_userbadges(request, obj_type, obj_ref, obj_revi):
    """
    Badge tab in user view.

    :url: :samp:`/user/{{username}}/badges`
    
    **Template:**
    
    :file:`users/badges_overview.html`

    **Context:**

    ``RequestContext``
 
    ``badges``
        List of badges won by the user

    ``current_page``
        name of the tab

    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    badges = Badge.objects.active().filter(user=obj.object).order_by("level")
    
    ctx.update({
        'current_page' : 'badges', 
        'badges' : badges,
        })
    
    return r2r("user/badges_overview.html", ctx, request)
