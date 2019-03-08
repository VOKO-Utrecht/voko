#!/bin/bash

set -e

source /home/voko/.virtualenvs/voko/bin/activate

cd
source ~/production_secrets.sh

cd voko/webapp
exec uwsgi uwsgi.ini
