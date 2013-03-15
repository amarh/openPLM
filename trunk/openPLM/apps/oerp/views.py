from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from openPLM.plmapp.views.base import get_generic_data, handle_errors
from openPLM.plmapp.exceptions import PermissionError
from openPLM.plmapp.forms import ConfirmPasswordForm
from openPLM.plmapp.utils import r2r

from openPLM.apps.oerp import erp
from openPLM.apps.oerp import forms
from openPLM.apps.oerp import models

CONNECTION_ERROR = _("Could not connect to OpenERP")

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
                try:
                    cost = erp.get_product_data([product])[0]["standard_price"]
                except erp.ERPError:
                    messages.error(request, CONNECTION_ERROR)
                else:
                    try:
                        pc, created = models.PartCost.objects.get_or_create(part=obj.object)
                    except:
                        pc = models.PartCost(part=obj.object)
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
                    try:
                        erp.export_bom(obj)
                    except ERPError:
                        messages.error(request, CONNECTION_ERROR)
                return HttpResponseRedirect("..")
            else:
                form = ConfirmPasswordForm(request.user)
            ctx["password_form"] = form
    else:
        # the current part has been published on openERP
        ctx["published"] = True
        try:
            ctx["product"] = erp.get_product_data([product])[0]
            ctx["boms"] = erp.get_bom_data(ctx["product"]["bom_ids"])
        except erp.ERPError:
            ctx["openerp_error"] = True
    return r2r("erp_summary.html", ctx, request)


