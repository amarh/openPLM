===================================================
How to install openPLM server - Centos
===================================================

This document describes how to install an openPLM server which runs under Centos.


Requirements
=============

This HowTo is based on :
 * CentOS release 5.5 (Final)
 * Apache Server version: Apache/2.2.3
 * PostgreSQL 8.1.22
 * Python 2.6.5
 * Django 1.1.4
 
    .. note ::
        Django framework can run with SQLite 3 and MySQL databases and with other web servers.
        We welcome all feedbacks about these combinations. For more information, you can visit :
        `Django website <http://www.djangoproject.com/>`_

    .. note ::
        This HowTo should lead to a successful installation but is not optimized. Any suggestion
        about how to optimize this process is welcome.

Connect necessary repositories
==============================

    #. :command:`rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-4.noarch.rpm`
    #. :command:`rpm -Uvh http://download1.rpmfusion.org/free/el/updates/testing/5/i386/rpmfusion-free-release-5-0.1.noarch.rpm`
    #. :command:`rpm -Uvh http://download1.rpmfusion.org/nonfree/el/updates/testing/5/i386/rpmfusion-nonfree-release-5-0.1.noarch.rpm`
    #. :command:`wget http://www.graphviz.org/graphviz-rhel.repo`
    #. :command:`cp /path/to/graphviz-rhel.repo /etc/yum.repo.d/`

    .. note ::
		If the first 3 commands fail, you can download and move .repo file in correct place (same wget+cp process as the last command).

Install necessary packages
==========================

    #. :command:`yum groupinstall 'Development Tools'`
    #. :command:`yum install centos-ds-base-devel gcc swig perl-ExtUtils-PkgConfig`
    #. :command:`yum install httpd mod_wsgi`
    #. :command:`yum install python26 python26-tools python26-devel python26-imaging`
    #. :command:`yum install postgresql-server libpqxx libpqxx-devel`
    #. :command:`yum install pyPdf python-pip`
    #. :command:`yum install graphviz graphviz-devel`

Install SetupTools from sources
===============================

    #. :command:`wget http://pypi.python.org/packages/2.6/s/setuptools/setuptools-0.6c11-py2.6.egg#md5=bfa92100bd772d5a213eedd356d64086`
    #. :command:`sh setuptools-0.6c11-py2.6.egg --install-dir=/usr/lib/python2.6/site-packages/`

Install gadFly/kjbuckkets from sources
======================================

    #. :command:`wget http://sourceforge.net/projects/gadfly/files/gadfly/gadflyZip/gadflyZip.zip`
    #. :command:`cd /patch/to/gadflyZip.zip`
    #. :command:`unzip gadflyZip.zip`
    #. :command:`cd /patch/to/gadflyZip/`
    #. :command:`python2.6 setup.py install`
    #. :command:`cd kjbuckets`
    #. :command:`python2.6 setup.py install`

Install some python eggs
========================

    #. :command:`easy_install-2.6 setuptools`   
    #. :command:`easy_install-2.6 odfpy`
    #. :command:`easy_install-2.6 hashlib`
    #. :command:`easy_install-2.6 psycopg2`
    #. :command:`easy_install-2.6 pyPdf`

Install pygraphviz from sources
===============================

    #. :command:`wget http://pypi.python.org/packages/source/p/pygraphviz/pygraphviz-1.1rc1.tar.gz#md5=7e709a8bf8d5103b461a5f54a399ef0d`  
    #. :command:`cd /patch/to/pygraphviz/`  
    #. :command:`tar -xzvf pygraphviz-1.1rc1.tar`  
    #. :command:`cd pygraphviz-1.1rc1`  
    #. :command:`python26 setup.py install`

Install Django from sources
===========================

    #. :command:`wget http://www.djangoproject.com/download/1.1.4/tarball/`  
    #. :command:`cd /path/to/Django-1.1.4`  
    #. :command:`tar -xzvf Django-1.1.4.tar.gz`
    #. :command:`cd Django-1.1.4`  
    #. :command:`python2.6 setup.py install`


Check applications are ok
===============================

    For Apache server : ::
    
        root@openplm-demo:~# service httpd status
        
        Httpd is running (pid 5315).
    
    For Python : ::
    
        root@openplm-demo:~# python2.6
		Python 2.6.5 (r265:79063, Feb 28 2011, 21:55:56) 
		[GCC 4.1.2 20080704 (Red Hat 4.1.2-50)] on linux2
		Type "help", "copyright", "credits" or "license" for more information.
		>>> 
    
    .. note ::
    
        press :kbd:`Control-D` to exit Python shell
    
    For Django : ::
    
        root@openplm-demo:~# python2.6 /usr/bin/django-admin.py --version
        1.1.4

Get codes using Subversion
==========================

    * :command:`yum install subversion`
    
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

    Start PostgreSQL :

    * :command:`service postgresql start`

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
    
        /usr/bin/initdb
        
    * :command:`su postgres`
    * :command:`/usr/bin/initdb --encoding=UTF-8 --locale=fr_FR.UTF-8 --pgdata=/var/postgres/`
    * :command:`/usr/bin/postgres -D /var/postgres &`

Modify postgresql authentification rules and restart
====================================================

    * :command:`vi /var/lib/pgsql/data/pg_hba.conf` ::
		
			local		all		postgres			ident sameuser
			local		all		all				md5
			host    	all		all		127.0.0.1/32	md5

    * :command:`psql` ::
    
            postgres=#create database openplm;
            postgres=#create role django with password 'MyPassword' login;
            \q
    
    * :command:`exit`
    * :command:`service postgresql restart`

Finalize installation
=====================

    * :command:`cd /var/django/openPLM/trunk/openPLM/`
    
    Check we have all modules :
     
    * :command:`python2.6 check_modules.py`
		All is ok
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
    
    Change rights for the directory where thumbnails and navigate pictures will be stored :
    
    * :command:`chown www-data:www-data /var/django/openPLM/trunk/openPLM/media/thumbnails`
    * :command:`chown www-data:www-data /var/django/openPLM/trunk/openPLM/media/navigate`

	Activate correct navigate.py file :
    * :command:`cp plmapp/navigate.py.centos plmapp/navigate.py
    
    Configure Apache server :

    * :command:`vi /etc/httpd.d/conf/httpd.conf` : ::
    
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
    
    * :command:`service httpd restart`

    .. note ::
			I had an issue with wsgi and I had to create /var/www/.python-eggs directory and set correct rights.

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
    
    You are now ready for your first login : ::
    
        http://localhost/
        
    .. image:: images/openplm_connexion.png


