===============================================
pdfgen -- création de PDF
===============================================

Cette application ajoute les fonctionnalités suivantes :

    * export de la page "attributs" au format PDF
    * export de la page "nomenclature" au format PDF
    * fusion de plusieurs PDF en un fichier PDF.

Dépendances
==============

Cette application dépend de `xhtml2pdf <http://www.xhtml2pdf.com/>`_ et
`pyPDF <http://pybrary.net/pyPdf/>`_. 


settings.py
==============

L'application *pdfgen* doit être activée dans le fichier settings pour être
utilisée. Pour cela, rajouter ``'openPLM.apps.pdfgen'``  à la liste des applications installées (:const:`INSTALLED_APPS`).

Test
=========

Pour tester cette application, créez une part. Ensuite rendez vous 
sur la page "attributs" et cliquez sur le bouton "Téléchargez au format PDF". 
Vous devriez télécharger un PDF similaire à la page "attributs".


