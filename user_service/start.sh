#!/bin/sh

# Apply migrations
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

# Start Gunicorn server
gunicorn user_service.wsgi:application --bind 0.0.0.0:8000