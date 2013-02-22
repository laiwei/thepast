#!/bin/bash

#hash uwsgi 2>&- || { echo >&2 "I require uwsgi but it's not installed.  Aborting."; exit 1; }
#
#killall uwsgi
#sleep 2
##nohup uwsgi -s /tmp/uwsgi.sock --file `pwd`/pastme.py --callable app &
#nohup uwsgi -s /tmp/uwsgi.sock --lazy --file `pwd`/pastme.py --callable app --processes 4 &

## use gunicorn

hash gunicorn 2>&- || { echo >&2 "I require gunicorn but it's not installed.  Aborting."; exit 1; }
killall gunicorn
sleep 2
gunicorn -c gunicorn.conf pastme:app -D --error-logfile ./app.log
