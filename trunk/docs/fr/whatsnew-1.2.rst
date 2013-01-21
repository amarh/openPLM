.. _whatsnew-1.2:

.. Images come later, once you are sure you would not have to update them ;)

=========================
Nouveautés d'OpenPLM 1.2
=========================


Introduction
===============

OpenPLM est une solution PLM orientée produit.  Une solution PLM (Product
Lifecycle Management, gestion de cycle de vie produit) unifie toutes les
activités de la société dans un ECM qui structure des données autour du produit.
OpenPLM dispose d'une interface full-web et conviviale. 
OpenPLM est un logiciel libre et open source.
Cela signifie que tout le monde peut librement l'utiliser, le modifier et le redistribuer.

Depuis la précédente version, sortie il y a cinq mois, beaucoup de modifications
ont été apportées dans OpenPLM 1.2.
Voici quelques points forts notables :

    * Le téléchargement et la création de documents est facilitée
    * Plusieurs améliorations apportées à la fonctionnalité « naviguer »
    * La gestion des *Engineering Change Requests*
    * Les liens *alternate* entre parts

.. image:: /whatsnew/1.2/intro.png
    :align: center
    :width: 64%

Nouveautés pour les utilisateurs
=================================

Naviguer
--------

Nouveau style
++++++++++++++++

Le style des nœuds a été retravaillé. Plus d'informations sur les documents
et parts sont affichées. Il est ainsi plus facile de déterminer si 
un nœud est une part ou un document.

.. list-table::

    * - .. figure:: /whatsnew/1.2/navigate_2.png
            :align: center
            
            Document

      - .. figure:: /whatsnew/1.2/navigate_3.png
            :align: center

            Part

Gestions des révisions
++++++++++++++++++++++

Deux liens vers les révisions suivantes et précédentes sont affichées :
    
.. figure:: /whatsnew/1.2/navigate_1.png


Basculement vers le mode d'édition
+++++++++++++++++++++++++++++++++++++++++

Désormais, vous pouvez directement étudier l'un des éléments affichés dans
le navigateur :


.. figure:: /whatsnew/1.2/navigate_4.png


Autres améliorations
+++++++++++++++++++++++++++++++++++

    * Le niveau de zoom est conservé lors du basculement d'un objet vers un autre

    * Le glisser-déposer pour déplacer le graphe a été amélioré

    * Vous pouvez naviguer à une date précédente


Téléchargement et création
----------------------------

Il est désormais possible de télécharger un ou plusieurs fichiers
puis de créer un document en quelques clics.


.. raw:: html

    <div>
        <br/>
        <video width="700" height="375" controls="controls">
          <source src="_downloads/upload.webm" type="video/webm" />
          Upload of a file
        </video>
    </div>

:download:`Download the video </whatsnew/1.2/upload.webm>`


Cycle de vie
---------------

Plusieurs signataires peuvent être assignés pour valider ou refuser
une part ou un document.
Le propriétaire peut être l'un des premiers signataires, et ainsi il peut
facilement signaler quand son travail est prêt.


.. figure:: /whatsnew/1.2/lifecycle_1.png

Nomenclature
------------

Comparaison
++++++++++++

Les nomenclatures sont comparables à deux dates différentes.


Documents attachés
+++++++++++++++++++


On peut éditer une nomenclature multi-niveaux en incluant les tous les documents
attachés :

.. figure:: /whatsnew/1.2/bom_1.png


Liens *alternates*
++++++++++++++++++


Il est possible de créer un ensemble de parts *alternate*.
Chaque usage d'une part peut être remplacé par l'une de ses alternates.
L'édition d'une nomenclature peut inclure les parts alternates.

OpenPLM prévient toutes situations incohérentes (telles qu'une part parent
à l'une de ses alternate) lors de la création des nomenclatures.


Fichiers
--------

Vous pouvez accéder aux versions précédentes de chaque fichier:

.. figure:: /whatsnew/1.2/files_1.png

Gestion des changements
---------------------------

Si votre administrateur les active, vous pourrez créer des
ECR (Engineering Change Requests) pour demander un changement
concernant plusieurs parts et documents.


Badges
------

Si votre administrateur les active, vous pourrez gagner des badges
en utilisant OpenPLM ☺.

Amélioations diverses
----------------------------

    * Lors de la création d'une part ou d'un document, le champ
      groupe est pré-rempli

    * Il est possible de choisir le groupe d'une nouvelle révision

    * Pour chaque objets, les contenus similaires sont affichés sur leur
      page « attributs »


What's new for administrators
===============================

Documentation
-------------

    * A new how-to, :ref:`admin-upgrade`, is available. 

New settings
------------

    * :const:`~settings.EMAIL_FAIL_SILENTLY`
    * :const:`~settings.KEEP_ALL_FILES`

Minor file revisions
--------------------

A notable change of this version is the ability of openPLM to keep
old minor revision of all files (all check-ins).
You can configure which files are kept, see :mod:`plmapp.files.deletable`.


New application: badges
-----------------------

A new application, :ref:`badges <badges-admin>` can be installed.
It adds badges ala StackOverflow.


New application: calendrier
-----------------------------

A new application, :ref:`calendrier <calendrier-admin>` can be installed.
It adds a calendar view of the timeline and histories pages and an ICal feed
for each object.


New application: ecr: change management
---------------------------------------

A new application, :ref:`ecr <calendrier-admin>` can be installed.
It adds Engineering Change Request objects.


Optional lifecycles
--------------------

New lifecycles are available, you can load them by running the command
``./manage.py loaddata extra_lifecycles``


Previous versions
=================

.. toctree::
    :maxdepth: 1
    :glob:

    whatsnew/*
