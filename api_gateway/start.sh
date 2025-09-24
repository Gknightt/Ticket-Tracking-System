#!/bin/sh

# Apply migrations
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

# Seed initial service endpoints
python manage.py seed_services

# Start Gunicorn server
gunicorn api_gateway.wsgi:application --bind 0.0.0.0:4000