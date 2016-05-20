# VOKO
Django based custom web application for food collective www.vokoutrecht.nl.

[![Travis CI](https://api.travis-ci.org/rikva/voko.svg)](https://travis-ci.org/rikva/voko)
## Some notes
1. The code base needs cleaning up and adding of tests.
1. License: GNU GPLv3
1. Use at your own risk, no support.

## Dev environment

1. apt-get install virtualenvwrapper
2. restart shell
3. mkvirtualenv vokou
4. clone...

### Run tests
    cd webapp
    ./runtests.sh

### Set up sqlite database
    ./manage.py migrate --settings=vokou.settings.development 
    ./manage.py createsuperuser --settings=vokou.settings.development
    
### Run development server
    cd webapp
    ./manage.py runserver --settings=vokou.settings.development

## Supervisor config
```yaml
[program:gunicorn]
environment=
    DJANGO_SETTINGS_MODULE=vokou.settings.production
command=/home/voko/vokou/webapp/gunicorn.sh
directory=/home/voko/vokou/webapp
user=voko
autostart=true
autorestart=true
redirect_stderr=true
```
