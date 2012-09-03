==================================
document3D -- Step et documents 3D
==================================

Cette application ajoute un type de document **Document3D** qui permet l'affichage
d'un fichier STEP dans le navigateur à l'aide de `WebGL <http://www.khronos.org/webgl/>`_. Il ajoute aussi la
possibilité de décomposer un fichier STEP en plusieurs parts et documents,
puis de recomposer un fichier STEP à jour.


Dépendances
===========

Cette application dépend de `pythonOCC <http://www.pythonocc.org/>`_. Elle a été testé avec la version 0.5.

.. versionchanged:: 1.1

Elle dépend aussi de `POV-Ray <http://www.povray.org/>`_ pour générer des aperçus des fichiers STEP. Testé avec la version 3.6.1.


settings.py
===========

Pour pouvoir utiliser l'application *Document3D*, il faut qu'elle est été
activé dans le fichier settings : 
ajouter ``'openPLM.apps.document3D'`` à la liste des applications installées (:const:`INSTALLED_APPS`).

Enfin, il est nécessaire de crée un répertoire dans le dossier media : 

    * ``mkdir media/3D/``
    * ``chown www-data:www-data media/3D``


Synchronisation de la base de données
=====================================

Exécuter ``./manage.py migate document3D && ./manage.py update_index document3D``.
Ensuite, redémarrer celery et apache.


Test
====

Pour tester l'application, il faut créer un nouveau Document3D et rajouter un
fichier STEP (un fichier d'exemple est fourni :file:`document3D/data_test/test.stp`).
Après un léger temps d'attente, une vue 3D sera accessible depuis l'onglet 3D.
Votre fichier STEP devrai apparaitre si le navigateur supporte WebGL.

En cas de dysfonctionnement, consulter le fichier log de celery (:file:`/var/log/celery/`) pour rechercher une erreur.
Un échange normal entre les logiciels devrait faire apparaitre une ligne de ce
genre 
``[2012-03-12 14:46:48,089: INFO/MainProcess] Task openPLM.apps.document3D.models.handle_step_file[9f732451-1b43-497c-8b89-f726db861941] succeeded in 27.816108942s: True``.

Si la vue 3D fonctionne, vous pouvez essayer de décomposer le fichier STEP : 

    #. Attacher un document à un draft part possédant une nomenclature vide.
    #. Aller à la page "NOMENCLATURE" de la part.
    #. Un message expliquant que la part peut être décomposer devrait
           apparaître, cliquer sur "Oui"
    #. Remplir le formulaire et cliquer sur le bouton "créer"
    #. Si tout est correct, votre part devrait avoir une nomenclature complète. Chaque part enfant ayant un Document3D d'attacher, visible dans l'onglet 3D.
    #. Maintenant, le fichier STEP original est liée à la nomenclature, donc si un fichier STEP enfant est mis à jour, ou si un lien de nomenclature est supprimé, le fichier STEP sera mis à jour.

.. note::
    Vous pouvez vérifier que votre navigateur supporte WebGL `ici <http://get.webgl.org>`_.



