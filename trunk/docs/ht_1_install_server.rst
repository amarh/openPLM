===================================================
How to install openPLM server
===================================================

This document describes how to install an openPLM server.


Requirements
=============

This HowTo is based on :
 * Ubuntu 10.04 LTS server edition
 * Apache Server version: Apache/2.2.14 (Ubuntu)
 * PostgreSQL 8.4.4
 * Python 2.6.5
 * Django 1.1.1
 
    .. note ::
        Django framework can run with SQLite 3 and MySQL databases and with other web servers.
        We welcome all feedbacks about these combinations. For more information, you can visit :
        `Django website <http://www.djangoproject.com/>`_

Install necessary packages
==========================

    #. :command:`apt-get install swig build-essential pkg-config build-essential gettext`
    #. :command:`apt-get install apache2 libapache2-mod-wsgi`
    #. :command:`apt-get install python-setuptools python-dev python-imaging python-kjbuckets python-pypdf ipython`
    #. :command:`easy_install odfpy`
    #. :command:`apt-get install graphviz graphviz-dev`
    #. :command:`easy_install pygraphviz`
    #. :command:`apt-get install python-django`
    #. :command:`apt-get install postgresql python-psycopg2 pgadmin3`
   
Check applications are ok
===============================

    For Apache server : ::
    
        root@openplm-demo:~# service apache2 status
        
        Apache is running (pid 5315).
    
    For Python : ::
    
        root@openplm-demo:~# python
        
        Python 2.6.5 (r265:79063, Apr 16 2010, 13:09:56) 
        [GCC 4.4.3] on linux2
        Type "help", "copyright", "credits" or "license" for more information.
        >>> 
    
    
    .. note ::
    
        press :kbd:`Control-D` to exit Python shell
    
    For Django : ::
    
        root@openplm-demo:~# django-admin --version
        1.1.1

Get codes using Subversion
==========================

    * :command:`apt-get install subversion`
    
    * :command:`mkdir /var/django`
    
    All files used for a new django site will be stored in this directory.
    
    * :command:`cd /var/django`
    
    * :command:`svn co svn://openplm.org/openPLM`
    
    The directory ./openPLM is created and all codes are downloaded.
    
    * :command:`cd /var/django/openPLM`
    
    * :command:`svn info` ::
        
        Path: .
        URL: svn://openplm.org/openPLM
        Repository Root: svn://openplm.org/openPLM
        Repository UUID: 5b46f505-65de-4892-aab2-a53e26d394e5
        Revision: 195
        Node Kind: directory
        Schedule: normal
        Last Changed Author: pjoulaud
        Last Changed Rev: 195
        Last Changed Date: 2010-08-25 11:29:03 +0200 (mer., 25 août 2010)
        

Configure PostgreSQL
====================

    Check PostgreSQL is running:
    
    * :command:`ps aux|grep postgres` ::
    
        postgres 25961  0.0  0.9  50544  4968 ?    S    Aug26   0:14 /usr/lib/postgresql/8.4/bin/postgres -D /var/postgres
        postgres 25963  0.0  1.0  50664  5600 ?    Ss   Aug26   1:07 postgres: writer process                             
        postgres 25964  0.0  0.2  50544  1336 ?    Ss   Aug26   1:00 postgres: wal writer process                         
        postgres 25965  0.0  0.2  50808  1480 ?    Ss   Aug26   0:28 postgres: autovacuum launcher process                
        postgres 25966  0.0  0.2  14664  1224 ?    Ss   Aug26   0:24 postgres: stats collector process                    
        root     27338  0.0  0.1   3324   804 pts/3    R+   16:53   0:00 grep --color=auto postgres
    
    .. note ::
    
        If PostgreSQL is already installed, you can go to next topic directly.
    
    Set password for 'postgres' user (in this example we give 'MyPassword' but you can change it)
    
    * :command:`passwd postgres`
    * :command:`mkdir /var/postgres`
    
    All files necessary to run PostgreSQL will be stored in this directory.
    
    * :command:`chown postgres:postgres /var/postgres/`
    * :command:`find / -name initdb` ::
    
        /usr/lib/postgresql/8.4/bin/initdb
        
    * :command:`locale-gen fr_FR.UTF-8`
    * :command:`su postgres`
    * :command:`/usr/lib/postgresql/8.4/bin/initdb --encoding=UTF-8 --locale=fr_FR.UTF-8 --pgdata=/var/postgres/`
    * :command:`/usr/lib/postgresql/8.4/bin/postgres -D /var/postgres &`
    * :command:`psql` ::
    
            postgres=#create database openplm;
            postgres=#create role django with password 'MyPassword' login;
            \q
    
    * :command:`exit`

Finalize installation
=====================

    * :command:`cd /var/django/openPLM/trunk/openPLM/`
    * :command:`./manage.py syncdb`
    
    .. note::
        You have to create the superadmin user for Django (in this example, we give 'MyAdmin' but you can change it)
        and its password.
    
    .. warning::
        Edit the '/var/django/openPLM/trunk/openPLM/settings.py' and set correct password ('MyPassword')
        for DATABASE_PASSWORD
    
    Create directory where the uploaded files will be stored :
    
    * :command:`mkdir /var/openPLM`
    
    Change rights :
    
    * :command:`chown www-data:www-data /var/openPLM`
    
    Change rights for the directory where thumbnails will be stored :
    
    * :command:`chown www-data:www-data /var/django/openPLM/trunk/openPLM/media/thumbnails`
    
    Check we have all modules :
    
    * :command:`./check_modules.py` ::
    
        /usr/local/lib/python2.6/dist-packages/pyPdf-1.12-py2.6.egg/pyPdf/pdf.py:52: DeprecationWarning: the sets module is deprecated
        from sets import ImmutableSet
        All is ok

    Configure Apache server :
    * :command:`vi /etc/apache2/httpd.conf` : ::
    
            WSGIScriptAlias / /var/django/openPLM/trunk/openPLM/apache/django.wsgi
            Alias /media /var/django/openPLM/trunk/openPLM/media
            <Directory /var/django/openPLM/trunk/openPLM/docs>
                Order deny,allow
                Allow from all
            </Directory>
            <Directory /var/django/openPLM/trunk/openPLM/media>
                Order deny,allow
                Allow from all
            </Directory>
    
    Restart Apache server :
    
    * :command:`service apache2 restart`

First steps in openPLM
======================

    Open your web browser and go to : ::
    
        http://your_site_adress/admin/
        
    .. note:: Here your_site_adress is given as example but you have to use your own site adress
    
    Enter superadmin login and password :
    
    .. image:: images/admin_login.png
    
    You can add new user and edit them going to Home>Auth>User : 

    .. image:: images/admin_user.png

    Do not forget to edit Home>Plmapp>User profiles in order to give correct rights for openPLM application :

    .. image:: images/admin_userprofile.png

    .. note ::
        For more information about the `Django Admin tool <http://docs.djangoproject.com/en/dev/intro/tutorial02/>`_ . 

    Then you must create a new *Site* (use the admin interface) and sets the `SITE_ID`
    variable in the :file:`settings.py` file.

    You are now ready for your first login : ::
    
        http://localhost/
        
    .. image:: images/openplm_connexion.png


Configuring E-mails
===================

There are several variables that can be set in the :file:`settings.py` to configure
how mails are sent. See the `Django documentation <https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-EMAIL_HOST>`_ for more details.

OpenPLM adds another variable `EMAIL_OPENPLM` which is the e-mail address set
in the `from` field of each e-mail. Usually, this is a `no-reply@` address.


