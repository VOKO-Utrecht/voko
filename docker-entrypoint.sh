#!/bin/bash

cd /code/webapp
# Apply database migrations
echo "Apply database migrations"
pipenv run python manage.py makemigrations --settings=vokoa.settings.development
pipenv run python manage.py migrate --settings=vokoa.settings.development


# Start server
echo "Starting server"
pipenv run python manage.py runserver 0.0.0.0:8000 --settings=vokoa.settings.development 
