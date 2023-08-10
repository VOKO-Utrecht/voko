#!/bin/bash
export DJANGO_SETTINGS_MODULE=vokoa.settings.testing

python manage.py test --nologcapture "$@" 

# To enable coverage:
#--with-coverage --cover-package=vokoa,ordering,mailing,log,finance,accounts
