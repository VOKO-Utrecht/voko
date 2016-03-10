# VOKO
Django based custom web application for food collective www.vokoutrecht.nl.

[![Travis CI](https://api.travis-ci.org/rikva/vokou.svg)](https://travis-ci.org/rikva/vokou)
## Some notes
1. This application was built on Django 1.7, RC1 and upgrading is a WIP
1. The code base needs cleaning up and adding of tests.
1. License: GNU GPLv3
1. Use at your own risk, no support.

## Dev environment

1. apt-get install virtualenvwrapper
2. restart shell
3. mkvirtualenv vokou
4. clone...

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
