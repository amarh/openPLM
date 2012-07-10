.. _whatsnew-1.1:

.. Images come later, once we are sure we would not have to update them ;)

=========================
Nouveautés d'OpenPLM 1.1
=========================

Changement pour l'utilisateur
=============================

Nouveau téléchargement de fichiers
----------------------------------

Vous pouvez télécharger (*upload-er*) vos fichiers depuis l'onglet Fichier de vos Documents tout en gardant
un oeil sur la liste des fichiers déjà présents.

Des barres de progressions apparaissent lors de l'upload des fichiers :
 * une pour chaque fichier envoyé
 * une barre de progression globale

.. todo:: image


Fonctionnalité **Parcourir**
-----------------------------

Une nouvelle fonctionnalité est disponible, elle permet de parcourir tous les objets (parts, documents),
groupes et utilisateurs de votre OpenPLM.


Cycle de vie et gestion
-------------------------

Les pages cycle de vie et gestion ont été fusionnées dans la page cycle de vie.

Remplacer un signataire est maintenant beaucoup plus intuitif.


Pages publiques
----------------

Vous pouvez à présent publier une part ou un document. Un objet pulié est accessible aux utilisateurs
anonymes (non-connectés).


Compte restreint et parrainage
--------------------------------------

Un nouveau type de compte est disponible : le compte restreint.

Un utilisateur ayant un compte restreint ne peut créer aucun contenu. 
Il ne peut qu'accéder à certaines parts et certains documents.

Grâce à ce nouveau type de compte, vous pourrez désormais partager des informations
avec d'autre personnes tout en étant sûr qu'ils (elles) ne pourront ni modifier le contenu partagé
ni accéder à des données confidentielles ou autres que celles partagées.

Pour créer un compte restreint vous n'avez qu'à parrainer un nouvel utilisateur et sélectionner
l'option "compte restreint" :
.. todo:: image


Comme vous pouvez le voir sur l'image ci-dessus, vous pouvez aussi parrainer un nouvel utilisateur
qui peut accéder à pratiquement tous les objets mais ne peut pas les modifier.


Timeline
---------

La timeline est un historique global qui contients :

 * l'historique des objets officiels
 * l'historique des objets appartenant aux groupes
 dont vous faites partie
 
 
Flux RSS
----------

Vous pouvez souscrire aux flux RSS de :

 * objets PLM
 * Utilisateur
 * Groupe
 * la timeline

Les liens pour souscrire à ces flux sont accessibles depuis les pages :

 * "Historique"
 * "Timeline"

Chaque flux se met à jour lorsqu'une modification intervient sur  l' (les) objet(s), l'utilisateur 
ou le groupe associé(s) au flux.


Nouvelle application: oerp
---------------------------

document3D
-----------

L'application document3D a été améliorée.

Amélioration de la vue 3D
++++++++++++++++++++++++++


Surbrillance
~~~~~~~~~~~~~~~

.. todo:: screenshots, gifs

Dégradés
~~~~~~~~~~

.. todo:: screenshots

Sélectionner la vue
~~~~~~~~~~~~~~~~~~~

Une nouvelle bar d'outils permet de changer de vue (avant, au-dessus...).

.. todo:: screenshots

Couleurs aléatoires et transparence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. todo:: screenshots

STL 
++++++++++++++

La vue 3D affiche aussi les fichiers type STL (ASCII et formats binaires).


Aperçu des fichiers STEP
+++++++++++++++++++++++++

OpenPLM peut désormais générer l'aperçu d'un fichier STEP. Pour l'instant, 
seuls les fichiers STEP non décomposés sont gérés.

.. todo:: example

Accès WebDAV
--------------


Bugs réparés
-------------

Autres amélioration
--------------------

Nomenclature : 
 * téléchargement sous format PDF
 * remplacer un assemblage

Annulation de part et de document

Amélioration d'affichage :
groupes, révisions...

Panneau de recherche : asynchrone

Documentation: 

    * Plus de fonctionnaliés documentées
    * disponible en anglais


Aperçu : nouveaux formats supportés
SolidWorks, Catia, Sketch Up, Pro Engineer 


Changements administrateur
===========================

Comptes restreints et publieur
-----------------------------------

Agencement des applications
-----------------------------

Il y a eu un grand changement sur l'agencement des applications.
Les applications optionnelles ont été placées dans le dossier *apps*.

Assurez vous que votre fichier settings.py a été mis à jour en conséquence :
à l'exception de plmapp, les applications d'openPLM sont dorénavant notées openPLM.apps.NomDeLAppli .

exemple : 

'openPLM.plmapp',
'openPLM.apps.cad',
'openPLM.apps.cae',
'openPLM.apps.office',

document3D
-----------

Nouvelle dépendance optionnelle: povray

Nouvelle application : oerp
-----------------------------

Changement pour les développeurs
================================


