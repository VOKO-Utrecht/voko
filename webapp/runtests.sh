#!/bin/bash
python manage.py test --settings=vokou.settings.testing --nologcapture #--with-coverage --cover-package=vokou,ordering,mailing,log,finance,accounts
