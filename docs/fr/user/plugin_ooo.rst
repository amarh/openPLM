==========================
Plugin pour OpenOffice.org
==========================


Compilation et Installation
===========================

Récupération des sources
------------------------

Ce plugin est disponible sur le svn dans le répertoire :file:`trunk/plugins/openoffice`.

Dépendances
-----------

Vous avez bien entendu besoin d'OpenOffice.org. Ce plugin a été testé avec la
version 3.2. Vous avez aussi besoin d'un environnement python (version 2.6)
avec la bibliothèque Poster (disponible `ici <http://atlee.ca/software/poster/#download>`_).

Compilation
-----------

.. note::
    Il est possible d'ignorer cette étape en téléchargeant directement le
    fichier :download:`fichier (Windows) <download/openplm-win.oxt>`
    ou :download:`fichier (Autre) <download/openplm.oxt>`.
    Veuillez noter que ce fichier n'est pas forcément à jour.

Il suffit de créer une archive zip contenant 3 fichiers, l'archive aura
l'extension ``oxt`` : 

    - Si vous disposez d'une installation de poster valide :

        ``zip openplm.oxt Addons.xcu META-INF/manifest.xml openplm.py`` 
    
    - sinon (ce qui devrait fonctionner sous Windows par exemple) :
        
        ``zip openplm.oxt Addons.xcu META-INF/manifest.xml openplm.py pythonpath/*/*`` 


Ceci créera un fichier intitulé :file:`openplm.oxt` que vous allez pouvoir
installer.

Installation
------------

Deux méthodes sont disponibles pour installer le plugin
    - via la ligne de commande
    - à l'aide de l'outil inclus dans OpenOffice.org

Via la ligne de commande
~~~~~~~~~~~~~~~~~~~~~~~~

Il vous suffit d'installer le plugin à l'aide de la commande suivante : 

``unopkg add -f -v openplm.oxt``

.. warning::
    Cette commande installe le plugin pour l'utilisateur courant uniquement,
    pour une installation globale, consulter la documentation de unopkg.

A l'aide du gestionnaire d'extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Démarrer OpenOffice
#. Démarrer le gestionnaire d'extension : menu :menuselection:`Tools --> Extension Manager...`.
   La fenêtre de dialogue suivante devrait apparaître :

   .. image:: images/pl_ooo_em.png

#. Cliquer sur le bouton :guilabel:`Add...` et sélectionner le fichier :file:`openplm.oxt`
#. L'installation du plugin est terminée. Refermer la fenêtre de dialogue et redémarrer OpenOffice. Si l'installation s'est déroulée correctement, un nouveau menu intitulé :guilabel:`OpenPLM` doit apparaître.

Utilisation
===========

Configuration
-------------

Avant tout, il faut indiquer l'emplacement du serveur. Pour cela, ouvrer la
fenêtre de configuration (menu :menuselection:`OpenPLM --> Configure`).

    .. image:: images/pl_ooo_conf.png

Renseigner l'emplacement du serveur et cliquer sur :guilabel:`Configure`.

Connexion
---------

Avant d'effectuer un check-out de fichier, il faut vous connecter. Ouvrer la
fenêtre de configuration (menu :menuselection:`OpenPLM --> Login`).

    .. image:: images/pl_ooo_login.png

Renseigner vos nom d'utilisateur et mot de passe avant de cliquer sur :guilabel:`Login`.

Check-out d'un fichier
----------------------

Pour effectuer le check-out d'un fichier, cliquer sur :menuselection:`OpenPLM --> Check-out`.
La fenêtre de dialogue suivante devrait apparaître :

    .. image:: images/pl_ooo_co1.png

Renseigner votre requête puis cliquer sur le bouton :guilabel:`Recherche`, déroulé l'objet intitulé :guilabel:`Résultats`.
Vous devriez pouvoir parcourir les documents pour voir la liste des fichiers
disponibles : 

    .. image:: images/pl_ooo_co2.png

Il ne vous reste qu'à sélectionner votre fichier et cliquer sur le bouton :guilabel:`Check-out`.
Votre document devrait s'ouvrir et vous pouvez désormais travailler comme
habituellement.

Une fois votre travail terminé, il est possible de changer la révision du
document ou d'effectuer un check-in.

Téléchargement d'un fichier
---------------------------

Si vous souhaitez juste consulter un document sans le modifier, il vous suffit
de cliquer sur :menuselection:`OpenPLM --> Download from OpenPLM`. Effectuer votre requête, sélectionner votre fichier et cliquer sur le bouton :guilabel:`Download`.

Check-in d'un fichier
---------------------


Pour sauvegarder votre travail sur le serveur, cliquer sur :menuselection:`OpenPLM --> Check-in`.
La fenêtre de dialogue suivante devrait apparaître : 

    .. image:: images/pl_ooo_ci.png

Cocher la case :guilabel:`Unlock?` si vous souhaitez déverrouiller votre
fichier, ce qui le fermera aussi dans OpenOffiche.

Cliquer sur le bouton :guilabel:`Check-in`.

Révision d'un document
----------------------

Pour créer une nouvelle révision d'un document lié à votre fichier, cliquer
sur :menuselection:`OpenPLM --> Revise`.

    .. image:: images/pl_ooo_rev.png

Si vous souhaitez déverrouiller votre fichier, cocher la case :guilabel:`Unlock?`. Cela fermera aussi votre document dans OpenOffice.

.. note::

    L'ancienne révision du fichier sera automatiquement déverrouillée.

Cliquer sur le bouton :guilabel:`Revise`.


Création d'un nouveau document
------------------------------

Il est possible de créer un nouveau document à partir d'un fichier qui n'a été
ni check-out, ni téléchargé. Pour cela, cliquer sur :menuselection:`OpenPLM --> Create a document`.
La fenêtre de dialogue suivante devrait apparaître :

    .. image:: images/pl_ooo_create.png

Remplir le formulaire, sans oublier d'indiquer le nom du fichier et son
extension, puis cliquer sur :guilabel:`Create` pour valider la création.

Comme pour une révision ou un check-in, cocher la case :guilabel:`Unlock?` si vous souhaitez déverrouiller votre fichier, ce qui le fermera dans OpenOffice.


Oublier un fichier
------------------

Tout les fichiers checked-out/téléchargés sont ouverts quand vous démarrez
OpenOffice. Il est possible d'oublier un fichier en cliquant sur :menuselection:`OpenPLM --> Forget current file`.

Attacher un document à une part
-------------------------------

On peut lier le document courant à une part en cliquant sur :menuselection:`OpenPLM --> Attach to part`.
Ceci ouvrira une fenêtre de dialogue permettant de choisir une part. En
sélectionner une avant de cliquer sur le bouton :guilabel:`Attach`.

