# Gmail API Migration Guide

This document describes the migration from SMTP to Gmail API for all email sending functionality in the Ticket Tracking System.

## Overview

All email sending has been migrated from traditional SMTP to the Gmail API. This provides:

- **Better reliability**: More robust authentication and delivery
- **Enhanced security**: OAuth 2.0 service account authentication instead of passwords
- **Header-based messaging**: Email content can be sent as headers instead of templated messages
- **Centralized email service**: All emails are sent through the notification_service microservice
- **Async processing**: Emails are sent via Celery tasks for non-blocking operations

## Architecture Changes

### Before (SMTP)
```
auth service → Django send_mail() → SMTP server → Gmail
```

### After (Gmail API)
```
auth service → Celery task → notification_service → Gmail API → Gmail
```

## Components

### 1. Gmail API Service (`notification_service/notifications/gmail_service.py`)

Core service class that handles Gmail API authentication and email sending.

**Key Features:**
- Service account authentication with OAuth 2.0
- Support for plain text and HTML emails
- Header-based email sending (no templates required)
- Singleton pattern for efficient resource usage

**Methods:**
- `send_email()`: Send standard email with body text
- `send_email_with_headers()`: Send email where message content is in custom headers

### 2. Celery Tasks (`notification_service/notifications/tasks.py`)

Async tasks for sending various types of emails:

- `send_email_via_gmail`: Generic email sending
- `send_email_with_headers`: Email with custom headers (preferred)
- `send_password_reset_email`: Password reset with reset URL
- `send_invitation_email`: New user invitation with temp password
- `send_otp_email`: OTP code delivery
- `send_system_addition_email`: System access notification

### 3. Notification Client (`auth/notification_client.py`)

Client library for auth service to enqueue email tasks:

- `send_password_reset_email_async()`
- `send_invitation_email_async()`
- `send_otp_email_async()`
- `send_system_addition_email_async()`

### 4. Updated Services (`notifications/services.py`)

Modified to use Gmail API instead of Django's `send_mail()`.

## Setup Instructions

### Step 1: Create Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"

4. Create a service account:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Fill in service account details
   - Grant "Gmail API User" role
   - Click "Done"

5. Create and download credentials:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose "JSON" format
   - Download the `credentials.json` file

### Step 2: Configure Domain-Wide Delegation (If using G Suite)

If using a G Suite/Workspace domain:

1. In service account details, note the "Client ID"
2. Go to Google Workspace Admin Console
3. Navigate to Security → API Controls → Domain-wide Delegation
4. Add the Client ID with scope: `https://www.googleapis.com/auth/gmail.send`

### Step 3: Configure notification_service

1. Copy `credentials.json` to the `notification_service/` directory:
   ```bash
   cp /path/to/credentials.json /path/to/notification_service/credentials.json
   ```

2. Update `.env` file in `notification_service/`:
   ```env
   # Gmail API Configuration
   GMAIL_CREDENTIALS_PATH=credentials.json
   GMAIL_SENDER_EMAIL=your-email@gmail.com
   DJANGO_DEFAULT_FROM_EMAIL=noreply@yourdomain.com
   ```

3. Install requirements:
   ```bash
   cd notification_service
   pip install -r requirements.txt
   ```

### Step 4: Update Celery Workers

Start Celery workers with the NOTIFICATION_TASKS queue:

```bash
cd notification_service
celery -A notification_service worker --pool=solo --loglevel=info -Q NOTIFICATION_TASKS,inapp-notification-queue
```

### Step 5: Verify RabbitMQ Configuration

Ensure RabbitMQ is running and accessible:

```bash
# Check RabbitMQ status
sudo systemctl status rabbitmq-server

# Access management UI
# http://localhost:15672 (default: admin/admin)
```

## Usage Examples

### From Auth Service

#### Send Password Reset Email
```python
from notification_client import notification_client

# In password reset view
user = User.objects.get(email=email)
reset_token = PasswordResetToken.generate_for_user(user)

success = notification_client.send_password_reset_email_async(
    user=user,
    reset_token=reset_token,
    request=request
)
```

#### Send Invitation Email
```python
from notification_client import notification_client

success = notification_client.send_invitation_email_async(
    user=new_user,
    temp_password="TempPass123",
    system_name="TTS",
    role_name="Agent"
)
```

#### Send OTP Email
```python
from notification_client import notification_client

otp_instance = UserOTP.generate_for_user(user, otp_type='email')

success = notification_client.send_otp_email_async(
    user=user,
    otp_code=otp_instance.otp_code
)
```

### Direct Task Invocation (Advanced)

```python
from celery import Celery

app = Celery('myapp')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Send email with custom headers
app.send_task(
    'notifications.send_email_with_headers',
    kwargs={
        'to_email': 'user@example.com',
        'subject': 'Custom Notification',
        'headers': {
            'User_Name': 'John Doe',
            'Action': 'Account Created',
            'Timestamp': '2025-11-20 10:30:00 UTC',
            'Message': 'Your account has been successfully created.'
        }
    },
    queue='NOTIFICATION_TASKS'
)
```

