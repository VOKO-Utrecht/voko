#!/bin/bash

set -e

cd
source ~/production_secrets.sh

cd voko/webapp
exec uwsgi uwsgi.ini
