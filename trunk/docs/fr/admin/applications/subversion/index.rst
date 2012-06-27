.. _subversion-admin:

====================================================
subversion -- Application pour les dépôts Subversion
====================================================

Cette application ajoute un document **SubversionRepository** qui est un lien
vers un dépôt svn.


Dépendances
===========

L'application *subversion* nécessite la dépendance suivante : 

    * `pysvn <http://pysvn.tigris.org/>`_

settings.py
===========

Pour utiliser l'application *subversion*, il faut qu'elle soit activée dans le
fichier settings : ajouter ``'openPLM.apps.subversion'`` à la liste des applications installées
(:const:`INSTALLED_APPS`).

Synchronisation de la base de données
=====================================

Exécuter ``./manage.py migrate subversion``.

Test
====

Pour tester l'application, créer un nouveau SubersionRepository.
Si OpenPLM parvient à s'y connecter, la page *logs* affichera la liste des
derniers changesets.

OpenPLM ne demandera *pas* de mot de passe pour se connecter au dépôt svn.


