#!/bin/bash
killall uwsgi
sleep 2
nohup uwsgi -s /tmp/uwsgi.sock --file /home/work/proj/thepast/pastme.py --callable app --processes 2 &
