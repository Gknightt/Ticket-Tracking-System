# Gmail API Migration Summary

## Overview
Successfully migrated all SMTP email functionality to Gmail API across the Ticket Tracking System. All emails are now sent through the `notification_service` microservice using Gmail API with header-based messaging.

## Changes Made

### 1. New Files Created

#### `notification_service/notifications/gmail_service.py`
- Core Gmail API service class
- Handles OAuth 2.0 service account authentication
- Provides methods for sending emails and emails with custom headers
- Singleton pattern for efficient resource usage

#### `notification_service/notifications/tasks.py`
- Celery tasks for async email sending
- Tasks created:
  - `send_email_via_gmail`: Generic email sending
  - `send_email_with_headers`: Header-based email (preferred method)
  - `send_password_reset_email`: Password reset emails
  - `send_invitation_email`: New user invitations
  - `send_otp_email`: OTP code delivery
  - `send_system_addition_email`: System access notifications

#### `GMAIL_API_MIGRATION.md`
- Comprehensive migration guide
- Setup instructions for Google Cloud service account
- Usage examples and troubleshooting guide
- Testing procedures and rollback instructions

#### `Scripts/setup_gmail_api.sh`
- Automated setup script for Gmail API integration
- Checks for credentials.json
- Updates .env configuration
- Installs dependencies

### 2. Modified Files

#### `notification_service/notifications/services.py`
**Changes:**
- Removed Django `send_mail()` import
- Added Gmail API service import
- Updated `send_notification()` method to use Gmail API instead of SMTP
- Added error handling and logging for Gmail API calls

#### `auth/notification_client.py`
**Changes:**
- Added Celery app initialization for task sending
- Added async email methods:
  - `send_password_reset_email_async()`
  - `send_invitation_email_async()`
  - `send_otp_email_async()`
  - `send_system_addition_email_async()`
- All methods enqueue tasks to `NOTIFICATION_TASKS` queue

#### `auth/users/serializers.py`
**Changes:**
- Replaced `send_otp_email()` function to use notification_client
- Replaced `send_password_reset_email()` function to use notification_client
- Removed direct SMTP `send_mail()` calls
- Removed threading logic (now handled by Celery)

#### `auth/system_roles/serializers.py`
**Changes:**
- Added notification_client import
- Replaced `send_invitation_email()` to use notification_client async method
- Replaced `send_system_addition_email()` to use notification_client async method
- Removed direct SMTP `send_mail()` calls

#### `notification_service/requirements.txt`
**Added:**
- `google-api-python-client==2.108.0`
- `google-auth-httplib2==0.2.0`
- `google-auth-oauthlib==1.2.0`

#### `notification_service/.env.example`
**Changes:**
- Added Gmail API configuration section
- Added `GMAIL_CREDENTIALS_PATH` variable
- Added `GMAIL_SENDER_EMAIL` variable
- Deprecated old SMTP settings (kept for reference)

#### `notification_service/notification_service/settings.py`
**Changes:**
- Added Gmail API configuration settings
- Added `GMAIL_CREDENTIALS_PATH` setting
- Added `GMAIL_SENDER_EMAIL` setting
- Updated Celery task routes to include Gmail API tasks
- All email tasks route to `NOTIFICATION_TASKS` queue

#### `.gitignore`
**Added:**
- `credentials.json` (all locations)
- `token.json` (all locations)
- Google Cloud credential file patterns

## Architecture Changes

### Before (SMTP)
```
┌─────────────┐
│ Auth Service│
│             │
│ send_mail() │──SMTP──> Gmail
│             │
└─────────────┘
```

### After (Gmail API)
```
┌─────────────┐      ┌──────────┐      ┌────────────────────┐      ┌──────┐
│ Auth Service│──>───│ RabbitMQ │──>───│ Notification Service│──>───│ Gmail│
│             │      │  Queue   │      │                    │      │  API │
│notification_│      │NOTIF_    │      │ gmail_service.py   │      │      │
│  client     │      │TASKS     │      │ Celery Worker      │      │      │
└─────────────┘      └──────────┘      └────────────────────┘      └──────┘
```

## Key Features

### 1. Header-Based Messaging
Emails can be sent with content in custom headers instead of templated bodies:

```python
headers = {
    'User_Name': 'John Doe',
    'Reset_URL': 'https://example.com/reset?token=abc123',
    'Expiry_Time': '1 hour',
    'Message': 'Please click the reset URL.'
}
```

### 2. Async Processing
All emails are sent via Celery tasks for non-blocking operations.

### 3. Centralized Logging
All emails logged in `NotificationLog` model with:
- Status (pending/sent/failed)
- Timestamps
- Error messages if any
- Context data

