#!/bin/bash

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate --settings=vokou.settings.development

# Start server
echo "Starting server"
python manage.py runserver 0.0.0.0:8000 --settings=vokou.settings.development