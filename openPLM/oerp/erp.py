import oerplib
from django.conf import settings

from openPLM.oerp import models

DEFAULT_PORT = 8070
DEFAULT_HTTP_PORT = 8069
DEFAULT_PROTOCOL = "netrpc"
DEFAULT_HTTP_PROTOCOL = "http"
PRODUCT_URI = "%(protocol)s://%(host)s:%(port)d/web/webclient/home?#id=%(id)d&view_type=page&model=product.product"
BOM_URI = "%(protocol)s://%(host)s:%(port)d/web/webclient/home?#id=%(id)d&view_type=page&model=mrp.bom"

EXPORT_ACTION = "OpenERP: published"

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
        product_id = prod_srv.create({"name" : name[:128], "default_code" : ref[:64] })  
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
    last_level = 1
    for level, link in children:
        if level < last_level:
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
        if last_level < level:
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

