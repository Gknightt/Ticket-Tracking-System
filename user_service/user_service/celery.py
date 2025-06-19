import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_service.settings')

app = Celery('user_service')

# Load broker URL from environment variable
app.conf.broker_url = os.environ.get("CELERY_BROKER_URL")

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()