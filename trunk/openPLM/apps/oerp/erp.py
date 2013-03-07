from itertools import izip

from django.conf import settings
try:
    import oerplib
    import oerplib.error
    ERPError = oerplib.error.Error
    CAN_EXPORT_TO_OERP = True
except ImportError:
    CAN_EXPORT_TO_OERP = False
    ERPError = Exception # fake exception for try...except block

from openPLM.plmapp.utils.units import convert_unit, UnitConversionError
from openPLM.apps.oerp import models

DEFAULT_PORT = 8070
DEFAULT_HTTP_PORT = 8069
DEFAULT_PROTOCOL = "netrpc"
DEFAULT_HTTP_PROTOCOL = "http"
PRODUCT_URI = "%(protocol)s://%(host)s:%(port)d/web/webclient/home?#id=%(id)d&view_type=page&model=product.product"
BOM_URI = "%(protocol)s://%(host)s:%(port)d/web/webclient/home?#id=%(id)d&view_type=page&model=mrp.bom"

EXPORT_ACTION = "OpenERP: published"
COST_ACTION = "Cost: updated"

def format_uri(uri, **kwargs):
    data = {
            "host" : settings.OERP_HOST,
            "port" : getattr(settings, "OERP_HTTP_PORT", DEFAULT_HTTP_PORT),
            "protocol" : getattr(settings, "OERP_HTTP_PROTOCOL", DEFAULT_HTTP_PROTOCOL),
            }
    data.update(kwargs)
    return uri % data
    

def unit_to_uom(unit):
    # FIXME: no mol unit
    from _unit_to_uom import UNIT_TO_UOM
    return UNIT_TO_UOM[unit]

def uom_to_unit(uom):
    from _unit_to_uom import UNIT_TO_UOM
    return dict((v, k) for k, v in UNIT_TO_UOM.iteritems())[uom]


def get_oerp():
    oerp = oerplib.OERP(settings.OERP_HOST,
            protocol=getattr(settings,"OERP_PROTOCOL", DEFAULT_PROTOCOL),
            port=getattr(settings, "OERP_PORT", DEFAULT_PORT))
    oerp.login(settings.OERP_USER,
               settings.OERP_PASSWORD,
               settings.OERP_DATABASE)
    return oerp


def export_part(obj, prod_srv=None):
    try:
        prod = models.OERPProduct.objects.get(part=obj.id)
    except models.OERPProduct.DoesNotExist:
        if prod_srv is None:
            oerp = get_oerp()
            prod_srv = oerp.get("product.product")
        ref = " / ".join((obj.type, obj.reference, obj.revision))
        name = u"%s - %s" % (obj.name, obj.revision) if obj.name else ref
        try:
            pc = models.PartCost.objects.get(part=obj.id)
            cost = pc.cost
            uom = unit_to_uom(pc.unit)
        except (models.PartCost.DoesNotExist, KeyError):
            cost = 1
            uom = unit_to_uom("-")
        product_id = prod_srv.create({
            "name" : name[:128],
            "default_code" : ref[:64],
            "uom_id" : uom,
            "standard_price" : cost,
        })  
        prod = models.OERPProduct.objects.create(part=obj, product=product_id)
    return prod


def export_bom(ctrl):
    oerp = get_oerp()
    prod_srv = oerp.get("product.product")
    uom_srv = oerp.get("product.uom")
    bom_srv = oerp.get("mrp.bom")
    children = ctrl.get_children(max_level=-1)
    prod = export_part(ctrl.object, prod_srv)
    data = {"product_id" : prod.product,
        "product_qty" : 1,
        "name" : "BOM %s" % ctrl.name,
        "product_uom" : unit_to_uom("-"),
        }
    bom = bom_srv.create(data)
    models.OERPRootBOM.objects.create(part=ctrl.object, bom=bom)
    boms = [bom]
    last_level = 0
    for level, link in children:
        if level <= last_level:
            del boms[level:]
        try:
            bom = models.OERPBOM.objects.get(link=link).bom
        except models.OERPBOM.DoesNotExist:
            prod_child = export_part(link.child, prod_srv)
            data = {"product_id" : prod_child.product,
                "product_qty" : link.quantity,
                "name" : "BOM %d - %d" % (link.parent_id, link.child_id),
                "product_uom" : unit_to_uom(link.unit),
                "bom_id" : boms[-1],
                }
            bom = bom_srv.create(data)
            models.OERPBOM.objects.create(bom=bom, link=link)
        boms.append(bom)
        last_level = level
    # TODO: errors handling
    uri = format_uri(PRODUCT_URI, id=boms[0])
    details = u"Part published on OpenERP\n%s" % uri
    ctrl._save_histo(EXPORT_ACTION, details)
    return prod, boms[0]
        
        
def get_bom_data(bom_ids, bom_srv=None):
    if bom_srv is None:
        oerp = get_oerp()
        bom_srv = oerp.get("mrp.bom")

    boms = bom_srv.read(bom_ids)
    for data in boms:
        data["uri"] = format_uri(BOM_URI, id=data["id"])
    return boms
    
def get_product_data(product_ids, prod_srv=None):
    if prod_srv is None:
        oerp = get_oerp()
        prod_srv = oerp.get("product.product")

    products = prod_srv.read(product_ids)
    for data in products:
        data["uri"] = format_uri(PRODUCT_URI, id=data["id"])
    return products


def compute_cost(part_ctrl):
    cost = 0
    try:
        pc = models.PartCost.objects.get(part=part_ctrl.object)
        cost += pc.cost
        unit = pc.unit
    except models.PartCost.DoesNotExist:
        unit = "-"
    individual_cost = cost

    ids = []
    children = part_ctrl.get_children(-1)
    if children:
        for level, link in children:
            ids.append(link.child_id)
        # total local cost
        pcs = models.PartCost.objects.filter(part__in=ids).values()
        pcs = dict((p["part_id"], p) for p in pcs)
        for level, link in children:
            try:
                pc = pcs[link.child_id]
                cost += link.quantity * convert_unit(pc["cost"], link.unit, pc["unit"]) 
            except (KeyError, UnitConversionError):
                pass
    total_local_cost = cost

    # total erp cost
    ids.append(part_ctrl.id)
    products = models.OERPProduct.objects.filter(part__in=ids).values()
    try:
        data = get_product_data([p["product"] for p in products])
    except ERPError:
        total_erp_cost = 0
    else:
        products = dict((p["part_id"], d) for p, d in izip(products, data))
        try:
            total_erp_cost = products[part_ctrl.id]["standard_price"]
        except KeyError:
            total_erp_cost = 0
        for level, link in children:
            try:
                pc = products[link.child_id]
                total_erp_cost += link.quantity * convert_unit(pc["standard_price"],
                        link.unit, uom_to_unit(pc["uom_id"][0])) 
            except (KeyError, UnitConversionError):
                pass

    return models.Cost(individual_cost, unit, total_local_cost, total_erp_cost)


def update_cost(ctrl, part_cost):
    part_cost.save()
    details = u"Cost: %.2f, unit: %s" % (part_cost.cost, part_cost.get_unit_display()) 
    ctrl._save_histo(COST_ACTION, details)

