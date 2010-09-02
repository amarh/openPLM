.. module:: http_api

================================
:mod:`http_api` --- HTTP-API
================================

This document describes how to communicate with an OpenPLM server to build a
plugin.


How to make a query
===================

You just have to make a POST or GET request to the server. All valid urls
are described above.

.. warning::

    You must set the user-agent to 'openplm', this is to prevent a CSRF attack.
    If an user click on a link related to the api, he will receive a 403
    forbidden response. Moreover, a XMLHttpRequest object can not set the
    user agent if the script was launched from another domain.


Returned value
==============

Results are returned in a JSON format. Each result contains at least two fields:

    api_version
        the api version (current : **1.0**)

    result
        - ``"ok"`` if no error occurred (i.e. the query was valid and succeed)
        - ``"error"`` if an error occurred

For example, a minimal result would be:

.. code-block:: javascript
    
    {"result": "ok", "api_version": "1.0"}

If an error occurred, an extra field is add:
    
    error
        a short description of the error

For example, a result could be:

.. code-block:: javascript

    {"result": "error", "api_version": "1.0", "error": "Oups an error occured"}


Authentication
===============

Several queries require an authenticated user. 

The authentication is based on Django module ``auth``, so you need to make
query with a cookies support.

To authenticated, see :func:`login`.


.. _http-api-object:

Object fields
=============

Some queries return a field which describes an object.

The fields are:

    ============ ===============================
       Field        Description
    ============ =============================== 
     id           id of the object
     type         type of the object
     reference    reference of the object
     revision     revision of the object
     name         name of the object
    ============ =============================== 

.. _http-api-fields:

Query fields
============

Some queries returns a description of an object field, this description contains
the following fields:

    =============== =============================================================
       Field         Description
    =============== =============================================================
     name            name of the field.
                     Examples: ``"type"``, ``"reference"``, ``"wheels"``
     label           verbose name more comprehensible for an user.
                     Example: ``"Number of wheels"``
     type            type of the field, the avalaible types are described above
     initial         initial (default) value for the field, may be `None`.
     others fields   see above
    =============== =============================================================

.. _http-api-types:

Available types
+++++++++++++++++

The available types are:

    ================ ================================================
        Type          Description
    ================ ================================================
     ``"int"``        an integer (positive or negative)
     ``"float"``      a float (positive or negative)
     ``"decimal"``    a number with a restrictive format
     ``"boolean"``    a boolean (`True` or `False`)
     ``"text"``       a string
     ``"choice"``     a type to choose among several values
    ================ ================================================

If the type is ``"choice"``, another field, called ``"choices"`` is given. It
contains a list of tuple (*short_value*, *long_value*) where *short_value* is
the value for the server and *long_value* is the value for the user.

Optional fields
+++++++++++++++++

Some other fields may be given:

    ============= ================== ==========================================
     Field         Associated types   Description
    ============= ================== ==========================================
     min_value     ``"int"``,         minimal value accepted by the field
                   ``"float"``,
                   ``"decimale``
     max_value     ``"int"``,         maximal value accepted by the field
                   ``"float"``,
                   ``"decimale``
     min_length    ``"text"``,        minimal length of the field 
     max_length    ``"text"``,        maximal length of the field
    ============= ================== ==========================================

.. _http-api-file:

File fields
===========

Some queries return information about a file.

The fields are:
    
    =============== =============================================================
       Field         Description
    =============== =============================================================
     id              id of the file
     filename        name of the file (with its extension)
     size            size of the file in bytes
    =============== =============================================================


List of available queries
=========================


General queries
+++++++++++++++

.. py:function:: login

    Query used to authenticate an user.

    :url: :samp:`{server}/api/login/`
    :type: POST
    :login required: no
    :implemented by: :func:`plmapp.api.api_login`

    :param string username: the username of the user
    :param string password: the password of the user
    
    :returned fields:
        username
            the username passed in the POST query

        first_name
            the user's first name

        last_name
            the user's last name

    :fail if:
        user does not exist or user is inactive

.. py:function:: testlogin

    Query used to test if an user is authenticated.
    
    This query does not take any parameters and does not return any specific
    fields. If the user is authenticated, *result* would be set to ``"ok"``.

    :url: :samp:`{server}/api/testlogin/`
    :type: GET
    :login required: no
    :implemented by: :func:`plmapp.api.test_login`

.. py:function:: types

    Query used to get all the subtypes of :class:`.PLMObject` managed by the server.

    :url: :samp:`{server}/api/types/`
    :type: GET
    :login required: yes
    :implemented by: :func:`plmapp.api.get_all_types`

    :returned fields:
        types
            list of all types (string) sorted alphabetically
            (without ``"plmobject"``)

    .. seealso:: :func:`parts` and :func:`docs`

.. py:function:: parts

    Query used to get all the types of :class:`.Part` managed by the server.

    :url: :samp:`{server}/api/parts/`
    :type: GET
    :login required: yes
    :implemented by: :func:`plmapp.api.get_all_parts`

    :returned fields:
        types
            list of all types (string) sorted alphabetically

.. py:function:: docs

    Query used to get all the types of :class:`.Document` managed by the server.

    :url: :samp:`{server}/api/docs/` or :samp:`{server}/api/documents/`
    :type: GET
    :login required: yes
    :implemented by: :func:`plmapp.api.get_all_docs`

    :returned fields:
        types
            list of all types (string) sorted alphabetically