## Email Header Format

When using `send_email_with_headers`, the email body is auto-generated from the headers dictionary:

**Input:**
```python
headers = {
    'User_Name': 'John Doe',
    'Reset_URL': 'https://example.com/reset?token=abc123',
    'Expiry_Time': '1 hour',
    'Message': 'Please click the reset URL to reset your password.'
}
```

**Generated Email Body:**
```
User Name: John Doe
Reset Url: https://example.com/reset?token=abc123
Expiry Time: 1 hour
Message: Please click the reset URL to reset your password.
```

**Custom Headers in Email:**
All headers are also added to the email as `X-` prefixed custom headers for programmatic parsing if needed.

## Monitoring & Troubleshooting

### Check Notification Logs

All emails are logged in the `NotificationLog` model:

```python
from notifications.models import NotificationLog

# Get recent emails
recent_emails = NotificationLog.objects.order_by('-created_at')[:10]

for log in recent_emails:
    print(f"{log.notification_type} to {log.recipient_email}: {log.status}")
```

### Check Celery Task Status

```bash
# View active tasks
celery -A notification_service inspect active

# View registered tasks
celery -A notification_service inspect registered

# Purge all tasks (development only!)
celery -A notification_service purge
```

### Common Issues

#### 1. Gmail API Not Initialized
**Error:** `Gmail API service not initialized`

**Solution:**
- Verify `credentials.json` exists at `GMAIL_CREDENTIALS_PATH`
- Check file permissions
- Ensure Gmail API is enabled in Google Cloud Console

#### 2. Authentication Error
**Error:** `Failed to send email: 401 Unauthorized`

**Solution:**
- Verify service account has correct permissions
- Check domain-wide delegation is configured (for G Suite)
- Ensure `GMAIL_SENDER_EMAIL` matches authorized email

#### 3. Tasks Not Being Processed
**Error:** Emails not being sent, no errors

**Solution:**
- Check Celery worker is running
- Verify worker is listening to `NOTIFICATION_TASKS` queue
- Check RabbitMQ is running and accessible
- Verify `DJANGO_CELERY_BROKER_URL` in `.env`

#### 4. ImportError in Auth Service
**Error:** `Cannot import notification_client`

**Solution:**
- Ensure `notification_client.py` is in auth service root
- Check Python path includes auth service directory
- Restart Django development server

## Migration Checklist

- [x] Created Gmail API service module
- [x] Created Celery tasks for email sending
- [x] Updated notification_client with async methods
- [x] Migrated password reset emails
- [x] Migrated invitation emails
- [x] Migrated OTP emails
- [x] Migrated system addition emails
- [x] Updated requirements.txt
- [x] Updated .env.example
- [x] Updated settings.py with Gmail config
- [x] Updated Celery task routes

## Testing

### Test Gmail API Service

```python
# In Django shell (notification_service)
from notifications.gmail_service import get_gmail_service

gmail = get_gmail_service()

success, msg_id, error = gmail.send_email(
    to_email='test@example.com',
    subject='Test Email',
    body_text='This is a test email from Gmail API'
)

print(f"Success: {success}, Message ID: {msg_id}, Error: {error}")
```

### Test Celery Task

```python
# In Django shell (auth or notification_service)
from celery import Celery

app = Celery('test')
app.config_from_object('django.conf:settings', namespace='CELERY')

result = app.send_task(
    'notifications.send_email_with_headers',
    kwargs={
        'to_email': 'test@example.com',
        'subject': 'Test Subject',
        'headers': {
            'Test_Field': 'Test Value',
            'Message': 'This is a test message'
        }
    },
    queue='NOTIFICATION_TASKS'
)

print(f"Task ID: {result.id}")
```

## Rollback Procedure

If you need to rollback to SMTP:

1. Comment out Gmail API task routes in `settings.py`
2. Restore old `send_mail()` functions in `users/serializers.py` and `system_roles/serializers.py`
3. Update `.env` to use SMTP backend:
   ```env
   DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   ```
4. Restart services

## Performance Considerations

- **Task Queuing**: Emails are sent asynchronously, so API responses are fast
- **Retry Logic**: Celery handles retries on failure (default: 3 retries)
- **Rate Limiting**: Gmail API has rate limits (users/day, messages/day)
- **Logging**: All emails are logged with status in `NotificationLog`

## Security Notes

- **Service Account Key**: Keep `credentials.json` secure, never commit to Git
- **Add to .gitignore**: Ensure `credentials.json` is in `.gitignore`
- **Permissions**: Service account should only have Gmail send permission
- **Environment Variables**: Never hardcode credentials in code

## References

- [Gmail API Documentation](https://developers.google.com/gmail/api/guides)
- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [Service Account Authentication](https://developers.google.com/identity/protocols/oauth2/service-account)
- [Celery Documentation](https://docs.celeryq.dev/)
