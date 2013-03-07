"""
Management utility to create units of measure.
"""

import os.path

from django.core.management.base import BaseCommand

UNIT_TO_UOM_FILE = os.path.join("apps", "oerp", "_unit_to_uom.py")
class Command(BaseCommand):

    help = 'Used to create all required units in OpenERP'

    def handle(self, *args, **options):

        from openPLM.apps.oerp.erp import get_oerp
        from openPLM.plmapp.utils.units import UNITS

        uom_srv = get_oerp().get("product.uom")
        names = {"-" : "PCE", "L" : "Litre" }
        unit_to_uom = {}
        for cat, units in UNITS:
            for id, name in units:
                name = name.format() # name is a proxy, format() returns a unicode
                oname = names.get(id, name)
                uoms = uom_srv.search([("name", "=", oname),])
                if uoms:
                    unit_to_uom[id] = uoms[0]
        with open(UNIT_TO_UOM_FILE, "w") as f:
            f.write("UNIT_TO_UOM = {\n")
            for key, value in unit_to_uom.iteritems():
                f.write('    "%s" : %d,\n' % (key, value))
            f.write("}\n")

