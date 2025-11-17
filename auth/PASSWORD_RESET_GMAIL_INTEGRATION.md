# Password Reset Gmail API Integration

This document explains how the password reset feature in the auth service is integrated with the notification service to use Gmail API for sending password reset emails.

## Overview

The password reset flow now uses the notification service with Gmail API instead of traditional SMTP, providing:
- Better email deliverability
- HTML email templates
- Email tracking and logging
- Centralized email management

## Architecture

```
┌─────────────────┐
│   Auth Service  │
│  (Port 8000)    │
│                 │
│  - User requests│
│    password     │
│    reset        │
│  - Generates    │
│    reset token  │
│  - Calls notif  │
│    service API  │
└────────┬────────┘
         │
         │ HTTP POST /api/v2/send/
         │ X-API-Key: xxx
         │
         ▼
┌─────────────────┐
│ Notification    │
│ Service         │
│ (Port 8001)     │
│                 │
│ - Receives req  │
│ - Renders HTML  │
│   template      │
│ - Sends via     │
│   Gmail API     │
└─────────────────┘
```

## Configuration

### 1. Auth Service Configuration

Add to `/auth/.env`:

```bash
# Notification Service Configuration
NOTIFICATION_SERVICE_URL=http://localhost:8001
NOTIFICATION_SERVICE_API_KEY=your-api-key-here
NOTIFICATION_SERVICE_TIMEOUT=10
NOTIFICATIONS_ENABLED=True

# Auth Service URL (used in reset links)
AUTH_SERVICE_URL=http://localhost:8000
```

For production (Railway/Docker):
```bash
NOTIFICATION_SERVICE_URL=http://notification-service:8001
AUTH_SERVICE_URL=https://your-auth-domain.railway.app
```

### 2. Notification Service Configuration

The notification service must have Gmail API configured. Follow the setup guide in:
- `/notification_service/GMAIL_API_SETUP.md`

Ensure these are set in `/notification_service/.env`:
```bash
EMAIL_PROVIDER=gmail
# Gmail API credentials should be in credentials.json
```

### 3. Setup Password Reset Template

Run this command in the notification service to create/update the password reset email template:

```bash
cd notification_service
python manage.py setup_notification_templates
```

This will create a beautiful HTML email template with:
- Professional styling
- Reset button
- Fallback link
- Security notice
- Expiration warning

## How It Works

### 1. User Requests Password Reset

**UI Route**: `/forgot-password` (renders HTML form)
**API Route**: `POST /api/v1/users/password/forgot/`

```json
{
  "email": "user@example.com"
}
```

### 2. Auth Service Generates Token

The auth service:
1. Validates the email exists
2. Creates a password reset token (expires in 1 hour)
3. Builds the reset URL: `{AUTH_SERVICE_URL}/api/v1/users/password/reset?token={token}`

### 3. Auth Service Calls Notification Service

Using the `notification_client.send_password_reset_email_v2()` method:

```python
POST http://notification-service:8001/api/v2/send/
Headers:
  X-API-Key: your-api-key
  Content-Type: application/json

Body:
{
  "user_email": "user@example.com",
  "user_name": "John Doe",
  "notification_type": "password_reset",
  "context_data": {
    "reset_url": "http://localhost:8000/api/v1/users/password/reset?token=abc123",
    "reset_token": "abc123",
    "user_email": "user@example.com"
  }
}
```

### 4. Notification Service Sends Email

The notification service:
1. Retrieves the `password_reset` template from database
2. Renders the HTML with context data (reset_url, user_name, etc.)
3. Sends email via Gmail API
4. Logs the result in `NotificationLog` table

### 5. User Clicks Reset Link

The link directs to: `{AUTH_SERVICE_URL}/api/v1/users/password/reset?token={token}`

User can then set a new password.

## Email Template

The password reset email includes:

```html
<!DOCTYPE html>
<html>
<!-- Professional HTML email with: -->
- Header with blue background
- Welcome message with user name
- "Reset Password" button
- Fallback link (if button doesn't work)
- Security warning (1 hour expiration)
- Footer with disclaimer
- Mobile responsive design
```

Preview the template by checking:
- `/notification_service/notifications/management/commands/setup_notification_templates.py`

## Testing

### Test End-to-End Flow

1. **Start both services**:
   ```bash
   # Terminal 1 - Auth service
   cd auth
   python manage.py runserver 8000
   
   # Terminal 2 - Notification service
   cd notification_service
   python manage.py runserver 8001
   ```

2. **Test via UI**:
   - Navigate to: http://localhost:8000/forgot-password
   - Enter your email
   - Check Gmail inbox for reset email

3. **Test via API**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/users/password/forgot/ \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com"}'
   ```

### Check Notification Logs

View sent emails in the notification service:

```bash
cd notification_service
python manage.py shell
```

```python
from notifications.models import NotificationLog

