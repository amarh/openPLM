.. _badges-admin:

===============================================
badges - 
===============================================

.. warning::

    This application is still in early development stage.

This application add a "BADGES" tab on user profile.


settings.py
==============

To enable the *badges* application, it must be enabled in the settings file: add
``'openPLM.apps.badges'`` to the list of installed applications
(:const:`INSTALLED_APPS`).
You must also add a middleware: add ``'openPLM.apps.badges.middleware.GlobalRequest'``
to the :const:`MIDDLEWARE_CLASSES` setting (after the ProfileLocaleMiddleware).



Synchronizing the database
==========================

Run ``./manage.py migrate badges``.


Collecting static files
==========================

Run ``./manage.py collectstatic``.

Award badges
=============

If you already had installed an openPLM, you can award badges to all users according
to what they have done before the application has been installed.

For that run ``./manage.py award_badges``.

Testing
=========

Log in openPLM , go to your profile (then tab "BADGES") and check if you have won a badge.

If you didn't get any badge, fill your profile (first name, last name and email), you should 
get the Autobiographer badge (one of the easiest).

From the "BADGES" tab and pages which describe the badges, you can reach a list of 
all available badges.
