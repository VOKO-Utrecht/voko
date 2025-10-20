#!/bin/bash

# Exit on any error
set -e

echo "Starting VOKO webapp setup..."

# Change to webapp directory
cd /code/webapp

# Wait for database to be ready
echo "Waiting for database to be ready..."
until pg_isready -h db -U postgres; do
    echo "Database is not ready yet. Waiting..."
    sleep 2
done

echo "Database is ready!"

# Run migrations
echo "Running migrations..."
uv run python manage.py makemigrations --settings=vokou.settings.docker_development
uv run python manage.py migrate --settings=vokou.settings.docker_development

# Create superuser if it doesn't exist
echo "Creating superuser if it doesn't exist..."
uv run python manage.py createsuperuser --noinput --settings=vokou.settings.docker_development || echo "Superuser already exists or creation failed"

# Run crons
echo "Running crons..."
uv run python manage.py runcrons --force --settings=vokou.settings.docker_development

# Start server
echo "Starting development server..."
uv run python manage.py runserver 0.0.0.0:8000 --settings=vokou.settings.docker_development