# View recent password reset emails
logs = NotificationLog.objects.filter(
    notification_type='password_reset'
).order_by('-created_at')[:5]

for log in logs:
    print(f"{log.recipient_email} - {log.status} - {log.sent_at}")
```

## Security Features

1. **Token Expiration**: Reset tokens expire after 1 hour
2. **One-time Use**: Tokens are invalidated after use
3. **No Email Enumeration**: Same success message whether email exists or not
4. **API Key Authentication**: Secure communication between services
5. **Audit Trail**: All emails logged in `NotificationLog`

## Troubleshooting

### Email Not Sending

**Check notification service logs**:
```bash
cd notification_service
tail -f logs/notification.log
```

**Verify Gmail API is working**:
```bash
cd notification_service
python test_gmail_api.py
```

### Auth Service Can't Connect to Notification Service

**Check environment variables**:
```bash
cd auth
python manage.py shell
```
```python
from django.conf import settings
print(settings.NOTIFICATION_SERVICE_URL)
print(settings.NOTIFICATION_SERVICE_API_KEY)
```

**Test connection**:
```bash
curl http://localhost:8001/api/v2/health/
```

### Template Not Found

**Re-run template setup**:
```bash
cd notification_service
python manage.py setup_notification_templates
```

**Verify template exists**:
```bash
python manage.py shell
```
```python
from notifications.models import NotificationTemplate
template = NotificationTemplate.objects.get(notification_type='password_reset')
print(template.subject)
print(template.is_active)
```

## Production Deployment

### Railway Deployment

1. **Set environment variables in Railway dashboard**:
   
   Auth Service:
   ```
   NOTIFICATION_SERVICE_URL=http://notification-service:8001
   NOTIFICATION_SERVICE_API_KEY=<generate-secure-key>
   AUTH_SERVICE_URL=https://your-auth-service.railway.app
   ```
   
   Notification Service:
   ```
   EMAIL_PROVIDER=gmail
   # Upload credentials.json via Railway files
   ```

2. **Ensure services can communicate**:
   - Both services must be in the same Railway project
   - Use internal service names for URLs

3. **Run migrations and setup**:
   ```bash
   # In notification service
   python manage.py migrate
   python manage.py setup_notification_templates
   ```

## API Reference

### Auth Service

#### Request Password Reset
```http
POST /api/v1/users/password/forgot/
Content-Type: application/json

{
  "email": "user@example.com"
}

Response: 200 OK
{
  "message": "If an account with that email exists, a password reset link has been sent."
}
```

#### Reset Password with Token
```http
POST /api/v1/users/password/reset?token={token}
Content-Type: application/json

{
  "new_password": "NewSecurePassword123!",
  "new_password_confirm": "NewSecurePassword123!"
}

Response: 200 OK
{
  "message": "Password reset successfully"
}
```

### Notification Service

#### Send Notification (used by auth service)
```http
POST /api/v2/send/
X-API-Key: your-api-key
Content-Type: application/json

{
  "user_email": "user@example.com",
  "user_name": "John Doe",
  "notification_type": "password_reset",
  "context_data": {
    "reset_url": "https://auth.example.com/reset?token=abc123",
    "reset_token": "abc123"
  }
}

Response: 201 Created
{
  "success": true,
  "message": "Notification sent successfully",
  "notification_id": "uuid-here",
  "type": "password_reset"
}
```

## Benefits of This Integration

1. **Centralized Email Management**: All emails sent from one service
2. **Better Deliverability**: Gmail API has better delivery rates than SMTP
3. **HTML Email Support**: Professional, branded emails
4. **Tracking**: Know when emails are sent/failed
5. **Scalability**: Easy to add more notification types
6. **Separation of Concerns**: Auth focuses on auth, notifications on emails
7. **Future-proof**: Can switch to SendGrid/other providers without changing auth service

## Related Files

### Auth Service
- `/auth/notification_client.py` - Client for calling notification service
- `/auth/users/serializers.py` - Contains `send_password_reset_email()` function
- `/auth/users/views.py` - `ForgotPasswordView` and `ForgotPasswordUIView`
- `/auth/templates/users/forgot_password.html` - Password reset form UI

### Notification Service
- `/notification_service/notifications/views_v2.py` - API endpoints
- `/notification_service/notifications/services.py` - Email sending logic
- `/notification_service/notifications/email_service.py` - Gmail API integration
- `/notification_service/notifications/models.py` - Template and log models
- `/notification_service/notifications/management/commands/setup_notification_templates.py` - Template setup

## Next Steps

Consider extending this for:
- [ ] Account creation emails
- [ ] Password changed confirmation
- [ ] Login alerts
- [ ] Profile update notifications
- [ ] System invitation emails

All can follow the same pattern!
