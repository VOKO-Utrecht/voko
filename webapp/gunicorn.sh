#!/bin/bash

set -e
DJANGO_SETTINGS_MODULE=vokou.settings.production

USER=voko
GROUP=voko

cd /home/voko/vokou/webapp
source /home/voko/.virtualenvs/voko/bin/activate

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

exec gunicorn vokou.wsgi:application -c /home/voko/vokou/webapp/gunicorn.conf.py
