.. _webdav-admin:

===============================================
webdav -- prise en charge de WebDAV
===============================================

.. warning::

    Cette application est encore à un stade de développement précoce.

Cette application ajoute un accés WebDAV aux documents et fichiers
enregistrés dans openPLM.

Actuellement, openPLM exporte tous les documents et suit la 
hierachie suivante : :samp:`/{type}/{reference}/{revision}/{files*}`.

Un utilisateur peut récupérer un ou plusieurs fichiers, 
ajouter un fichier à un document et supprimer des fichiers.

OpenPLM vérifie que toutes les actions sont autorisées : par exemple, openPLM 
empêche un utilisateur de supprimer un fichier appartenant à un document officiel.

Les actions vérouiller, dé-vérouiller, créer et éditer les propriétés
ne sont pas implémentées.


settings.py
==============

L'application *webdav* doit être activée dans le fichier settings pour être
utilisée. Pour cela, rajouter ``'openPLM.apps.webdav'``  à la liste des applications installées (:const:`INSTALLED_APPS`).


Apache
=========

Assurez vous que

.. code-block:: apache

    WSGIPassAuthorization On 

est défini dans votre fichier de configuration apache.


Test
=========

Pour tester cette application, accédez à :samp:`http://{server}/dav/` via un client 
WebDAV et parcourez vos documents.

