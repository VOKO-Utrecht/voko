#!/bin/bash

set -e

source ~/production_secrets.sh

source /home/voko/.virtualenvs/voko/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

cd /home/voko/voko/webapp
exec python manage.py runcrons
