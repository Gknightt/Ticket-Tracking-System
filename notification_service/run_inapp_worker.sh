#!/bin/bash

# Start Celery worker for in-app notifications
echo "Starting Celery worker for in-app notifications..."
celery -A notification_service worker --loglevel=info --concurrency=2 -Q inapp-notification-queue
# windows
celery -A notification_service worker --loglevel=info -P solo -Q inapp-notification-queue
