#!/bin/bash

set -e

cd /home/voko/vokou/webapp
source production_secrets.sh

source /home/voko/.virtualenvs/voko/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

exec gunicorn vokou.wsgi:application -c /home/voko/vokou/webapp/gunicorn.conf.py
