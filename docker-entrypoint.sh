#!/bin/bash

cd /code/webapp
# Apply database migrations
echo "Apply database migrations"
pipenv run python manage.py makemigrations --settings=vokou.settings.development
pipenv run python manage.py migrate --settings=vokou.settings.development


# Start server
echo "Starting server"
pipenv run python manage.py runserver 0.0.0.0:8000 --settings=vokou.settings.development 
