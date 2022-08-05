# VOKO
Django based custom web application for food collective www.vokoutrecht.nl.

![example workflow](https://github.com/VOKO-Utrecht/voko/actions/workflows/ci.yml/badge.svg)

## Some notes
1. The code base needs cleaning up and adding of tests.
2. License: GNU GPLv3
3. Use at your own risk, no support.


# Development environment using Docker
### Get the code
1. Run: `git clone https://github.com/VOKO-Utrecht/voko.git`
2. Run: cd voko

### Initiate the database
1. Run: docker-compose up db
2. Wait until db is ready to accept connections
3. Press CTRL-C to stop the db container again
_first time postgress restarts which confuses Django_

### Start voko website and run migrations
1. Run: docker-compose up -d
2. Run: docker exec -it voko_web_1 bash
3. Run: ./manage.py makemigrations --settings=vokou.settings.development
4. Run: ./manage.py migrate --settings=vokou.settings.development
5. Run: exit

### Create superuser in the voko web container
1. Run: docker exec -it voko_web_1 bash
2. Run: ./manage.py createsuperuser --settings=vokou.settings.development
3. _follow the prompts_
4. Run: exit

In your browser go to: http://127.0.0.1:8000/admin/ordering/orderround/

Login as the super user just created \
Use the admin site to create an order round (otherwise you get an ugly error going to the main site --FIXTHIS)



# Development environment without Docker
1. Run: pip install --user pipenv
2. Run: `git clone https://github.com/VOKO-Utrecht/voko.git`
3. Run: `cd voko`
4. Run: `pipenv install --dev`
5. Run: `pipenv shell`
6. In vokou/settings/development.py: \
        - Uncomment config for sqlite3 \
        - Comment the config for postgresql


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
