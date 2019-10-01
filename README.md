# VOKO
Django based custom web application for food collective www.vokoutrecht.nl.

[![Travis CI](https://api.travis-ci.org/rikva/voko.svg)](https://travis-ci.org/rikva/voko)
## Some notes
1. The code base needs cleaning up and adding of tests.
1. License: GNU GPLv3
1. Use at your own risk, no support.

## Dev environment

1. Install Docker Compose.
1. Run `docker-compose -f docker-compose-dev.yaml up`
1. After initialization, in second shell run `docker-compose -f docker-compose-dev.yaml exec voko ./manage.py createsuperuser` to create a user.

### Run tests
    docker-compose -f docker-compose-dev.yaml run voko test

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
