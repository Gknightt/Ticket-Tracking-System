# Notification Microservice

A standalone Django microservice for handling email notifications from the authentication system. This service operates independently with its own database and provides a REST API for sending notifications.

## 🚀 Features

- **Separate Microservice**: Runs independently from the auth service with its own database
- **REST API**: HTTP endpoints for sending notifications and managing templates
- **Email Templates**: Configurable email templates with variable substitution
- **Notification Logging**: Track all sent notifications with status and error tracking
- **Health Monitoring**: Health check endpoints for service monitoring
- **Docker Support**: Containerized deployment ready
- **Admin Interface**: Django admin for managing templates and viewing logs

## 📋 API Endpoints

### Core Endpoints
- `POST /api/v1/notifications/send/` - Send a notification
- `GET /api/v1/notifications/history/` - Get notification history
- `GET /api/v1/notifications/health/` - Health check
- `GET /api/v1/notifications/types/` - Get available notification types

### Template Management
- `GET /api/v1/notifications/templates/` - List templates
- `POST /api/v1/notifications/templates/` - Create template
- `GET /api/v1/notifications/templates/{id}/` - Get template
- `PUT /api/v1/notifications/templates/{id}/` - Update template
- `DELETE /api/v1/notifications/templates/{id}/` - Delete template

### Logs
- `GET /api/v1/notifications/logs/` - View notification logs

## 🛠️ Installation & Setup

### 1. Environment Setup

Copy the environment file and configure it:
```bash
cd notification_service
cp .env.example .env
```

Edit `.env` with your settings:
```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@notifications.com

# Service Settings
NOTIFICATION_SERVICE_PORT=8001
AUTH_SERVICE_URL=http://localhost:8000
```

### 2. Development Setup

Using virtual environment:
```bash
# Activate virtual environment
source ../venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Setup default templates
python manage.py setup_notification_templates

# Create admin user (optional)
python manage.py createsuperuser

# Start the service
python manage.py runserver 8001
```

### 3. Docker Setup

```bash
# Build the image
docker build -t notification-service .

# Run the container
docker run -p 8001:8001 --env-file .env notification-service
```

## 🔧 Configuration

### Auth Service Integration

Update your auth service settings (in `auth/auth/settings.py`):

```python
# Notification Settings
NOTIFICATIONS_ENABLED = config('NOTIFICATIONS_ENABLED', default=True, cast=bool)
NOTIFICATION_SERVICE_URL = config('NOTIFICATION_SERVICE_URL', default='http://localhost:8001')
NOTIFICATION_SERVICE_TIMEOUT = config('NOTIFICATION_SERVICE_TIMEOUT', default=10, cast=int)
```

Add to your auth service `.env`:
```env
NOTIFICATIONS_ENABLED=True
NOTIFICATION_SERVICE_URL=http://localhost:8001
NOTIFICATION_SERVICE_TIMEOUT=10
```

### Email Configuration

For development (console output):
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

For production (Gmail example):
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourapp.com
```

## 📧 Notification Types

The service supports these notification types out of the box:

- `account_locked` - When user account is locked due to failed login attempts
- `account_unlocked` - When user account is unlocked
- `failed_login_attempt` - When failed login attempts occur
- `password_reset` - When password reset is requested
- `account_created` - When new account is created
- `login_success` - When successful login occurs

## 🔌 API Usage Examples

### Send Notification

```bash
curl -X POST http://localhost:8001/api/v1/notifications/send/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_email": "user@example.com",
    "user_name": "John Doe",
    "notification_type": "account_locked",
    "context_data": {
      "failed_attempts": 5,
      "lockout_duration": "15 minutes"
    },
    "ip_address": "192.168.1.1"
  }'
```

### Get Notification History

```bash
curl "http://localhost:8001/api/v1/notifications/history/?user_email=user@example.com&limit=10"
```

### Health Check

```bash
curl http://localhost:8001/api/v1/notifications/health/
```

## 🎯 Template Variables

Email templates support these variables:

- `{{ user_name }}` - User's full name or username
- `{{ user_email }}` - User's email address
- `{{ timestamp }}` - Current timestamp
- `{{ failed_attempts }}` - Number of failed login attempts
- `{{ lockout_duration }}` - Account lockout duration
- `{{ ip_address }}` - User's IP address

## 🏥 Monitoring

### Health Check
The service provides a health check endpoint at `/api/v1/notifications/health/` that returns:
- Service status
- Database connectivity
- Email backend configuration
- Service version

### Logging
All notifications are logged with:
- User information
- Notification type and content
- Send status (pending/sent/failed)
- Error messages (if any)
- Timestamps

### Admin Interface
Access the Django admin at `http://localhost:8001/admin/` to:
- Manage notification templates
- View notification logs
- Monitor service health

## 🔒 Security Considerations

- The service currently has no authentication on API endpoints (designed for internal microservice communication)
- Add API authentication if exposing to external networks
- Use environment variables for sensitive configuration
- Monitor notification logs for unusual activity

## 🐛 Troubleshooting

### Common Issues

1. **Service not starting**: Check if port 8001 is available
2. **Email not sending**: Verify email configuration in `.env`
3. **Template not found**: Run `python manage.py setup_notification_templates`
4. **Database errors**: Run migrations with `python manage.py migrate`

### Logs
Check Django logs for detailed error information:
```bash
python manage.py runserver 8001 --verbosity=2
```

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in production
- [ ] Configure proper `SECRET_KEY`
- [ ] Set up email backend (SMTP)
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up monitoring and logging
- [ ] Configure database (PostgreSQL recommended)
- [ ] Set up reverse proxy (nginx)

### Docker Compose Example
```yaml
version: '3.8'
services:
  notification-service:
    build: .
    ports:
      - "8001:8001"
    environment:
      - SECRET_KEY=your-secret-key
      - DEBUG=False
      - EMAIL_HOST=smtp.gmail.com
    volumes:
      - ./data:/app/data
```

## 📝 License

This notification microservice is part of the Authentication-and-Authorization project.