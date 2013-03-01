.. _calendrier-admin:

===============================================
calendrier -- Calendar views
===============================================

.. versionadded:: 1.2

This application adds the following features:

    * show timeline and history pages as a calendar
    * export of calendars to iCalendar (.ics) format

Dependencies
==============

This application optionally depends on
`django-ical <https://bitbucket.org/IanLewis/django-ical/overview>`_
to export generated calendars to iCalendar format.

To install ``django-ical``: ``pip install django-ical``.


settings.py
==============

To enable the *calendrier* application, it must be enabled in the settings file: add
``'openPLM.apps.calendrier'`` to the list of installed applications
(:const:`~settings.INSTALLED_APPS`).

Collecting static files
==========================

Run ``./manage.py collectstatic``.

Testing
=========

To test this application, visit the timeline or any history page.
A *Calendar* link should be visible. Visit this link, you should
see a nice calendar.
If `django-ical` is installed, a download link is available at
the bottom of the page. 

