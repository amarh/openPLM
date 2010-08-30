#! /usr/bin/env sh

# run this script to generate/update translation files
django-admin makemessages -l fr -e html,htm
django-admin compilemessages
