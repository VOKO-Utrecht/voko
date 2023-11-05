#!/bin/bash

cd /code/webapp

# Start server
echo "Starting server"
pipenv run python manage.py runserver 0.0.0.0:8000 --settings=$VOKO_ENV