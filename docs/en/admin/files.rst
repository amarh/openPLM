.. _files-admin:

===========
Files
===========

How OpenPLM manages files
=========================


All files bound to a document are stored in a single directory
(see :const:`~settings.DOCUMENTS_DIR`). This directory contains
a lot of subdirectories, one per seen extensions (in lower case).

Each file is stored in the directory related to its extension.
However, they are renamed into :samp:`{md5sum}-{rand}.{ext}` where:

    * `md5sum` is the md5 sum of the original filename
    * `rand` is a random part to avoid to overwrite an existing file
    * `ext` is the original extension

This renaming makes it possible to store several files with the
same name and several revision of the same file.

The model :class:`.DocumentFile` stores in the database the
data related to a file (its document, path, etc.).


Minor revisions
++++++++++++++++

.. versionadded:: 1.2

After a check-in or a deletion, OpenPLM creates a new DocumentFile
in the database. This DocumentFile is marked as deprecated and
its file may be kept or deleted according to the configuration
of OpenPLM.

If :const:`~settings.KEEP_ALL_FILES` is True (default is False),
OpenPLM will never delete a file. This ensures a maximum traceability
but may require a lot of disk place.

How OpenPLM decides to keep or delete a file is explained 
:mod:`here <plmapp.files.deletable>`. Currently, the only way to modify
the default behaviour is to edit this file.


Thumbnails
+++++++++++++

Thumbnails are stored in the :const:`~settings.THUMBNAILS_DIR` directory.
All thumbnails are PNG files and they are named :samp:`df_id.png` where
`df_id` is the id of the related DocumentFile.

When a file is deleted, its thumbnail is also deleted.

WebDAV
======

Enabling :ref:`WebDAV access <webdav-admin>` allows the company to browse
all documents and their files.

