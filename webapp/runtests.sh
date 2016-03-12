#!/bin/bash
export DJANGO_SETTINGS_MODULE=vokou.settings.testing

python manage.py test --nologcapture "$@" 

# To enable coverage:
#--with-coverage --cover-package=vokou,ordering,mailing,log,finance,accounts
