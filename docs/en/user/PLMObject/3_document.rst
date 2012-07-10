========================================================
Functions specific to PLM object : **DOCUMENT**
========================================================


PARTS
========================================================
Displays related Parts of the current document.

If you have necessary rights, you can :
  * **Add** a new Part,

  * **Remove** a Part. 


FILES
========================================================
Displays files uploaded in the current document.

If you have necessary rights, you can :
    * add/upload files
    * simply download them
    * check-out files (download and lock file)
    * check-in files (upload and unlock them).


3D DOCUMENT
========================================================
3DDocument is a type of document with all the functions related to the sub-class of **PLMObject** , Document. It's used to describe the solid geometry of an object. This geometry is usually defined in STEP files ( extension *.step* or *.stp*)  .

If the document is a 3D document and contains STEP files,  a 3D view is generated using these files.

Here is an example of 3D view :

.. image:: ../images/3Dview.png
   :width: 100%
