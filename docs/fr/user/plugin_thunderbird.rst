=======================
Plugin pour Thunderbird
=======================


Compilation et Installation
===========================

Récupération des sources
------------------------

Ce plugin est disponible sur le svn dans le répertoire :file:`trunk/plugins/thunderbird`.

Dépendances
-----------

Bien entendu, vous avez besoin de Thunderbird. Ce plugin a été testé avec les
version 3.0 et 3.1.

Compilation
-----------

.. note::
    Il est possible d'ignorer cette étape en récupérant directement ce :download:`fichier <download/openplm.xpi>`.
    Il est par contre possible que ce fichier ne soit pas à jour.

Rendez vous simplement dans le répertoire :file:`plugins/thunderbird` et exécutez la commande :command:`./build.sh`.
Ceci devrait créer un fichier :file:`openplm.xpi`. 


Installation
------------

#. Démarrez Thunderbird
#. Allez dans le gestionnaire d'add-ons : menu :menuselection:`Outils --> Add-ons`.
   Une fenêtre de dialogue devrait apparaître :

   .. image:: images/pl_th_em.png
        :scale: 90%

#. Cliquez sur le bouton :guilabel:`Install...` et sélectionnez le fichier :file:`openplm.oxt`.
   Une fenêtre de dialogue devrait vous demander confirmation :

   .. image:: images/pl_th_em2.png
        :scale: 90%

#. Cliquez sur :guilabel:`Installer Maintenant`.
#. Redémarrez Thunderbird
#. Le plugin est désormais installé. Un nouveau sous menu nommé :guilabel:`OpenPLM` devrait être disponible dans le menu :guilabel:`Fichier`.

Utilisation
===========

Configuration
-------------

Avant toute chose, il faut indiquer l'emplacement du serveur :

    #. Ouvrez la fenêtre (menu :menuselection:`Tools -- Add-ons`).
    #. Sélectionnez l'add-on OpenPLM :

        .. image:: images/pl_th_em3.png
            :scale: 90%
    
    #. Cliquez sur le bouton :guilabel:`Préférences`. La fenêtre de dialogue suivante devrait apparaître :
        
        .. image:: images/pl_th_conf.png

    #. Renseignez l'emplacement du serveur puis refermez la fenêtre.    


Connexion
---------

Avant de pouvoir faire un check-in sur un fichier, il faudrait vous connecter. Ouvrez la fenêtre
de configuration (menu :menuselection:`Fichier --> OpenPLM --> Connexion`).

    .. image:: images/pl_th_login.png

Renseignez vos nom d'utilisateur et mot de passe avant de cliquer sur :guilabel:`Ok`.

Check-in d'un email
-------------------

Vous pouvez sauvegarder un email sur le serveur : 
    
    #. Sélectionnez un ou plusieurs emails
    #. Cliquez sur :menuselection:`Fichier --> OpenPLM --> Check-in du mail courant`.
       La fenêtre de dialogue suivante doit apparaître :

       .. image:: images/pl_th_ci.png

    #. Renseignez le formulaire de recherche avant de cliquer sur le bouton :guilabel:`Recherche`.
    #. Sélectionnez votre document et cliquer sur :guilabel:`Ok`
    #. Votre mail a été sauvegardé.


Créer un nouveau document
-------------------------

Il est possible de créer un nouveau document depuis un email :

    #. Sélectionnez un ou plusieurs emails
    #. Cliquez sur :menuselection:`Fichier --> OpenPLM --> Créer un nouveau document`.
       La fenêtre de dialogue suivante devrait apparaitre :

        .. image:: images/pl_th_create.png

    #. Remplissez le formulaire
    #. Cliquez sur :guilabel:`Ok` pour valider la création.
    #. Votre document a été créé.

