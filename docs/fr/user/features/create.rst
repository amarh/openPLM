=====
Créer
=====

Ce document décrit la création de parts et de documents.

.. raw:: html
   :file: html/create.html
   
Autres outils de création
=========================

Parrainer un nouvel utilisateur
*********************************
On peut aussi accéder au formulaire de parrainage depuis l'onglet délégation


Import depuis un fichier csv
****************************
On peut créer des utilisateurs et des objets PLMObject à partir d'un fichier
csv. Ce fichier doit comporter les en-têtes relatifs à la cible (objet ou
utilisateur).

En majorité, ces en-têtes correspondent aux champs requis que l'on peut
retrouver dans le formulaire de création de l'objet ou de l'utilisateur.

Exemple de la structure d'un fichier csv : 
 1 - PLMObject
    .. csv-table::
        :header-rows: 1
        :file: csv_import/PLMObject.csv
        
    Télécharger le fichier :download:`here <csv_import/PLMObject.csv>`.

  
 2 - Nomenclature      
    .. csv-table::
        :header-rows: 1
        :file: csv_import/BOM.csv
        
    Télécharger le fichier :download:`here <csv_import/BOM.csv>`.


 3 - Utilisateur        
    .. csv-table::
        :header-rows: 1
        :file: csv_import/User.csv
        
    Télécharger le fichier :download:`here <csv_import/User.csv>`.
