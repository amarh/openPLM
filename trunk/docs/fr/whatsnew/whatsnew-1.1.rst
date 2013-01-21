.. _whatsnew-1.1:

.. Images come later, once we are sure we would not have to update them ;)

=========================
Nouveautés d'OpenPLM 1.1
=========================

Changements pour l'utilisateur
==============================

Nouveau téléchargement de fichiers
----------------------------------

Vous pouvez télécharger (*upload-er*) vos fichiers depuis l'onglet Fichier de vos Documents tout en gardant
un oeil sur la liste des fichiers déjà présents.

Vous pouvez *upload-er* plusieurs fichiers simultanément.

Des barres de progressions apparaissent lors de l'upload des fichiers :

 * une pour chaque fichier envoyé
 * une barre de progression globale

Captures d'écran :

.. list-table::

    * - .. figure:: /whatsnew/1.1/Capture_openPLM_file_add.png
           :width: 100%

           Nouvelle page "Fichiers"
    
           Comme vous pouvez le voir , le formulaire d'*upload* et la liste des fichiers sont tous deux disponibles sur cette page.


    * - .. figure:: /whatsnew/1.1/Capture_openPLM_file_progress.png
           :width: 100%
               
           Barre de progression
           
           OpenPLM affiche désormais des informations sur la progression des *upload* de fichiers ainsi qu'une information sur la progression globale.


Fonctionnalité **Parcourir**
-----------------------------

Une nouvelle fonctionnalité est disponible, elle permet de parcourir tous les objets (parts, documents),
groupes et utilisateurs de votre OpenPLM.

Pour plus d'informations voir la documentation sur la fonctionnalité :ref:`fr-feat-browse` 


Cycle de vie et gestion
-------------------------

Les pages cycle de vie et gestion ont été fusionnées dans la page cycle de vie.

Remplacer un signataire est maintenant beaucoup plus intuitif, voir la capture d'écran ci-dessous :

.. image:: /whatsnew/1.1/Capture_openPLM_lifecycle_management.png


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
l'option "compte restreint".

Capture d'écran :

.. image:: /whatsnew/1.1/Capture_openPLM_sponsor.png
    :width: 100%


Comme vous pouvez le voir sur l'image ci-dessus, vous pouvez aussi parrainer un nouvel utilisateur
qui peut accéder à pratiquement tous les objets mais ne peut pas les modifier.

Vous pouvez aussi sélectionner une langue pour le nouvel utilisateur. Le mail le notifiant
de la création de son compte sera traduit en fonction de la langue choisie.


Timeline
---------

La timeline est un historique global qui contient :

 * l'historique des objets officiels
 * l'historique des objets appartenant aux groupes dont vous faites partie
 
 
Flux RSS
----------

Vous pouvez souscrire aux flux RSS relatif :

 * aux objets PLM
 * à un utilisateur
 * à un groupe
 * à la timeline

Les liens pour souscrire à ces flux sont accessibles depuis les pages :

 * "Historique"
 * "Timeline"

Chaque flux se met à jour lorsqu'une modification intervient sur  l' (les) objet(s), l'utilisateur 
ou le groupe associé(s) au flux.


Nouvelle application: oerp
---------------------------

Si vous utilisez OpenERP , OpenPLM dispose d'une nouvelle application qui permet de "publier"
vos parts officielles (et leur nomenclature) vers OpenERP.


document3D
-----------

L'application document3D a été améliorée.

Amélioration de la vue 3D
++++++++++++++++++++++++++


Mettre en évidence
~~~~~~~~~~~~~~~~~~~

Vous pouvez mettre une pièce en évidence en plaçant votre souris
sur le nom correspondant à cette pièce, tel que vous pouvez le voir sur 
la capture d'écran ci-dessous :

.. figure:: /whatsnew/1.1/3D3.png
    :width: 90%
    
    Mise en évidence
    
    La part mise en évidence ici est la part L-Bracket. Elle apparait en 
    rouge au lieu d'apparaitre en vert.


Ombres
~~~~~~~~~~

OpenPLM affiche les ombres dans la vue en 3D.

Captures d'écran :

.. list-table::

   * - .. figure:: /whatsnew/1.1/3D_old.png
            :width: 60%
            
            Avant (sans ombres)  
            
            
     - .. figure:: /whatsnew/1.1/3D1.png
            :width: 70%
            
            Maintenant (avec les ombres)

Sélectionner la vue
~~~~~~~~~~~~~~~~~~~

Une nouvelle bar d'outils permet de changer de vue (avant, au-dessus...).


Couleurs aléatoires et transparence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Vous pouvez choisir d'afficher votre produit avec des couleurs choisies aléatoirement
ou revenir aux couleurs initiales.
Vous pouvez aussi activer/désactiver la transparence et afficher/cacher les axes.


