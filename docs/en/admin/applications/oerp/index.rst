.. _oerp-admin:

====================================
oerp -- OpenERP Application
====================================

That applications adds an "ERP" tab on all parts to export an official BOM
to OpenERP.

Dependencies
==============

The *oerp* application depends on `oerplib <https://launchpad.net/oerplib>`_
(tested version: 0.5.0).

It is installable through *pip* or *easy_install*:

    * ``pip install oerplib``


settings.py
==============

To enable the *oerp* application, it must be enabled in the settings file: add
``'openPLM.apps.oerp'`` to the list of installed applications
(:const:`INSTALLED_APPS`).

At the end of the :file:`settings.py` file, adds the following settings::
    
    OERP_HOST = "openerp.example.com"
    OERP_DATABASE = "oerp_database" # name of the database
    OERP_USER = "admin" # an user who can create a product and a BOM
    OERP_PASSWORD = "OERP_USER password"
    OERP_PROTOCOL = "netrpc" # or "xmlrpc"
    OERP_PORT = 8070
    OERP_HTTP_PROCOLE = "http" # or "https"
    OERP_HTTP_PORT = 8069

The OpenERP server must have the MRP module installed.

Synchronizing the database
==========================

Run ``./manage.py migrate oerp``.

Creating required units
=======================

You must import a list of units of measure into OpenERP.
OpenPLM ships with a CSV file (:file:`oerp/product.uom.csv`) that can be
imported into OpenERP.

Once all units are imported into OpenERP. You must run the following
command:

 * ``./manage.py createuom``

This should create a file named :file:`oerp/_unit_to_uom.py` that should
contain something like this::

    UNIT_TO_UOM = {
        "dL" : 42,
        "dm" : 43,
        "kg" : 2,
        "g" : 3,
        "cm" : 40,
        "cL" : 39,
        "mm" : 48,
        "-" : 1,
        "m" : 7,
        "L" : 11,
        "km" : 44,
        "m3" : 45,
        "mL" : 47,
        "dg" : 41,
        "cg" : 38,
        "mg" : 46,
    }

The order and the numbers may differ but its important that all units are present.

.. note::

    Currently the mole unit is not supported.


Testing
=========

To test this application, create a new part an officialize it.
An :guilabel:`ERP` tab should be available. Click on this tab and then,
on the :guilabel:`Publish on OpenERP` button. A pop-up asking your password
(of your openPLM account) should appear. Fill the form and validate.
If no error occurs, a list of links related to the created product should
appear.



