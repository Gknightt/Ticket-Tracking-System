#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn workflow_api.wsgi:application --bind 0.0.0.0:8000
