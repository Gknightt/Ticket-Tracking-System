# Gmail API Quick Reference

## Send Email from Auth Service

### Password Reset
```python
from notification_client import notification_client

user = User.objects.get(email=email)
reset_token = PasswordResetToken.generate_for_user(user)

notification_client.send_password_reset_email_async(
    user=user,
    reset_token=reset_token,
    request=request  # Optional
)
```

### User Invitation
```python
from notification_client import notification_client

notification_client.send_invitation_email_async(
    user=new_user,
    temp_password="TempPass123",
    system_name="TTS",
    role_name="Agent"
)
```

### OTP Code
```python
from notification_client import notification_client

otp_instance = UserOTP.generate_for_user(user, otp_type='email')

notification_client.send_otp_email_async(
    user=user,
    otp_code=otp_instance.otp_code
)
```

### System Addition
```python
from notification_client import notification_client

notification_client.send_system_addition_email_async(
    user=user,
    system_name="HDTS",
    role_name="Reviewer"
)
```

## Send Custom Email

### With Headers (Recommended)
```python
from celery import Celery

app = Celery('auth')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.send_task(
    'notifications.send_email_with_headers',
    kwargs={
        'to_email': 'user@example.com',
        'subject': 'Custom Subject',
        'headers': {
            'Field_Name': 'Field Value',
            'Another_Field': 'Another Value',
            'Message': 'Your message here'
        },
        'user_id': str(user.id)  # Optional
    },
    queue='NOTIFICATION_TASKS'
)
```

### Standard Email
```python
app.send_task(
    'notifications.send_email_via_gmail',
    kwargs={
        'to_email': 'user@example.com',
        'subject': 'Subject',
        'body_text': 'Plain text content',
        'body_html': '<p>HTML content</p>',  # Optional
        'notification_type': 'custom',  # Optional
        'user_id': str(user.id)  # Optional
    },
    queue='NOTIFICATION_TASKS'
)
```

## Check Email Status

### Query NotificationLog
```python
from notifications.models import NotificationLog

# Recent emails
logs = NotificationLog.objects.filter(
    user_email='user@example.com'
).order_by('-created_at')[:5]

for log in logs:
    print(f"{log.notification_type}: {log.status}")
    if log.status == 'failed':
        print(f"Error: {log.error_message}")
```

### Check specific email
```python
log = NotificationLog.objects.get(id=log_id)
print(f"Status: {log.status}")
print(f"Sent at: {log.sent_at}")
print(f"Subject: {log.subject}")
```

## Celery Commands

### Start Worker
```bash
cd notification_service
celery -A notification_service worker --pool=solo --loglevel=info -Q NOTIFICATION_TASKS,inapp-notification-queue
```

### Check Active Tasks
```bash
celery -A notification_service inspect active
```

### Check Registered Tasks
```bash
celery -A notification_service inspect registered
```

### Purge Queue (Dev Only!)
```bash
celery -A notification_service purge
```

## Troubleshooting

### Gmail API Not Working
```python
# Test Gmail service
from notifications.gmail_service import get_gmail_service

gmail = get_gmail_service()
if gmail.service is None:
    print("Gmail service not initialized - check credentials.json")
else:
    print("Gmail service OK")
```

### Task Not Processing
```bash
# Check worker is running and listening to correct queue
celery -A notification_service inspect active_queues

# Check RabbitMQ
sudo systemctl status rabbitmq-server
```

### Email Not Delivered
```python
# Check notification log
from notifications.models import NotificationLog

failed = NotificationLog.objects.filter(status='failed').order_by('-created_at')[:10]
for log in failed:
    print(f"{log.created_at}: {log.recipient_email}")
    print(f"Error: {log.error_message}\n")
```

## Environment Variables

### notification_service/.env
```env
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_SENDER_EMAIL=your-email@gmail.com
DJANGO_DEFAULT_FROM_EMAIL=noreply@yourdomain.com
DJANGO_CELERY_BROKER_URL=amqp://admin:admin@localhost:5672/
```

### auth/.env
```env
DJANGO_CELERY_BROKER_URL=amqp://admin:admin@localhost:5672/
NOTIFICATION_SERVICE_URL=http://localhost:8001
```

## Common Tasks

### Setup Gmail API
```bash
# Run automated setup
./Scripts/setup_gmail_api.sh
```

### Manual Setup
1. Place `credentials.json` in `notification_service/`
2. Update `.env` with Gmail settings
3. Install requirements: `pip install -r requirements.txt`
4. Start Celery worker

### Test Email
```python
# Django shell in notification_service
from notifications.gmail_service import get_gmail_service

gmail = get_gmail_service()
success, msg_id, error = gmail.send_email(
    to_email='test@example.com',
    subject='Test',
    body_text='Test email'
)
print(f"Success: {success}, Message ID: {msg_id}")
```

## File Locations

- **Gmail Service**: `notification_service/notifications/gmail_service.py`
- **Celery Tasks**: `notification_service/notifications/tasks.py`
- **Notification Client**: `auth/notification_client.py`
- **Settings**: `notification_service/notification_service/settings.py`
- **Credentials**: `notification_service/credentials.json` (gitignored)

## Documentation

- Full Guide: `GMAIL_API_MIGRATION.md`
- Summary: `GMAIL_API_MIGRATION_SUMMARY.md`
- Google Docs: https://developers.google.com/gmail/api/guides
