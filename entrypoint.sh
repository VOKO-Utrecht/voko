#!/usr/bin/env sh

set -e

if [ -z "$1" ]; then
    echo "No command supplied."
    echo
    echo "Exiting!"
    exit 1
fi

echo
echo "Received command: $@"
echo

if [ "$1" = 'devserver' ]; then
    ./wait-for postgresql:5432
    ./manage.py migrate
    ./manage.py collectstatic --noinput
    ./manage.py runserver 0.0.0.0:8000
elif [ "$1" = 'test' ]; then
    ./wait-for postgresql:5432
    ./manage.py test --nologcapture
elif [ "$1" = 'prodserver' ]; then
    ./manage.py migrate
    ./manage.py collectstatic --noinput
    uwsgi uwsgi.ini
else
    echo "Unknown command: $1"
    echo "Exiting!"
    exit 1
fi
