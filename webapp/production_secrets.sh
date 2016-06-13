#!/bin/bash

DJANGO_SETTINGS_MODULE=vokou.settings.production
USER=voko
GROUP=voko

export DJANGO_SECRET_KEY=""
export DB_PASSWORD=""
export MOLLIE_API_KEY=""
