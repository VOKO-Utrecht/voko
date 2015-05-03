# VOKO automation
![Travis CI](https://api.travis-ci.org/rikva/vokou.svg)
## Some notes
1. This application depends on Django 1.7, RC1.
2. It's been a while since I last crafted a Django application. 
2. Because of time shortage,
   1. This app is not written TDD
   2. There will be no i18n support (at least initially)
   3. Code or styling may be ugly - functionality is the main concern.
3. No license yet.
4. Limited support ;)

## Dev environment

1. apt-get install virtualenvwrapper
2. new shell
3. mkvirtualenv vokou
4. ...

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
