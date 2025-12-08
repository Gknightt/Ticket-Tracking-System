# SendGrid Email Migration Guide

## Overview

The authentication service has been refactored to use **SendGrid** instead of Gmail API for sending emails. All email functionality is now handled locally within the `auth/emails` app.

## What Changed

### Before (Gmail API)
- Email sending was handled by a separate `notification_service` microservice
- Used Gmail API with OAuth2 authentication
- Required complex Gmail API credentials and token management
- Emails were sent via Celery tasks to external notification service

### After (SendGrid)
- Email sending is handled directly in the `auth/emails` app
- Uses SendGrid API (simple API key authentication)
- All email templates and tracking are local to auth service
- No external notification service dependency for basic emails

## Setup Instructions

### 1. Get SendGrid API Key

1. Sign up for a free SendGrid account at https://sendgrid.com/
2. Navigate to **Settings > API Keys**
3. Create a new API key with **Mail Send** permissions
4. Copy the API key (you'll only see it once!)

### 2. Configure Environment Variables

Add the following to your `auth/.env` file:

```bash
# SendGrid Configuration
SENDGRID_API_KEY=SG.your_actual_api_key_here
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_ENABLED=True
```

**Important Notes:**
- Replace `noreply@yourdomain.com` with your verified sender email
- You need to verify your sender identity in SendGrid dashboard
- For testing, you can use SendGrid's sandbox mode

### 3. Install Dependencies

```bash
cd /workspaces/Ticket-Tracking-System/auth
pip install -r requirements.txt
```

This will install `sendgrid>=6.11.0` along with other dependencies.

### 4. Run Migrations

Create and apply the new email tracking models:

```bash
python manage.py makemigrations emails
python manage.py migrate
```

### 5. Seed Email Templates

Load the HTML email templates into the database:

```bash
python manage.py seed_email_templates
```

This creates the following templates:
- `password_reset` - Password reset with link
- `otp` - OTP verification code
- `account_locked` - Account lockout notification
- `account_unlocked` - Account unlock notification
- `failed_login` - Failed login attempt alert

### 6. Verify Setup

Test the email service with Django shell:

```python
from emails.services import get_sendgrid_service
from django.contrib.auth import get_user_model

User = get_user_model()
service = get_sendgrid_service()

# Test sending an email
success, message_id, error = service.send_email(
    to_email='test@example.com',
    subject='Test Email',
    html_content='<h1>Hello from SendGrid!</h1>',
    email_type='general'
)

print(f"Success: {success}, Message ID: {message_id}, Error: {error}")
```

## Email Templates

### Available Templates

All templates are located in `auth/emails/templates/emails/`:

1. **password_reset.html** - Sent when user requests password reset
2. **otp.html** - Sent with OTP verification code
3. **account_locked.html** - Sent when account is locked due to failed attempts
4. **account_unlocked.html** - Sent when account is automatically unlocked
5. **failed_login.html** - Sent after multiple failed login attempts

### Customizing Templates

Templates use Django template syntax and support variables:

```html
<!-- Example variables in password_reset.html -->
{{ user_name }}      - User's full name
{{ reset_url }}      - Password reset URL
{{ expiry_time }}    - Token expiration time
{{ timestamp }}      - Current timestamp
```

To customize:
1. Edit the HTML files in `auth/emails/templates/emails/`
2. Run `python manage.py seed_email_templates` to update the database
3. Or edit directly in Django admin at `/admin/emails/emailtemplate/`

## Email Tracking

All sent emails are tracked in the `EmailLog` model:

### Viewing Email Logs

**Django Admin:**
```
http://localhost:8000/admin/emails/emaillog/
```

**Programmatically:**
```python
from emails.models import EmailLog

# Get recent emails
recent = EmailLog.objects.all()[:10]

# Get emails for specific user
user_emails = EmailLog.objects.filter(user_email='user@example.com')

# Get failed emails
failed = EmailLog.objects.filter(status='failed')
```

### Email Statuses

- `pending` - Email queued but not sent yet
- `sent` - Successfully sent to SendGrid
- `delivered` - Confirmed delivered (via webhooks)
- `failed` - Failed to send
- `bounced` - Email bounced (via webhooks)
- `dropped` - Dropped by SendGrid (via webhooks)

## Usage in Code

### Password Reset Email

```python
from notification_client import notification_client

# In your view
success = notification_client.send_password_reset_email_async(
    user=user,
    reset_token=reset_token,
    request=request
)
```

### OTP Email

```python
success = notification_client.send_otp_email_async(
    user=user,
    otp_code='123456'
)
```

### Account Locked Email

```python
success = notification_client.send_account_locked_notification(
    user=user,
    failed_attempts=10,
    lockout_duration='15 minutes',
    ip_address=request.META.get('REMOTE_ADDR')
)
```

## Testing Without SendGrid

For development/testing without a SendGrid account:

### Option 1: Console Backend

Set in `.env`:
```bash
SENDGRID_ENABLED=False
```

Emails will print to console instead.

### Option 2: File Backend

In `auth/settings.py`:
```python
if not SENDGRID_API_KEY and DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'tmp_emails')
```

Emails will be saved as files in `auth/tmp_emails/`.

## SendGrid Dashboard Features

### Verify Sender Identity

Before sending emails, verify your sender:

1. Go to **Settings > Sender Authentication**
2. Choose **Single Sender Verification** (free) or **Domain Authentication** (production)
3. Follow the verification steps

### Monitor Email Activity

- **Activity Feed**: See real-time email events
- **Statistics**: View delivery rates, bounces, spam reports
- **Suppressions**: Manage bounce/block lists

### Webhooks (Optional)

To update email status automatically:

1. Go to **Settings > Mail Settings > Event Webhook**
2. Set webhook URL: `https://yourdomain.com/api/v1/emails/webhook/`
3. Select events: Delivered, Bounced, Dropped, etc.

## Migration from notification_service

### What's Removed

The following are **no longer used** for basic emails:
- `notification_service/` microservice
- Celery tasks in notification_service
- Gmail API credentials
- RabbitMQ queues for notification tasks

### What Still Uses notification_service (if needed)

If you have other notification types beyond email:
- In-app notifications
- Push notifications
- SMS notifications

These would still require the notification_service or a separate implementation.

## Troubleshooting

### "SendGrid client not initialized"

**Cause:** Missing or invalid API key

**Fix:**
1. Check `SENDGRID_API_KEY` in `.env`
2. Verify API key is valid in SendGrid dashboard
3. Ensure key has "Mail Send" permissions

### "sender email not verified"

**Cause:** Sender email not verified in SendGrid

**Fix:**
1. Go to SendGrid **Settings > Sender Authentication**
2. Verify your sender email or domain
3. Use the verified email in `SENDGRID_FROM_EMAIL`

### Emails not being sent

**Check:**
1. `SENDGRID_ENABLED=True` in `.env`
2. Check `EmailLog` in admin for error messages
3. Verify SendGrid API key permissions
4. Check SendGrid activity feed for blocks/bounces

### Template not found

**Fix:**
```bash
python manage.py seed_email_templates
```

Or create templates manually in Django admin.

## Production Checklist

- [ ] Get production SendGrid API key
- [ ] Verify sender domain (not single email)
- [ ] Set `SENDGRID_FROM_EMAIL` to your domain
- [ ] Enable SendGrid webhooks for status tracking
- [ ] Monitor SendGrid activity dashboard
- [ ] Set up email suppression handling
- [ ] Configure SendGrid IP warmup (if high volume)
- [ ] Test all email flows in staging
- [ ] Set up alerts for failed emails

## Support

For issues:
- SendGrid docs: https://docs.sendgrid.com/
- SendGrid support: https://support.sendgrid.com/
- Check Django logs: `docker logs auth-service` or console output

---

**Migration completed on:** December 8, 2025  
**Previous system:** Gmail API via notification_service  
**New system:** SendGrid via auth/emails app
