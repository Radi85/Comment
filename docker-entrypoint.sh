#!/usr/bin/env bash
set -e

echo "running migrations"
python /code/manage.py migrate

echo "creating initial data"
python /code/manage.py create_initial_data

echo "Done"

python manage.py runserver 0.0.0.0:8000
