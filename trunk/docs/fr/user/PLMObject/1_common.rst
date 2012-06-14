===============================================================
Fonctions en commun pour les objets PLM **PART** / **DOCUMENT**
===============================================================

APERÇU
======
Les **Parts** et les **Documents** sont des objets PLM. Ils représentent un
produit dans la vraie vie.

Par exemple : un vélo, un paquets de gâteaux, un médicament, une roue, un
dessin, un document 3D, ...

**Part** et **Document** sont des sous classes de PLMObject. Vous pouvez
définir des sous classes de **Part** et **Document** adaptés au domaine de
l'industrie pour lequel vous utilisez OpenPLM. Chaque sous-classe est défini
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
suivre les modifications majeures. Elles suivent une séquence du type a, b, c ou 1, 2, 3 ou n'importe qu'elle autre séquence personnalisée.

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
Affiche la carte d'identification d'une part.

On y trouve des attributs standard comme le nom, la date de création, le
propriétaire...
On y trouve aussi des attributs personnalisés qui dépendent du paramétrage
effectué par la société utilisant OpenPLM.

Si vous avez les autorisation nécessaires, vous pouvez **Éditer** les attributs
et les modifier.

.. note :: Il est possible d'effectuer des recherches en fonction des attributs.


CYCLE DE VIE
============
Affiche le cycle de vie d'une part.

On y trouve les différents état de la part, incluant l'état courant. Ces
cycles de vie sont personnalisables en fonctions des besoins de l'entreprise.

Si vous avez les autorisations nécessaires, vous pouvez **Valider** ou
**Annuler** une part.

Il est possible d'ajouter des triggers sur les actions **Valider/Annuler**
(vérification des autorisations, envoi d'email, validation d'un autre
PLMObject ...)


RÉVISIONS
=========
Affiche toutes les révisions d'une part

Si la part courante est la dernière révision, on peut en ajouter une nouvelle.


HISTORIQUE
==========
Affiche l'historique d'une part.

Cela permet une traçabilité complète de la part.


MANAGEMENT
==========
Affiche les utilisateurs liés et leurs autorisations sur la part.

Si vous avez les autorisations nécessaires, vous pouvez **Remplacer** certains
utilisateurs. Vous pouvez aussi inscrire un ou plusieurs utilisateurs aux
notifications emails : l'utilisateur recevra un email pour chaque évènement en
rapport avec la part (révisions, modifications, validations, ...)
