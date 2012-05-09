from django.http import HttpResponseRedirect

from openPLM.plmapp.base_views import get_generic_data
from openPLM.plmapp.views.main import r2r
from openPLM.plmapp.forms import ConfirmPasswordForm

from openPLM.oerp import models
from openPLM.oerp import erp

def erp_summary(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if not obj.is_part:
        raise ValueError("Object is not a part")
    ctx["current_page"] = "ERP"
    try:
        product = models.OERPProduct.objects.get(part=obj.object).product
    except models.OERPProduct.DoesNotExist:
        # allow to publish on openERP
        return erp_publish(request, obj, ctx)
    else:
        # the current part has been published on openERP
        ctx["product"] = erp.get_product_data([product])[0]
        ctx["boms"] = erp.get_bom_data(ctx["product"]["bom_ids"])
        return r2r("erp_published.html", ctx, request)

def erp_publish(request, obj, ctx):
    if not obj.group.user_set.filter(id=request.user.id).exists():
        ctx["can_publish"] = False
    else:
        ctx["can_publish"] = obj.is_official
    if ctx["can_publish"]:
        if request.method == "POST":
            form = ConfirmPasswordForm(request.user, request.POST)
            if form.is_valid():
                erp.export_bom(obj)
            return HttpResponseRedirect("..")
        else:
            form = ConfirmPasswordForm(request.user)
        ctx["password_form"] = form
    return r2r("erp_summary.html", ctx, request)

