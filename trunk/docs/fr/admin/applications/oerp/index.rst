.. _oerp-admin:

===========================
oerp -- Application OpenERP 
===========================

Cette application rajoute un onglet ERP à toutes les parts pour exporter une 
nomenclature officielle vers OpenERP.

Dépendances
===========

L'application *oerp* dépend de `oerplib <https://launchpad.net/oerplib>`_.
(version testée 0.5.0)

On peut l'installer via *pip* ou *easy_install*:

    * ``pip install oerplib``


settings.py
===========

L'application *oerp* doit être activer dans le fichier settings pour être
utilisée. Pour cela, rajouter ``'openPLM.apps.oerp'``  à la liste des applications installées (:const:`INSTALLED_APPS`).

A la fin du ficher :file:`settings.py`, ajouter les paramètres suivants::
    
    OERP_HOST = "openerp.example.com"
    OERP_DATABASE = "oerp_database" # name of the database
    OERP_USER = "admin" # an user who can create a product and a BOM
    OERP_PASSWORD = "OERP_USER password"
    OERP_PROTOCOL = "netrpc" # or "xmlrpc"
    OERP_PORT = 8070
    OERP_HTTP_PROCOLE = "http" # or "https"
    OERP_HTTP_PORT = 8069

Le module MRP doit être installé sur le serveur OpenERP.

Synchronisation de la base de données
=====================================

Exécuter ``./manage.py migrate oerp``.

Création des unités requises
============================

Il faut importer une liste des unités de mesure dans OpenERP.
OpenPLM dispose d'un fichier CSV (:file:`oerp/product.uom.csv`) qui peut être
importé dans OpenERP.

Une fois que toutes les unités ont été importées, il vous faut exécuter la
commande suivante :

 * ``./manage.py createuom``

Cela devrait créer un fichier nommé :file:`oerp/_unit_to_uom.py` contenant
quelque chose de ce genre::

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

L'ordre et les nombres peuvent être différents, ce qui est important c'est que
toutes les unités soient présentes.

.. note::

    A l'heure actuelle, l'unité la mole n'est pas supportée.


Test
====

Pour vérifier que tout fonctionne, il faut créer une nouvelle part et la
publier. 
Un onglet :guilabel:`ERP` devrait être disponible. Cliquer sur l'onglet puis
sur le bouton :guilabel:`Publish on OpenERP`. Un pop-up vous demandant votre
mot de passe OpenPLM devrait apparaitre. Renseigner les champs avant de
valider.
S'il n'y a eu aucune erreur, une liste de liens en relation avec le produit
créé devrait apparaître



