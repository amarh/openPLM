================================
:mod:`http_api` --- HTTP-API
================================

This document describes how to communicate with an OpenPLM server to build a
plugin.


How to make a query
===================

You just have to make a POST or GET request to the server. All valid urls
are described above.


Returned value
==============

Results are returned in a JSON format. Each result contains at least two fields:

    api_version
        the api version (current : **1.0**)

    result
        - `ok` if no error occurred (i.e. the query was valid and succeed)
        - `error` if an error occurred

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


List of available queries
=========================

.. py:function:: login

    Query used to authenticate an user.

    :url: :samp:`{server}/api/login/`
    :type: POST

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
    fields. If the user is authenticated, *result* would be set to `ok`

    :url: :samp:`{server}/api/testlogin/`
    :type: GET



