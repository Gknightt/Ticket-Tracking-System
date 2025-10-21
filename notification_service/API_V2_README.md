# Notification Service v2 API

## Overview

The Notification Service v2 provides simplified email functionality with API key authentication, following the same simple pattern as the messaging service. Just **send** and **fetch** - that's it!

## Authentication

All v2 endpoints require API key authentication. Include your API key in one of these ways:

### Option 1: X-API-Key Header
```bash
curl -H "X-API-Key: your-api-key-here" \
     -H "Content-Type: application/json" \
     http://localhost:8001/api/v2/health/
```

### Option 2: Authorization Header
```bash
curl -H "Authorization: Bearer your-api-key-here" \
     -H "Content-Type: application/json" \
     http://localhost:8001/api/v2/health/
```

## API Endpoints

### 1. Send Template-Based Notification
**POST** `/api/v2/send/`

Send notifications using predefined templates with individual form fields.

```bash
curl -X POST \
  -H "X-API-Key: demo-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "user@example.com",
    "user_name": "John Doe",
    "notification_type": "password_reset",
    "reset_token": "abc123xyz789",
    "reset_url": "https://example.com/reset/token123",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  }' \
  http://localhost:8001/api/v2/send/
```

**Required fields:**
- `user_email`: Recipient's email address
- `notification_type`: Type of notification (password_reset, account_locked, login_success, etc.)

**Optional context fields:**
- `user_name`: User's full name
- `ip_address`: IP address for security notifications
- `user_agent`: Browser/device information
- `failed_attempts`: Number of failed login attempts
- `reset_token`: Password reset token
- `reset_url`: Complete reset URL
- `otp_code`: OTP verification code
- `login_timestamp`: Login time for alerts
- `previous_email`: Previous email for profile updates
- `previous_username`: Previous username for profile updates
- `device_info`: Device information
- `location`: Geographic location
- `additional_message`: Extra context message

### 2. Send Flexible Email
**POST** `/api/v2/send-email/`

Send custom emails with your own subject and content.

```bash
curl -X POST \
  -H "X-API-Key: demo-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_email": "user@example.com",
    "subject": "Welcome to our service!",
    "message": "Thank you for signing up. We are excited to have you on board!",
    "html_message": "<h1>Welcome!</h1><p>Thank you for signing up.</p>",
    "priority": "normal",
    "send_immediately": true
  }' \
  http://localhost:8001/api/v2/send-email/
```

**Required fields:**
- `recipient_email`: Email address to send to
- `subject`: Email subject line

**Optional fields:**
- `message`: Plain text email body
- `html_message`: HTML email body

- `priority`: Email priority (low, normal, high)
- `send_immediately`: Whether to send immediately (true/false)

### 3. Fetch Notifications
**POST** `/api/v2/fetch/`

Retrieve notification history, optionally filtering after a specific notification ID.

```bash
curl -X POST \
  -H "X-API-Key: demo-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "user@example.com",
    "limit": 10,
    "notification_type": "password_reset",
    "after_notification_id": "notification-uuid-here"
  }' \
  http://localhost:8001/api/v2/fetch/
```

Required fields:
- `user_email`: Email address to filter notifications for

Optional fields:
- `notification_type`: Filter by notification type
- `limit`: Number of records to return (default: 50)
- `after_notification_id`: Get notifications after this ID

### 4. Health Check
**GET** `/api/v2/health/`

Check service health and status.

```bash
curl -H "X-API-Key: demo-api-key-123" \
     http://localhost:8001/api/v2/health/
```

### 5. Notification Types
**GET** `/api/v2/types/`

Get available notification types.

```bash
curl -H "X-API-Key: demo-api-key-123" \
     http://localhost:8001/api/v2/types/
```

## Comparison with Messaging Service

| Messaging Service | Notification Service v2 |
|------------------|-------------------------|
| `POST /send/` | `POST /send/` (template-based) |
| `POST /fetch/` | `POST /fetch/` |
| Send messages to tickets | Send template notifications |
| Fetch messages from tickets | Fetch notification history |
| | `POST /send-email/` (flexible) |

## Endpoint Differences

### `/api/v2/send/` - Template-Based Notifications
- Uses predefined notification templates
- Requires `notification_type` to select template
- Individual form fields for better DRF browsable API experience
- Context data passed as separate fields (not JSON)
- Integrated with notification templates in database
- Returns `"type": "template_based"`

### `/api/v2/send-email/` - Flexible Emails  
- Custom email content (you provide subject and message)
- No templates required

- Priority and scheduling options
- Individual form fields for HTML forms
- Returns `"type": "flexible_email"`

## Response Format

### Template-Based Send Response
```json
{
  "success": true,
  "message": "Notification sent successfully",
  "notification_id": "uuid-here",
  "type": "template_based"
}
```

### Flexible Email Send Response
```json
{
  "success": true,
  "message": "Email sent successfully",
  "notification_id": "uuid-here",
  "type": "flexible_email"
}
```

### Fetch Response
```json
{
  "user_email": "user@example.com",
  "notifications": [
    {
      "id": "notification-uuid",
      "notification_type": "password_reset",
      "subject": "Password Reset Request",
      "message": "Click the link to reset...",
      "status": "sent",
      "created_at": "2025-10-09T10:30:00Z"
    }
  ],
  "count": 1
}
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# API Key Authentication for v2 endpoints (comma-separated list)
NOTIFICATION_API_KEYS=demo-api-key-123,test-api-key-456,your-secure-api-key
```

## Key Features

✅ **Two Specialized Endpoints**: `/send/` for templates and `/send-email/` for flexible content  
✅ **Individual Form Fields**: Better DRF browsable API experience instead of JSON blobs  
✅ **API Key Auth**: Simple, secure authentication  
✅ **Template-Based Notifications**: Predefined templates for consistent messaging  
✅ **Flexible Content**: Custom emails without predefined templates  
✅ **Custom Sender**: Specify `from_email` for different departments/purposes  
✅ **History Tracking**: Fetch notification history with filtering

## NOTE

- `/send/` endpoint uses predefined templates and saves notification requests  
- `/send-email/` endpoint sends flexible emails directly  
- Both endpoints store notification logs for history tracking  
- `/fetch/` endpoint is read-only for debugging and history retrieval  
- Celery integration planned for asynchronous processing