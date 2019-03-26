# VOKO
Django based custom web application for food collective www.vokoutrecht.nl.

[![Travis CI](https://api.travis-ci.org/rikva/voko.svg)](https://travis-ci.org/rikva/voko)
## Some notes
1. The code base needs cleaning up and adding of tests.
1. License: GNU GPLv3
1. Use at your own risk, no support.

## Dev environment

1. Run: `apt install virtualenvwrapper`
2. restart shell
3. Run: `git clone https://github.com/rikva/voko.git`
4. Run: `cd voko`
5. Run: `mkvirtualenv vokou --python=[path to pyton3 binary] -r ./requirements/development.txt`

### Run tests
    cd webapp
    ./runtests.sh

### Set up sqlite database
    ./manage.py migrate --settings=vokou.settings.development
    ./manage.py createsuperuser --settings=vokou.settings.development

### Run development server
    cd webapp
    ./manage.py runserver --settings=vokou.settings.development

### Adding user
1. Register as new user at: http://localhost:8000/accounts/register/
2. Look up the confirmation token at: http://localhost:8000/admin/accounts/emailconfirmation/
3. Visit (replace TOKEN with copied token): http://localhost:8000/accounts/register/confirm/TOKEN
4. Log in as superuser and go to user admin: http://localhost:8000/admin/accounts/vokouser/
5. Select your user, choose in dropdown: "Gebruikersactivatie na bezoek info-avond", click "Uitvoeren" button
6. Log out as superuser, or visit the next link incognito (replace TOKEN with copied token): http://localhost:8000/accounts/register/finish/TOKEN
7. Fill in fields and submit
