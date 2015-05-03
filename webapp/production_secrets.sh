#!/bin/bash

DJANGO_SETTINGS_MODULE=vokou.settings.production
USER=voko
GROUP=voko

export DJANGO_SECRET_KEY=""
export DB_PASSWORD=""
export QANTANI_MERCHANT_ID=""
export QANTANI_MERCHANT_KEY=""
export QANTANI_MERCHANT_SECRET=""
