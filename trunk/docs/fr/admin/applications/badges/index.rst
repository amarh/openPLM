.. _badges-admin:

===============================================
badges - 
===============================================

.. warning::

    Cette application est encore à un stade de développement précoce.

Cette application ajoute un onglet "BADGES" sur la page d'un utilisateur.


settings.py
==============

L'application *badges* doit être activée dans le fichier settings pour être
utilisée. Pour cela, rajouter ``'openPLM.apps.badges'``  à la liste des applications installées (:const:`INSTALLED_APPS`).



Synchronisation de la base de données
=====================================

Exécuter ``./manage.py migrate badges``.


Attribuer les badges
=====================

Si vous aviez déjà installé un OpenPLM, vous pouvez mettre à jour la liste
des badges obtenus par les utilisateurs en fonction de leurs actions antérieures à
l'installation de l'application *badges*.

Pour cela exécutez ``./manage.py award_badges``.

Tester
=========

Connectez vous à OpenPLM , rendez sur votre profil (puis sur l'onglet "BADGES") et vérifiez si vous avez obtenu un badge.

Si vous n'avez aucun badge, vous pouvez obtenir le badge Autobiographe en remplissant votre profile
(nom, prénom et email).

À partir de l'onglet "Badges" et de la page descriptive de chaque badge, vous pouvez accéder à la liste
des badges disponibles.

