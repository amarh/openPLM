#! /usr/bin/env sh

# run this script to generate/update translation files
django-admin.py makemessages -l fr -e html,htm,xhtml,py
django-admin.py compilemessages 
