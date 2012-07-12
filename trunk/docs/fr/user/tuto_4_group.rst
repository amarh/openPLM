.. _fr-group-func:

===================================
Fonctions liées aux **GROUPES**
===================================

Ce document décrit les fonctions utilisées pour afficher et manipuler les
**Groupes** dans openPLM.


APERÇU
======

Les **Groupes** sont des objets standards de Django. Depuis OpenPLM vous pouvez modifier
 certains attributs.

Dans OpenPLM, le *type* est **Group**.

Chaque **Groupe** posséde un *nom* unique.

.. hint :: Exemple : Group / leading-group / -


ATTRIBUTS
==========

Affiche la carte d'identification du groupe.

On y retrouve des attributs standards tels que le nom, la description, la date de création ..
On trouve aussi des attributs personnalisés qui dépendent de la configuration
de OpenPLM qui a été effectué.


Si vous possédez les autorisations nécessaires, vous pouvez **Éditer** certains attributs.

.. note :: On peut effectuer des recherches en fonction des attributs.


HISTORIQUE
===========

Affiche l'historique du groupe.

Ceci offre une traçabilité complète des actions effectuées sur le groupe.

Une icone RSS sur cette page vous permet de vous abonner au flux d'actualités du groupe.

UTILISATEURS
=============

Liste les membres du groupe et les invitations et demandes en attente .

Depuis cet onglet vous pourrez :

    * inviter des utilisateurs à rejoindre le groupe , si vous possédez les autorisations nécessaires
    * retirer des utilisateurs du groupe, si vous possédez les autorisations nécessaires
    * demander à rejoindre le groupe


OBJETS
=======

Affiche les "cartes d'identité" des objets appartenant au groupe.

