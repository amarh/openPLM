=========
Create
=========

This document describes how to create **Parts**, **Documents**.
It describes how to add new **Users** too.

.. raw:: html
   :file: html/create.html
   
Other creation tools
======================

Sponsor a new user
*******************
The sponsor form is also reachable in the delegation tab


Import from a csv file
***********************
PLM object (parts and document) and user can be created with a csv file. This file
must contains headers related to the target (object or user).
Mostly these headers are the required field in the related
object or user creation form.

Example of csv file's structure :
 1 - PLM object
    .. csv-table::
        :header-rows: 1
        :file: csv_import/PLMObject.csv
                
    Download the :download:`file <csv_import/PLMObject.csv>`.

  
 2 - BOM      
    .. csv-table::
        :header-rows: 1
        :file: csv_import/BOM.csv
        
    Download the :download:`file <csv_import/BOM.csv>`.


 3 - User        
    .. csv-table::
        :header-rows: 1
        :file: csv_import/User.csv
    
    
    The available values for language are :
        * "en" (english)
        * "fr" (french)
        * "es" (spanish)
        * "ja" (japanese)
        * "ru" (russian)
        * "zh_CN" (chinese)
        
    Download the :download:`file <csv_import/User.csv>`.
