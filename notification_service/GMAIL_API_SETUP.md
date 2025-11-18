# Gmail API Setup Guide for Notification Service

This guide will help you set up Gmail API for sending emails in the TTS Notification Service.

## 🎯 Why Gmail API?

- **For Testing/Capstone Projects**: Gmail API is perfect for demonstration and testing
- **No SMTP Port Blocking**: Works on Railway and other cloud platforms that block SMTP ports
- **Free**: 250 emails/day (free Gmail) or 2000/day (Google Workspace)
- **Easy to Switch**: Architecture supports switching to SendGrid/Mailgun for production

## 📋 Prerequisites

- Google Account (Gmail)
- Access to Google Cloud Console
- Python 3.8+

## 🚀 Setup Steps

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project" or select existing project
3. Name it (e.g., "TTS-Notifications")
4. Click "Create"

### Step 2: Enable Gmail API

1. In Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on "Gmail API"
4. Click "Enable"

### Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: **External** (for testing)
   - App name: "TTS Notification Service"
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Skip (default is fine)
   - Test users: Add your email
   - Click "Save and Continue"
4. Create OAuth Client ID:
   - Application type: **Desktop app**
   - Name: "TTS Notification Desktop"
   - Click "Create"
5. **Download the JSON file**
6. Rename it to `credentials.json`
7. Place it in the `notification_service/` folder

### Step 4: Install Dependencies

```bash
cd notification_service
pip install -r requirements.txt
```

### Step 5: Authenticate (First Time Only)

```bash
# Run the test script - this will open your browser for OAuth
python test_gmail_api.py
```

**What happens:**
1. Browser opens automatically
2. Sign in with your Gmail account
3. Grant permissions to the app
4. Token is saved to `token.pickle` (this file persists your authentication)

**When prompted, enter your email to send test emails or press Enter to skip**

### Step 6: Verify Setup

After authentication, the test script will:
- ✅ Test connection
- ✅ Send a simple test email
- ✅ Send a password reset email template
- ✅ Send a ticket notification email template

## 📝 Environment Configuration

Update your `.env` file:

```bash
# Email Provider
EMAIL_PROVIDER=gmail

# No additional config needed for Gmail API!
# credentials.json and token.pickle handle authentication
```

## 🔧 Usage

### In Your Code

```python
from notifications.email_service import get_email_service

# Get email service (auto-loads Gmail API)
email_service = get_email_service()

# Send password reset email
result = email_service.send_password_reset_email(
    to='user@example.com',
    reset_url='https://your-app.com/reset?token=abc123',
    user_name='John Doe'
)

# Send ticket notification
result = email_service.send_ticket_notification(
    to='user@example.com',
    ticket_id='12345',
    ticket_title='Login Issue',
    action='created',
    user_name='John Doe',
    ticket_url='https://your-app.com/tickets/12345'
)

# Send custom email
result = email_service.send_email(
    to='user@example.com',
    subject='Test Email',
    body_text='Plain text version',
    body_html='<h1>HTML version</h1>'
)
```

### Via API Endpoints

#### Password Reset Email
```bash
curl -X POST http://localhost:8001/api/v2/email/password-reset/ \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_email": "user@example.com",
    "reset_url": "https://your-app.com/reset?token=abc123",
    "user_name": "John Doe"
  }'
```

#### Ticket Notification
```bash
curl -X POST http://localhost:8001/api/v2/email/ticket-notification/ \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_email": "user@example.com",
    "ticket_id": "12345",
    "ticket_title": "Cannot login",
    "action": "created",
    "user_name": "John Doe",
    "ticket_url": "https://your-app.com/tickets/12345"
  }'
```

#### Check Email Service Status
```bash
curl http://localhost:8001/api/v2/email/status/ \
  -H "X-API-Key: your-api-key"
```

## 🔄 Integration with Auth Service

Update your auth service to call the notification service:

```python
import requests

def send_password_reset_email(user_email, reset_url):
    try:
        response = requests.post(
            'http://localhost:8001/api/v2/email/password-reset/',
            headers={
                'X-API-Key': 'your-api-key',
                'Content-Type': 'application/json'
            },
            json={
                'recipient_email': user_email,
                'reset_url': reset_url,
                'user_name': user.get_full_name()
            },
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
```

## 📊 Gmail API Quotas

- **Free Gmail**: 250 emails per day
- **Google Workspace**: 2,000 emails per day
- **Quota Units**: 10 units per message sent

Check your quota usage: [Gmail API Quotas](https://console.cloud.google.com/apis/api/gmail.googleapis.com/quotas)

## 🚨 Troubleshooting

### "credentials.json not found"
- Make sure `credentials.json` is in the `notification_service/` folder
- Download it again from Google Cloud Console if needed

### "Token refresh failed"
- Delete `token.pickle`
- Run `python test_gmail_api.py` again to re-authenticate

### "Quota exceeded"
- You've hit the daily limit (250 or 2000 emails)
- Wait until midnight PST (Google's reset time)
- Or switch to SendGrid for production

### "Network is unreachable" on Railway
- This shouldn't happen with Gmail API (unlike SMTP)
- Check that credentials.json is uploaded to Railway
- Make sure token.pickle is generated (run test locally first)

## 🔐 Security Best Practices

1. **Never commit credentials.json or token.pickle to git** (already in .gitignore)
2. **Keep your API keys secure** (use Railway environment variables)
3. **Use test users** in OAuth consent screen during development
4. **Switch to verified app** when going to production

## 🎓 For Capstone Presentation

You can explain:
- ✅ "Implemented Gmail API with OAuth2 for secure email delivery"
- ✅ "Designed hybrid architecture supporting multiple email providers"
- ✅ "Centralized email logic in dedicated microservice"
- ✅ "Used token-based authentication for Railway deployment"
- ✅ "Scalable design: easy to switch to SendGrid for production"

## 🚀 Switching to SendGrid (Future)

When ready for production, simply:

1. Sign up for SendGrid
2. Get API key
3. Add to `.env`:
   ```bash
   EMAIL_PROVIDER=sendgrid
   SENDGRID_API_KEY=your-api-key
   ```
4. No code changes needed!

## 📚 Resources

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [OAuth 2.0 Setup](https://developers.google.com/identity/protocols/oauth2)
- [Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)

## 💡 Tips

- **Test locally first** before deploying to Railway
- **Save token.pickle** securely (contains your auth)
- **Monitor quota usage** in Google Cloud Console
- **Use test email addresses** during development

---

Need help? Check the [API_V2_README.md](API_V2_README.md) for API endpoint documentation.
