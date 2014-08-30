#!/bin/bash

set -e
DJANGODIR=/home/ubuntu/app
DJANGO_SETTINGS_MODULE=vokou.settings.production

USER=voko
GROUP=voko

cd /home/voko/vokou/webapp
source /home/voko/.virtualenvs/voko/bin/activate

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

test -d $LOGDIR || mkdir -p $LOGDIR
exec gunicorn vokou.wsgi:application -c /home/voko/vokou/webapp/gunicorn.conf.py
