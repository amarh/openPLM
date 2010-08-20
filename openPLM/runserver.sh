#! /usr/bin/env sh
python -m smtpd -n -c DebuggingServer localhost:1025 &
./manage.py runserver
