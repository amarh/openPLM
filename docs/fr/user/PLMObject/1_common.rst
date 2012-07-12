===============================================================
Fonctions en commun pour les objets PLM **PART** / **DOCUMENT**
===============================================================

APERÇU
======

Les **Parts** et les **Documents** sont des objets PLM. Ils représentent un
produit dans la vraie vie.

Par exemple : un vélo, un paquets de gâteaux, un médicament, une roue, un
dessin, un document 3D, ...

**Part** et **Document** sont des sous classes de **PLMObject**. Vous pouvez
définir des sous classes de **Part** et **Document** adaptées au domaine de
l'industrie pour lequel vous utilisez OpenPLM. Chaque sous-classe est définie
comme un *type*.

========================    ===============================     ===============================
Exemple 1 :                 Exemple 2 :                         Exemple 3 :                    
========================    ===============================     ===============================
PLMObject                   PLMObject                           PLMObject                      
...=> Part                  ...=> Part                          ...=> Document                    
......=> Bicycle            ......=> CardboardPacking           ......=> Drawing      
......=> Wheel              ......=> PlasticWrap                ......=> Standard
......=> Handlebar          ......=> Cake                       ......=> TestData
......=> Saddle             ......=> Floor                      ......=> Document3D
......=> ...                ......=> ...                        ......=> ...
========================    ===============================     ===============================

Dans une sous classe/type, vous avez plusieurs instances avec une *référence*.

Pour chaque référence, vous pouvez avoir plusieurs *révisions* permettant de
suivre les modifications majeures. Elles suivent une séquence du type a, b, c ou 1, 2, 3 ou n'importe quelle autre séquence personnalisée.

Chaque **Part** et chaque **Document** possède un unique jeu de *type*,
*référence*, *révision*.

.. hint :: Exemple : Bicycle / BI-2010 / a

Les assemblages et sous assemblages sont aussi des Parts. Il est possible de
créer des liens entre un assemblage et une autre Part. Ainsi, nous pouvons
définir l'assemblage et construire une Nomenclature (BOM - Bill Of Material).

Il est possible de créer un lien entre une **Part** et un **Document**. Chaque
Document aide à définir et décrire la Part

Les Documents peuvent contenir un ou plusieurs fichiers électronique.


ATTRIBUTS
=========

Affiche la carte d'identification d'un objet.

On y trouve des attributs standard comme le nom, la date de création, le
propriétaire...
On y trouve aussi des attributs personnalisés qui dépendent du paramétrage
effectué par la société utilisant OpenPLM.

Si vous avez les autorisation nécessaires, vous pouvez :
  * **Éditer** les attributs et les modifier,
  * **Cloner** l'objet courant.

.. note :: Il est possible d'effectuer des recherches en fonction des attributs.


CYCLE DE VIE
============

Affiche :
 * le cycle de vie d'un objet
    
 * les utilisateurs liés et leurs droits sur l'objet.

On y trouve les différents état de l'objet, incluant l'état courant. Ces
cycles de vie sont personnalisables en fonctions des besoins de l'entreprise.

Si vous avez les autorisations nécessaires, vous pouvez :
 * **Valider** ou **Refuser** l'objet
 
 * **Annuler** l'objet
    
 * **Remplacer** certains signataires ou utilisateurs notifiés
    
 * **Inscrire** ou **Supprimer** des utilisateurs aux notifications emails ,
   il recevra un email pour chaque évènement en rapport avec l'objet (révisions, 
   modifications, validations, ...)

Il est possible d'ajouter des triggers sur les actions **Valider/Refuser**
(vérification des autorisations, envoi d'email, validation d'un autre
objet PLM ...)


RÉVISIONS
=========

Affiche toutes les révisions d'un objet.

Si l'objet courant est la dernière révision, on peut en ajouter une nouvelle.


HISTORIQUE
==========

Affiche l'historique d'un objet.

Cela garantit une traçabilité complète de l'objet.

Une icone RSS sur cette page vous permet de vous abonner aux actualités de l'objet.
