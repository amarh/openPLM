===================
Plugin pour FreeCAD
===================


Installation
============

Récupération des sources
------------------------

Ce plugin est disponible sur le svn, dans le répertoire :file:`trunk/plugins/freecad/`.

Dépendances
-----------

Il vous faudra bien entendu FreeCAD. Ce plugin a été testé avec les versions
0.10 et 0.11.
Il vous faut aussi un environnement python (version 2.6) incluant la
bibliothèque Poster (disponible `ici <http://atlee.ca/software/poster/#download>`_).

Installation
------------

Accéder au répertoire :file:`plugins/freecad` et exécuter la commande  :command:`./install.sh`.

Démarrer FreeCAD, si le plugin s'est installé correctement, un nouvel atelier nommé *OpenPLM* est disponible.

.. warning::
    Cette procédure installera le plugin uniquement pour l'utilisateur
    courant.

Utilisation
===========

Configuration
-------------

Avant tout, il faut spécifier l'emplacement du serveur : 

    #. Activer l'atelier *OpenPLM*.
    #. Ouvrir la fenêtre de configuration (menu :menuselection:`OpenPLM --> Configurer`).
       La fenêtre suivante doit apparaitre :

       .. image:: images/pl_fc_conf.png

    #. Renseigner l'emplacement du serveur.
    #. Cliquer sur :guilabel:`Ok`.

Connexion
---------

Avant d'effectuer le check-out d'un fichier, il faut vous connecter :

    #. Activer l'atelier *OpenPLM*.
    #. Ouvrir la fenêtre de configuration (menu :menuselection:`OpenPLM --> Configurer`).
       La fenêtre suivante doit apparaitre :

       .. image:: images/pl_fc_login.png

    #. Renseigner vos nom d'utilisateur et mot de passe.
    #. Cliquer sur :guilabel:`Ok`.

Check-out d'un fichier
----------------------

Pour effectuer un check-out, activer l'atelier *OpenPLM*. Ensuite, cliquer sur :menuselection:`OpenPLM --> Check-out`.
La fenêtre suivante doit apparaitre : 

    .. image:: images/pl_fc_co1.png

Renseigner votre requête avant de cliquer sur le bouton :guilabel:`Recherche`; ensuite, déplier la partie intitulée :guilabel:`Résultats`. 
Vous pouvez ensuite parcourir les documents pour voir les fichiers disponibles 

    .. image:: images/pl_fc_co2.png

Sélectionné ensuite votre fichier et cliquer sur le bouton :guilabel:`Check-out`.
Votre fichier devrai maintenant être ouvert, ce qui vous permet de travailler
comme habituellement.

Une fois votre travail accompli, vous pouvez effectuer une révision du document, ou un check-in.

Télécharger un fichier
----------------------

Si vous voulez juste consulter un fichier sans le modifier, cliquer sur :menuselection:`OpenPLM --> Télécharger depuis OpenPLM`. Renseigner votre requête, sélectionner votre fichier puis cliquer sur le bouton :guilabel:`Télécharger`.

Check-in d'un fichier
---------------------

Pour sauvegarder votre travail sur le serveur, cliquer sur :menuselection:`OpenPLM --> Check-in`.
La fenêtre de dialogue suivante doit apparaitre :

    .. image:: images/pl_fc_ci.png

Cocher la case :guilabel:`Déverrouiller?` si vous souhaitez déverrouiller
votre fichier, ce qui fermera aussi le fichier dans FreeCAD.

Cliquer sur le bouton :guilabel:`Check-in`.

Nouvelle révision d'un document
-------------------------------

Pour créer une nouvelle révision du document lié à votre fichier, cliquer sur :menuselection:`OpenPLM --> Révision`. 
La fenêtre de dialogue suivante doit apparaître :

    .. image:: images/pl_fc_rev.png

Cocher la case :guilabel:`Déverrouiller?` si vous souhaiter déverrouiller votre fichier, ce qui fermer aussi le fichier dans FreeCAD.

.. note::

    L'ancienne révision du fichier sera automatiquement déverrouillée.

Cliquer sur le bouton :guilabel:`Revision`.


Créer un nouveau document
-------------------------

Vous pouvez créer un nouveau document depuis un fichier qui n'a été ni
check-out, ni téléchargé. Pour cela, cliquer sur :menuselection:`OpenPLM --> Create a document`.
La fenêtre de dialogue suivante doit apparaitre :

    .. image:: images/pl_fc_create.png

Remplir le formulaire sans oublier d'indiquer le nom du fichier et son
extension. Cliquer sur :guilabel:`Créer` pour valider la création.

Comme dans le cas d'une révision ou d'un check-in, cochez la case :guilabel:`Déverrouiller?` si vous souhaitez déverrouiller votre fichier, ce qui le fermera dans FreeCAD.


Oublier un fichier
------------------

Tout les fichiers téléchargé/checked-out sont ouvert lorsque vous démarrez
FreeCAD; il est possible d'oublier un fichier en cliquant sur :menuselection:`OpenPLM --> Oublier le fichier courant`.

Attacher un document à une part
-------------------------------

Il est possible de lié le document courant à une part en cliquant sur
:menuselection:`OpenPLM --> Attacher à une part`. Une fenêtre de dialogue
permettant de choisir la part devrait apparaître. En sélectionner une avant de cliquer sur le bouton :guilabel:`Attacher`.