.. py:function:: search
    
    Query used to perform a search on the objects stored on the server
    
    Possible values for *editable_only* are:

        * *true* (the default) to return only editable objects
        * *false* to return all objects

    Possible values for *with_file_only* are:

        * *true* (the default) to return only documents with at least one file
        * *false* to return all documents

    :url: :samp:`{server}/api/search/[{editable_only}/[{with_file_only}/]]`
    :type: GET
    :login required: yes
    :implemented by: :func:`plmapp.api.search`
    

    :get params:
        type
            (required) a valid type (see :func:`types` to get a list of types)
        others params
            see :func:`search_fields`

    :returned fields:
        objects
            list of all objects matching the query, see :ref:`http-api-object`.

.. py:function:: create

    Query used to create an object 
    
    :url: :samp:`{server}/api/create/`
    :type: POST
    :login required: yes
    :implemented by: :func:`plmapp.api.create`
    :post params:
        type
            (required) a valid type (see :func:`types` to get a list of types)
        others params
            see :func:`creation_fields`

    :returned fields:
        object
           the object which has been created, see :ref:`http-api-object`.

.. py:function:: search_fields

    Query used to get available fields to perform a search 
    
    :url: :samp:`{server}/api/search_fields/{typename}/`
    :type: GET
    :login required: yes
    :implemented by: :func:`plmapp.api.get_search_fields`
    :returned fields:
        fields
           the list of fields available to perform a search on the objects
           of type *typename*, see :ref:`http-api-fields`.

.. py:function:: creation_fields

    Query used to fields need to create an object 
    
    :url: :samp:`{server}/api/creation_fields/{typename}/`
    :type: GET
    :login required: yes
    :implemented by: :func:`plmapp.api.get_creation_fields`
    :returned fields:
        fields
           the list of fields need to create an object of type *typename*, see
           :ref:`http-api-fields`.


Document queries
++++++++++++++++

In the following queries, *doc_id* is a the id (an integer) of a
:class:`.Document`

.. py:function:: files

    Returns the list of files associated to the document.
    If *all/* is given, all files are returned, otherwise, only unlocked files
    are returned.
    
    :url: :samp:`{server}/api/{doc_id}/files/[all/]`
    :type: GET
    :login required: yes
    :implemented by: :func:`plmapp.api.get_files`
    :returned fields:
        files
           the list of files of the document, see :ref:`http-api-file`.

.. py:function:: revise

    Make a new revision of the document

    :url: :samp:`{server}/api/{doc_id}/revise/`
    :type: POST
    :login required: yes
    :implemented by: :func:`plmapp.api.revise`
    :post params:
        revision
            new revision of the document
    :returned fields:
        doc
           the new document, see :ref:`http-api-object` 
        files
           the list of files of the new document, see :ref:`http-api-file`.

.. py:function:: next_revision

    Returns a possible new revision for the document.

    :url: :samp:`{server}/api/{doc_id}/next_revision/`
    :type: GET
    :login required: yes
    :implemented by: :func:`plmapp.api.next_revision`
    :returned fields:
        revision
            the new revision (may be an empty string)

.. py:function:: is_revisable

    Returns True if the document can be revised.

    :url: :samp:`{server}/api/{doc_id}/is_revisable/`
    :type: GET
    :login required: yes
    :implemented by: :func:`plmapp.api.is_revisable`
    :returned fields:
        revisable
            boolean, True if the document can be revised.

.. py:function:: attach_to_part

    Links the document with the part identified by *part_id*

    :url: :samp:`{server}/api/{doc_id}/attach_to_part/{part_id}/`
    :type: GET
    :login required: yes
    :implemented by: :func:`plmapp.api.attach_to_part`
    :returned fields: None

.. py:function:: add_file

    Adds a file to the document, the request must be have the attribute
    ``enctype="multipart/form-data"``.

    :url: :samp:`{server}/api/{doc_id}/add_file/`
    :type: POST
    :login required: yes
    :implemented by: :func:`plmapp.api.add_file`
    :post param: filename
    :returned fields:
        doc_file
            the file that has been had, see :ref:`http-api-file`.


Document file queries
-----------------------

In the following queries, *df_id* is the id (an integer) of a
:class:`.DocumentFile`.

.. py:function:: is_locked

    Returns True if the file is locked.

    :url: :samp:`{server}/api/{doc_id}/is_locked/{df_id}/`
    :type: GET
    :login required: yes
    :implemented by: :func:`plmapp.api.is_locked`
    :returned fields:
        locked
            boolean, True if the file is locked.

.. py:function:: lock

    Locks the file

    :url: :samp:`{server}/api/{doc_id}/lock/{df_id}/` or 
          :samp:`{server}/api/{doc_id}/checkout/{df_id}/`
    :type: GET
    :login required: yes
    :implemented by: :func:`plmapp.api.check_out`
    :returned fields: None

.. py:function:: unlock

    Unlocks the file

    :url: :samp:`{server}/api/{doc_id}/unlock/{df_id}/` 
    :type: GET
    :login required: yes
    :implemented by: :func:`plmapp.api.unlock`
    :returned fields: None

.. py:function:: checkin

    Updates (checks-in) the file, the request must be have the attribute
    ``enctype="multipart/form-data"``.

    :url: :samp:`{server}/api/{doc_id}/checkin/{df_id}/` 
    :type: POST
    :login required: yes
    :implemented by: :func:`plmapp.api.check_in`
    :post param: filename
    :returned fields: None

.. py:function:: add_thumbnail

    Adds a thumbnail to the file, the request must be have the attribute
    ``enctype="multipart/form-data"``.

    :url: :samp:`{server}/api/{doc_id}/add_thumbnail/{df_id}/` 
    :type: POST
    :login required: yes
    :implemented by: :func:`plmapp.api.add_thumbnail`
    :post param: filename
    :returned fields: None
