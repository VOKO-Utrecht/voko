#!/bin/bash

set -e

echo "Starting VOKO production setup..."

cd /code/webapp

echo "Waiting for database to be ready..."
until pg_isready -h "${POSTGRES_HOST:-db}" -U "${POSTGRES_USER:-voko}"; do
    echo "Database is not ready yet. Waiting..."
    sleep 2
done

echo "Database is ready!"

echo "Running migrations..."
uv run python manage.py migrate --settings="$DJANGO_SETTINGS_MODULE"

echo "Collecting static files..."
uv run python manage.py collectstatic --noinput --settings="$DJANGO_SETTINGS_MODULE"

echo "Starting gunicorn..."
exec uv run gunicorn vokou.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout 120 \
    --forwarded-allow-ips="127.0.0.1" \
    --access-logfile - \
    --error-logfile -
