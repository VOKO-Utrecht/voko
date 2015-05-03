#!/bin/bash

set -e

cd /home/voko/vokou/webapp
source production_secrets.sh

source /home/voko/.virtualenvs/voko/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

exec python manage.py runcrons
