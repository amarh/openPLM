from django.http import HttpResponseRedirect

from openPLM.plmapp.base_views import get_generic_data, handle_errors
from openPLM.plmapp.exceptions import PermissionError
from openPLM.plmapp.forms import ConfirmPasswordForm
from openPLM.plmapp.views.main import r2r

from openPLM.oerp import erp
from openPLM.oerp import forms
from openPLM.oerp import models



@handle_errors
def erp_summary(request, obj_type, obj_ref, obj_revi, publish=False, update=False):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if not obj.is_part:
        raise ValueError("Object is not a part")
    ctx["current_page"] = "ERP"
    can_update = (obj.check_in_group(request.user, False)
            and not obj.is_cancelled
            and not obj.is_deprecated)
    ctx["can_update"] = can_update
    if update:
        # update the cost
        if request.method == "POST":
            if not can_update:
                raise PermissionError("You can not update this cost.")
            if request.POST.get("update"):
                form = forms.get_cost_form(obj.object, request.POST)
                if form.is_valid():
                    pc = form.save(commit=False)
                    erp.update_cost(obj, pc)
                    return HttpResponseRedirect("..")
                else:
                    ctx["cost_form"] = form
            elif request.POST.get("update_erp"):
                product = models.OERPProduct.objects.get(part=obj.object).product
                cost = erp.get_product_data([product])[0]["standard_price"]
                pc, created = models.PartCost.objects.get_or_create(part=obj.object)
                pc.cost = cost
                erp.update_cost(obj, pc)
                return HttpResponseRedirect("..")
    else:
        ctx["cost_form"] = forms.get_cost_form(obj.object)
    ctx["cost"] = erp.compute_cost(obj)
    try:
        product = models.OERPProduct.objects.get(part=obj.object).product
    except models.OERPProduct.DoesNotExist:
        # allow to publish on openERP
        ctx["published"] = False
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
    else:
        # the current part has been published on openERP
        ctx["published"] = True
        ctx["product"] = erp.get_product_data([product])[0]
        ctx["boms"] = erp.get_bom_data(ctx["product"]["bom_ids"])
    return r2r("erp_summary.html", ctx, request)