.. figure:: /whatsnew/1.1/3D2.png
    :target: http://www.openplm.org/example3D/mendelmax2.html
    :width: 90%
    
    Les nouvelles barres d'outils de la vue 3D
    
    Cliquez sur l'image pour tester ces nouvelles barres d'outils.

STL 
++++++++++++++

La vue 3D traite aussi les fichiers type STL (ASCII et formats binaires).


Aperçu des fichiers STEP
+++++++++++++++++++++++++

OpenPLM peut désormais générer l'aperçu d'un fichier STEP. Pour l'instant, 
seuls les fichiers STEP non décomposés sont gérés.

.. todo:: example


Accès WebDAV
--------------

OpenPLM propose aussi la gestion de fichier via un accés WebDAV :

.. figure:: /whatsnew/1.1/webdav_nautilus.png

    Une liste de répertoire utilisant nautilus


Bugs réparés
-------------


**Suggestion de référence pour les objets PLM**

`108 <http://wiki.openplm.org/trac/ticket/108>`_ step management - Suggested part references are all the same

`113 <http://wiki.openplm.org/trac/ticket/113>`_  Part - Suggested reference may cause some problem

`117 <http://wiki.openplm.org/trac/ticket/117>`_ Object creation - If you update the page suggested reference and reference change


**Nomenclature**

`121 <http://wiki.openplm.org/trac/ticket/121>`_ BOM - Display last level is not correct


**Document3D**

`104 <http://wiki.openplm.org/trac/ticket/104>`_ 3D data not copied when a Document3D is revised

`106 <http://wiki.openplm.org/trac/ticket/106>`_ document3D: can not decompose a step file defining two products with the same name


**Gestion des fichiers**

`124 <http://wiki.openplm.org/trac/ticket/124>`_ File check-in broken


**Parrainage**

`109 <http://wiki.openplm.org/trac/ticket/109>`_ Sponsorship - Character ' is authorised for username and leads to a bug


**Délégation de droits**

`119 <http://wiki.openplm.org/trac/ticket/119>`_ Delegation - We can delegate someone who is not in the same groupe as the object

Autres amélioration
--------------------

**Nomenclature**
 * télécharger sous format PDF
 
 * remplacer un assemblage ou une pièce


**Naviguer**

Si l'objet courrant est une part vous pouvez :

 * lier un nouveau document,
 * ajouter une nouvelle part (fils).
 
Si l'objet courrant est un document vous pouvez :

 * lier une nouvelle part.
  

**Part et Document**

 * annulation possible depuis l'onglet "CYCLE DE VIE"
 * clonage possible depuis l'onglet "ATTRIBUTS"


**Panneau de recherche**

La recherche s'exécute de manière asynchrone exceptée sur les pages de création
de liens (ajout de document ou part).


**Amélioration d'affichage**
 * onglet groupes
 * onglet révisions
 * ...


**Documentation** 

 * plus de fonctionnalités documentées
 * disponible en anglais


**Aperçu : nouveaux formats supportés**
 SolidWorks, Catia, Sketch Up, Pro Engineer 


Changements administrateur
===========================

Comptes restreints et publieur
-----------------------------------

Les comptes restreints représentent les utilisateurs dont le champ ``restricted`` vaut true (vrai).
Un utilisateur ayant un compte restreint :

 * ne peut ni être un contributeur ( il ne peut pas créer d'objet ou de groupe ou encore parrainer un autre utilisateur) ni être un administrateur
 * ne peut pas faire partie d'un groupe
 
Un "publieur" est un utilisateur dont le champ ``can_publish`` vaut true. Il peut publier
tous les objets PLM officiels auxquels il a accés. Un objet publié est visible par tous,
même les utilisateurs anonymes (non connecté).

Les champs ``restricted``et ``can_publish`` peuvent être modifiés via l'interface administrateur.
Pour plus d'informations voir :ref:`rest-account-specs` et :ref:`publication-specs` (en anglais).


Agencement des applications
-----------------------------

Il y a eu un grand changement sur l'agencement des applications.
Les applications optionnelles ont été placées dans le dossier *apps*.

Assurez vous que votre fichier settings.py a été mis à jour en conséquence :
à l'exception de plmapp, les applications d'openPLM sont dorénavant nommées :samp:`openPLM.apps.{NomDeLApplication}`

exemple : 

'openPLM.plmapp',
'openPLM.apps.cad',
'openPLM.apps.cae',
'openPLM.apps.office',

document3D
-----------

Nouvelle dépendance optionnelle : povray

Nouvelle application : oerp
-----------------------------

Cette application depend de oerplib et son utilisation nécessite une mise à jour de votre fichier settings.py , see :ref:`oerp-admin`


Changement pour les développeurs
================================

Nouvelles applications
------------------------

Quelques nouvelles applications ont été implémentées, voir :ref:`applications` pour plus d'informations.

