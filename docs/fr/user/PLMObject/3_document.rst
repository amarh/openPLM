==================================================
Fonctions spécifiques à l'objet PLM : **DOCUMENT**
==================================================


PARTS
=====
Affiche les Parts liées au Document courant.

Si vous avez les autorisations nécessaires, vous pouvez : 
  * **Ajouter** une nouvelle Part,

  * **Supprimer** une Part.


FICHIERS
========
Affiche les fichiers uploadés dans le Document courant.

Si vous avez les autorisations nécessaires, vous pouvez :
    * télécharger des fichiers
    
    * ajouter/uploader des fichiers
    
    * faire des check-out (télécharger et verrouiller un fichier)
    
    * faire des check-in (uploader et déverrouiller un fichier)


3D DOCUMENT
===========
3DDocument est un type de document possédant toutes les fonctionnalités de la
sous-classe Document de **PLMObject**. Elle est utilisée pour décrire la géométrie
d'un objet. Cette géométrie est généralement définie dans des fichiers STEPs
(extensions *.step* ou *.stp*).

Si le document est un Document 3D et contient un ou des fichiers STEPs, une représentation 3D est générée en
utilisant ce(s) fichier(s).

Exemple de représentation 3D : 

.. image:: ../images/3Dview.png
   :width: 100%
