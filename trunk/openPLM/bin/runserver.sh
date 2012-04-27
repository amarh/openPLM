#! /usr/bin/env sh
./manage.py celeryd -Q mails,index,celery,step -c 3 -l info &
python -m smtpd -n -c DebuggingServer localhost:1025 &
./manage.py runserver
exit 0
