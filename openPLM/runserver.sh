#! /usr/bin/env sh
./manage.py celeryd -Q mails,index,celery -c 3 -l info --settings=my_settings &
python -m smtpd -n -c DebuggingServer localhost:1025 &
./manage.py runserver
exit 0
