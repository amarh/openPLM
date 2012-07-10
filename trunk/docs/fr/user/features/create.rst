=====
Créer
=====

Ce document décrit la création de **Parts**, **Documents**.
Il décrit aussi l'ajout de nouveaux **Utilisateurs**.

.. raw:: html
   :file: html/create.html
   
Autres outils de création
=========================

Parrainer un nouvel utilisateur
*********************************
On peut aussi accéder au formulaire de parrainage depuis l'onglet délégation


Import depuis un fichier csv
****************************
On peut créer des utilisateurs et des objets PLMObject (parts et documents) à partir d'un fichier
csv. Ce fichier doit comporter les en-têtes relatifs à la cible (objet ou
utilisateur).

Ces en-têtes correspondent, principalement, aux champs requis que l'on peut
retrouver dans le formulaire de création de l'objet ou de l'utilisateur.

Exemple de la structure d'un fichier csv : 
 1 - Objet PLM (Part et Document)
    .. csv-table::
        :header-rows: 1
        :file: csv_import/PLMObject.csv
        
    Télécharger le  :download:`fichier <csv_import/PLMObject.csv>`.

  
 2 - Nomenclature      
    .. csv-table::
        :header-rows: 1
        :file: csv_import/BOM.csv
        
    Télécharger le  :download:`fichier <csv_import/BOM.csv>`.


 3 - Utilisateur        
    .. csv-table::
        :header-rows: 1
        :file: csv_import/User.csv
    
    Les différentes valeurs que peut prendre l'attribut *language* :
        * "en" (anglais)
        * "fr" (français)
        * "es" (espagnol)
        * "ja" (japonnais)
        * "ru" (russe)
        * "zh_CN" (chinois)
            
    Télécharger le  :download:`fichier <csv_import/User.csv>`.
