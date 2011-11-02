#! /bin/sh
coverage erase
coverage run ./manage.py test  --settings=settings_tests
coverage run -a plmapp/utils.py
coverage run -a plmapp/lifecycle.py
coverage html