### 4. Better Security
- OAuth 2.0 service account authentication
- No passwords in configuration
- Domain-wide delegation support for G Suite

## Email Types Migrated

1. **Password Reset** - Forgot password flow
2. **User Invitation** - New user account creation with temp password
3. **OTP Codes** - 2FA authentication codes
4. **System Addition** - Adding existing user to new system
5. **Account Locked** - Security notifications (via NotificationService)
6. **Account Unlocked** - Security notifications (via NotificationService)
7. **Failed Login** - Security notifications (via NotificationService)

## Configuration Required

### Notification Service
```env
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_SENDER_EMAIL=your-email@gmail.com
DJANGO_DEFAULT_FROM_EMAIL=noreply@yourdomain.com
DJANGO_CELERY_BROKER_URL=amqp://admin:admin@localhost:5672/
```

### Auth Service
```env
DJANGO_CELERY_BROKER_URL=amqp://admin:admin@localhost:5672/
NOTIFICATION_SERVICE_URL=http://localhost:8001
```

## Setup Steps

1. **Create Google Cloud Service Account**
   - Enable Gmail API
   - Download `credentials.json`
   - Place in `notification_service/` directory

2. **Update Environment Variables**
   - Configure `GMAIL_CREDENTIALS_PATH`
   - Configure `GMAIL_SENDER_EMAIL`

3. **Install Dependencies**
   ```bash
   cd notification_service
   pip install -r requirements.txt
   ```

4. **Start Celery Worker**
   ```bash
   cd notification_service
   celery -A notification_service worker --pool=solo --loglevel=info -Q NOTIFICATION_TASKS,inapp-notification-queue
   ```

5. **Verify Setup**
   - Run Django shell test
   - Send test email
   - Check logs

## Testing

### Unit Test (Django Shell)
```python
from notifications.gmail_service import get_gmail_service

gmail = get_gmail_service()
success, msg_id, error = gmail.send_email(
    to_email='test@example.com',
    subject='Test Email',
    body_text='This is a test'
)
print(f"Success: {success}, ID: {msg_id}")
```

### Integration Test (Celery Task)
```python
from celery import Celery

app = Celery('test')
app.config_from_object('django.conf:settings', namespace='CELERY')

result = app.send_task(
    'notifications.send_email_with_headers',
    kwargs={
        'to_email': 'test@example.com',
        'subject': 'Test',
        'headers': {'Message': 'Test message'}
    },
    queue='NOTIFICATION_TASKS'
)
```

## Backward Compatibility

- SMTP settings retained in `.env.example` for reference
- Old email backend can be re-enabled by restoring original functions
- No database schema changes required
- NotificationLog model supports both methods

## Performance Improvements

- **Non-blocking**: Email sending doesn't block API responses
- **Retry Logic**: Celery handles automatic retries
- **Logging**: All emails tracked with detailed status
- **Scalability**: Can add more Celery workers as needed

## Security Improvements

- **OAuth 2.0**: Service account authentication instead of passwords
- **No Credentials in Code**: All credentials in environment variables
- **Domain Control**: G Suite domain-wide delegation for access control
- **Audit Trail**: Complete email history in database

## Known Limitations

1. **Gmail API Rate Limits**: 
   - 1 billion messages per day per project
   - 20,000 messages per day per user
   
2. **Service Account Setup**: 
   - Requires Google Cloud Console access
   - Domain admin for G Suite delegation

3. **Celery Dependency**: 
   - Requires RabbitMQ or Redis running
   - Worker must be active for email delivery

## Rollback Procedure

If issues occur, rollback by:

1. Restore old functions in `users/serializers.py` and `system_roles/serializers.py`
2. Comment out Gmail task routes in settings
3. Switch back to SMTP backend in `.env`
4. Restart services

## Documentation

- **Main Guide**: `GMAIL_API_MIGRATION.md`
- **Google Docs**: https://developers.google.com/gmail/api/guides
- **Setup Script**: `Scripts/setup_gmail_api.sh`

## Success Criteria

✅ All SMTP functions migrated to Gmail API
✅ Forgot password emails sent via notification_service
✅ Invitation emails sent via notification_service
✅ OTP emails sent via notification_service
✅ System addition emails sent via notification_service
✅ Header-based messaging implemented
✅ Celery tasks created and configured
✅ Requirements updated
✅ Environment configuration updated
✅ Documentation created
✅ Setup script created
✅ .gitignore updated for credentials

## Next Steps

1. Test in development environment
2. Verify email delivery end-to-end
3. Monitor Celery worker logs
4. Check NotificationLog for status
5. Deploy to staging for testing
6. Update production credentials
7. Roll out to production

## Support

For issues or questions:
- Review `GMAIL_API_MIGRATION.md`
- Check Celery logs
- Verify Gmail API quota
- Check service account permissions
