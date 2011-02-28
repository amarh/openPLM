#! /usr/bin/env sh

# run this script to generate/update translation files
/usr/lib/python-django/bin/django-admin.py makemessages -l fr -e html,htm
# /usr/local/bin/django-admin.py makemessages -l fr -e html,htm
/usr/lib/python-django/bin/django-admin.py compilemessages 
# /usr/local/bin/django-admin.py compilemessages
