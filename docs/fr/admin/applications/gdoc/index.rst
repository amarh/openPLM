.. _gdoc-admin:

===================================
gdoc -- Application Google Document 
===================================

Cette application ajoute un document **GoogleDocument** qui est lié à un
document stocké sur `Google Document <https://docs.google.com/#home>`_. 


Dépendances
===========

L'application *gdoc* ajoute les dépendances suivantes : 

    * `gdata <http://code.google.com/intl/fr-FR/apis/gdata/>`_
    * `google-api-python-client <http://code.google.com/p/google-api-python-client/>`_

Vous pouvez les installer en utilisant *pip* ou *easy_install* : 

    * ``pip install gdata google-api-python-client``


OAuth 2
=======

*gdoc* utilise OAuth 2 pour authentifier un utilisateur, ainsi OpenPLM n'a pas
besoin de stocker les mots de passe des utilisateurs.

Pour cela, il vous faut enregistrer votre application auprès de Google : 

    1. Aller sur https://code.google.com/apis/console/ , si vous n'avez encore jamais enregistré d'applications, vous devriez voir cette page : 

       .. image:: images/gapi_1.png

    #. Cliquez sur le bouton *Create project*.

       .. image:: images/gapi_2.png

    #. Cliquez sur le lien d'accès à l'API.

       .. image:: images/gapi_3.png

    #. Cliquez surle bouton *Create an OAuth 2.0 client ID...* ; un formulaire devrait apparaitre. Sur la deuxième page, rajouter le nom de domaine de votre site :

       .. image:: images/gapi_4.png

    #. Rentrez le nom de domaine de votre application et valider le formulaire. Vos identifiants sont contenus dans les champs client ID et client secret.

       .. image:: images/gapi_5.png


settings.py
==============

Pour utiliser l'application *gdoc*, il faut qu'elle soit activée dans le
fichier settings : 
ajouter ``'openPLM.apps.gdoc'`` à la liste des applications installées (:const:`INSTALLED_APPS`).

A la fin du fichier :file:`settings.py`, ajouter les deux variables suivantes::
    
    GOOGLE_CONSUMER_KEY = u'client id from Google API access page'
    GOOGLE_CONSUMER_SECRET = u'client secret from Google API access page'

Synchronisation de la base de données
=====================================

Run ``./manage.py migrate gdoc``.

Test
====

Pour vérifier que l'application fonctionne, créer un nouveau GoogleDocument.
Vous serez ensuite redirigé sur une page demandant si vous souhaiter autoriser
OpenPLM à accéder au document. Accepter et vous devriez être capable d'accéder
aux documents.


