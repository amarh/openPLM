from django.db.models import F, Q
from django.utils.translation import ugettext_lazy as _

from openPLM.plmapp import models
import openPLM.plmapp.base_views as bv
from openPLM.plmapp.views import create_object, r2r, get_pagination

from openPLM.apps.ecr.forms import get_creation_form
from openPLM.apps.ecr.models import ECR


@bv.handle_errors
def create_ecr(request, *args):
    if request.method == 'GET':
        creation_form = get_creation_form(request.user)
    elif request.method == 'POST':
        creation_form = get_creation_form(request.user, request.POST)
    return create_object(request, True, creation_form)
bv.register_creation_view(ECR, create_ecr)


@bv.secure_required
def browse_ecr(request):
    user = request.user
    if user.is_authenticated() and not user.get_profile().restricted:
        # only authenticated users can see all groups and users
        obj, ctx = bv.get_generic_data(request, search=False)
        object_list = ECR.objects.all()
        # this is only relevant for authenticated users
        ctx["state"] = state = request.GET.get("state", "all")
        if state == "official":
            object_list = object_list.\
                exclude(lifecycle=models.get_cancelled_lifecycle()).\
                filter(state=F("lifecycle__official_state"))
        ctx["plmobjects"] = False
    else:
        ctx = bv.init_ctx("-", "-", "-")
        ctx.update({
            'is_readable': True,
            'restricted': True,
            'object_menu': [],
            'navigation_history': [],
        })
        query = Q(published=True)
        if user.is_authenticated():
            readable = user.ecruserlink_user.now().filter(role=models.ROLE_READER)
            readable |= user.ecruserlink_user.now().filter(role=models.ROLE_OWNER)
            query |= Q(id__in=readable.values_list("ecr_id", flat=True))
        object_list = ECR.objects.filter(query)

    ctx.update(get_pagination(request.GET, object_list, type))
    extra_types = [c.__name__ for c in models.IObject.__subclasses__()]
    ctx.update({
        "object_type": _("Browse"),
        "type": "ECR",
        "extra_types": extra_types,
    })
    return r2r("browse_ecr.html", ctx, request)
