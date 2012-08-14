.. _fr-user-func:

====================================
Fonctions liées aux **UTILISATEURS**
====================================

Ce document décrit les fonctions utilisées pour afficher et manipuler les
**Utilisateurs** dans openPLM.


APERÇU
======

Les **Utilisateurs** sont des objets standard de Django. Depuis OpenPLM, vous
pouvez modifier certains attributs, changer votre mot de passe et déléguer vos
autorisations.

Dans OpenPLM, le *type* est **Utilisateur**.

Dans la classe **Utilisateur**, il y a plusieurs instances avec un *nom
d'utilisateur*.

Chaque **Utilisateur** possède un *nom d'utilisateur* unique.

.. hint :: Exemple : User / pdurand / -

On peut créer des lien entre un **Utilisateur** et une **Part** ou un
**Document**. Ces liens définissent les différentes autorisations que possèdent les
**Utilisateurs** sur chaque **Part** et chaque **Document**

On peut créer des lien de délégation entre les **Utilisateurs** pour effectuer
des transferts d'autorisations.


ATTRIBUTS
=========

Affiche la carte d'identification de l'utilisateur.

On trouve des attributs standards comme le nom de famille et le prénom,
l'adresse email, la date de création, ...
On trouve aussi des attributs personnalisés qui dépendent de la configuration
de OpenPLM qui a été effectué.

Si vous possédez les autorisations nécessaires, vous pouvez **Éditer** les
attributs et les modifier.

Si vous avez les autorisations nécessaires, vous pouvez aussi changer le **mot
de passe**

.. note :: On peut effectuer des recherches en fonction des attributs.


HISTORIQUE
==========

Affiche l'historique de l'utilisateur.

Ceci offre une traçabilité complète des actions des utilisateurs.

Une icone RSS sur cette page vous permet de vous abonner au flux d'actualités de l'utilisateurs.

PARTS-DOC-CAD
========================================================

Affiche les Parts et Documents de l'utilisateur courant.


DÉLÉGATION
========================================================

Affiche les parrainages effectués par l'utilisateur et les rôles de
chaque utilisateurs parrainés.

Si vous avez les autorisations nécessaires, vous pouvez 
  * **Ajouter** des utilisateurs sponsorisés/parrainés pour chaque rôle.

  * **Révoquer** un parrainage.


.. _add-user:

Ajouter un utilisateur (parrainer)
++++++++++++++++++++++++++++++++++++++

Rendez-vous sur votre page utilisateur :

    * en cliquant sur le bouton ETUDIER dans la page d'accueil,
    * en cliquant sur votre nom .
    
À partir de l'onglet DELEGATION cliquez sur le bouton Parrain.
Vous devriez arriver sur une page permettant de parrainer un nouvel
utilisateur. Remplissez le formulaire en n'oubliant pas d'ajouter un groupe
(un groupe par défaut a été créé lors de l'installation), et assurez vous de
renseigner une adresse email valide. Ensuite, valider.

.. image:: images/sponsor.png


Le nouvel utilisateur a été créé et un email contenant ses paramètres de
connexion à été envoyé.


GROUPES
========================================================
Affiche les Groupes auxquels appartient l'utilisateur.
