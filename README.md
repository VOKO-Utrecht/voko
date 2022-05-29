# VOKO
Django based custom web application for food collective www.vokoutrecht.nl.

![example workflow](https://github.com/VOKO-Utrecht/voko/actions/workflows/ci.yml/badge.svg)

## Some notes
1. The code base needs cleaning up and adding of tests.
2. License: GNU GPLv3
3. Use at your own risk, no support.

## Development environment
1. Run: pip install --user pipenv
2. Run: `git clone https://github.com/VOKO-Utrecht/voko.git`
3. Run: `cd voko`
4. Run: `pipenv install --dev`
5. Run: `pipenv shell`

### Set up sqlite database
    cd webapp
    ./manage.py migrate --settings=vokou.settings.development
    ./manage.py createsuperuser --settings=vokou.settings.development

### Run tests
    cd webapp
    ./runtests.sh

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

## Marking member as sleeping member
1. Go to http://localhost:8000/admin/accounts/vokouser/
2. Select user
3. Choose in dropdown: "Anonimiseer account"
4. Click "Uitvoeren" button

## Re-activating sleeping member
1. Go to http://localhost:8000/admin/accounts/sleepingvokouser/
2. Open user
3. De-tick "Sleeping (inactive) member"
4. click "OPSLAAN" button
