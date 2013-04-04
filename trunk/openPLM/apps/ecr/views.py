from django.http import HttpResponseRedirect
from django.db.models import F
from django.utils.translation import ugettext_lazy as _

from openPLM.plmapp import models
import openPLM.plmapp.views.base as bv
from openPLM.plmapp.utils import r2r
from openPLM.plmapp.views import create_object, get_pagination, ITEMS_PER_HISTORY, SimpleDateFilter
from openPLM.plmapp.forms import PLMObjectForm

from openPLM.apps.ecr.forms import get_creation_form
from openPLM.apps.ecr.models import ECR, ECRHistory


@bv.handle_errors
def create_ecr(request, *args):
    if request.method == 'GET':
        creation_form = get_creation_form(request.user)
    elif request.method == 'POST':
        creation_form = get_creation_form(request.user, request.POST)
    return create_object(request, True, creation_form)
bv.register_creation_view(ECR, create_ecr)


@bv.handle_errors(restricted_access=False)
def browse_ecr(request):
    user = request.user
    if not user.profile.restricted:
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
        ctime_filter = SimpleDateFilter("ctime", request, ECR, "ctime")
        object_list = ctime_filter.queryset(request, object_list)
        mtime_filter = SimpleDateFilter("mtime", request, ECR, "mtime")
        object_list = mtime_filter.queryset(request, object_list)
        ctx["time_filters"] = [ctime_filter, mtime_filter]
    else:
        ctx = bv.init_ctx("-", "-", "-")
        ctx.update({
            'is_readable': True,
            'restricted': True,
            'object_menu': [],
            'is_contributor': False,
            'navigation_history': [],
        })
        readable = user.ecrs.now().filter(role=models.ROLE_READER)
        readable |= user.ecrs.now().filter(role=models.ROLE_OWNER)
        object_list = ECR.objects.filter(id__in=readable)

    ctx.update(get_pagination(request, object_list, "ECR"))
    extra_types = [c.__name__ for c in models.IObject.__subclasses__()]
    ctx.update({
        "object_type": _("Browse"),
        "type": "ECR",
        "extra_types": extra_types,
    })
    return r2r("browse_ecr.html", ctx, request)


@bv.handle_errors
def plmobjects(request, obj_ref):
    obj, ctx = bv.get_generic_data(request, "ECR", obj_ref, "-")
    objects = models.PLMObject.objects.filter(
            id__in=obj.plmobjects.now().values_list("plmobject", flat=True))
    objects = objects.select_related("state", "lifecycle")
    ctx.update(get_pagination(request, objects, "object"))
    ctx["current_page"] = "part-doc-cads"
    ctx["detach_objects"] = obj.is_editable and ctx["is_owner"]
    return r2r("ecrs/plmobjects.html", ctx, request)


@bv.handle_errors
def attach_plmobject(request, obj_ref):
    obj, ctx = bv.get_generic_data(request, "ECR", obj_ref, "-", search=True)
    if request.method == "POST":
        form = PLMObjectForm(request.POST)
        if form.is_valid():
            plmobject = bv.get_obj_from_form(form, request.user)
            obj.attach_object(plmobject.object)
            return HttpResponseRedirect("..")
    else:
        form = PLMObjectForm()
    if obj.is_editable and ctx["is_owner"]:
        plmobjects = obj.plmobjects.now().values_list("plmobject", flat=True)
        can_attach = lambda x: x.id not in plmobjects
    else:
        can_attach = lambda x: False
    ctx.update({
        "current_page": "part-doc-cads",
        "attach_form": form,
        "link_creation": True,
        "attach": (obj, can_attach),
    })
    return r2r("ecrs/plmobjects_add.html", ctx, request)


@bv.handle_errors
def detach_plmobject(request, obj_ref):
    obj, ctx = bv.get_generic_data(request, "ECR", obj_ref, "-")
    if request.method == "POST":
        plmobject_id = int(request.POST["plmobject"])
        plmobject = models.PLMObject.objects.get(id=plmobject_id)
        obj.detach_object(plmobject)
    return HttpResponseRedirect("..")


@bv.handle_errors
def redirect_history(request, hid):
    h = ECRHistory.objects.get(id=int(hid))
    items = ECRHistory.objects.filter(plmobject=h.plmobject, date__gte=h.date).count() - 1
    page = items // ITEMS_PER_HISTORY + 1
    url = u"%shistory/?page=%d#%s" % (h.plmobject.plmobject_url, page, hid)
    return HttpResponseRedirect(url)


@bv.handle_errors
def changes(request, obj_type, obj_ref, obj_revi):
    obj, ctx = bv.get_generic_data(request, obj_type, obj_ref, obj_revi)
    ecrs = ECR.objects.filter(id__in=obj.ecrs.now().values_list("ecr", flat=True))
    ctx.update(get_pagination(request, ecrs, "ECR"))
    ctx["current_page"] = "changes"
    return r2r("changes.html", ctx, request)
