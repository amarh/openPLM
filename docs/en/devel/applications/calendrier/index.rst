===================================
calendrier -- calendar generations
===================================

.. versionadded:: 1.2

This application can generate HTML calendars and iCalendar files.
Currently it can generate a month view of an history page or 
of the timeline page.


How HTML calendars are generated
================================

Short answer: using the :class:`.calendar.HTMLCalendar` class from the stdlib.

This `article`_ explains how to generate an HTML calendar using
the HTMLCalendar class.

.. _article: http://uggedal.com/journal/creating-a-flexible-monthly-calendar-in-django/


How iCalendar files are generated
=================================

Short answer: using `django-ical`_.

.. _django-ical: https://bitbucket.org/IanLewis/django-ical/

Views
========

.. automodule::  openPLM.apps.calendrier.views
    :members:
    :show-inheritance:
    :undoc-members:

