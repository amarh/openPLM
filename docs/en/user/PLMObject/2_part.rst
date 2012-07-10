========================================================
Functions specific to PLM object : **PART**
========================================================


BOM-CHILD
========================================================
Displays BOM of the current part i.e. Parts which are under or which are in.

You can filter *1 level* (only sons) or *all levels* (grandsons, great-gransons, ...) or *last level* . You can specify a date in order to get the BOM at that time. You can also specify a state.

If you have necessary rights, you can :
  * **Add** a new Part/children specifying its type, reference, revision, its quantity (1, 2, 0.5 kg, 2.5 m, ...) and its ordering number (which define where the children is shown in the BOM).

  * **Edit** the first level and modify quantity, ordering number or remove the Part out of the BOM.

If a document with a STEP file is linked to the current part and the part has no children, you can be asked if you want to build the BOM analysing the STEP file.


PARENTS
========================================================
Displays Parts which are upon the current part.

You can filter *1 level* (only parents) or *all levels* (grandparents, great-grandparents, ...) or *last level*. You can also specify a date in order to see the assemblies where we could find the current part at that time.


DOC-CAD
========================================================
Displays related Documents of the current part.

If you have necessary rights, you can :

* **Add** a new Document

* **Remove** a Document

* **Download** one or all files

