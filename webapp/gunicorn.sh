#!/bin/bash

set -e
DJANGO_SETTINGS_MODULE=vokou.settings.production

USER=voko
GROUP=voko

cd /home/voko/vokou/webapp
source /home/voko/.virtualenvs/voko/bin/activate

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export DJANGO_SECRET_KEY=""
export DB_PASSWORD=""
export QANTANI_MERCHANT_ID=""
export QANTANI_MERCHANT_KEY=""
export QANTANI_MERCHANT_SECRET=""


exec gunicorn vokou.wsgi:application -c /home/voko/vokou/webapp/gunicorn.conf.py
