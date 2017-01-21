#!/bin/bash

set -e

cd
source ~/production_secrets.sh

source /home/voko/.virtualenvs/voko/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

cd voko/webapp
exec gunicorn vokou.wsgi:application -c gunicorn.conf.py
