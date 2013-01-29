#! /bin/sh
coverage run $* ./manage.py test  --settings=settings_tests
coverage html $*

