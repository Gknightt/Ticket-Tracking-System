"""
Email Service - Hybrid approach supporting multiple providers
Supports Gmail API (for testing) and can be extended for SendGrid (production)
"""
import os
from decouple import config
from .gmail_backend import GmailBackend


class EmailService:
    """
    Unified email service that supports multiple providers.
    Switch providers via EMAIL_PROVIDER environment variable.
    """
    
    def __init__(self):
        self.provider = config('EMAIL_PROVIDER', default='gmail')
        self.backend = None
        
        if self.provider == 'gmail':
            self.backend = GmailBackend()
            try:
                self.backend.authenticate()
            except Exception as e:
                print(f"⚠️  Gmail authentication failed: {e}")
                print("⚠️  Email service will not be available until credentials are configured.")
        
        # Future providers can be added here
        # elif self.provider == 'sendgrid':
        #     self.backend = SendGridBackend()
        # elif self.provider == 'mailgun':
        #     self.backend = MailgunBackend()
        else:
            print(f"⚠️  Unknown email provider: {self.provider}")
            print(f"⚠️  Supported providers: gmail")
    
    def send_email(self, to, subject, body_text, body_html=None):
        """
        Send email using configured provider
        
        Args:
            to: Recipient email address (string or list)
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body
            
        Returns:
            dict: Result with success status
        """
        if not self.backend:
            return {
                'success': False,
                'error': f'Email backend not configured. Provider: {self.provider}'
            }
        
        print(f"📧 Sending email via {self.provider}...")
        print(f"   To: {to}")
        print(f"   Subject: {subject}")
        
        if self.provider == 'gmail':
            return self.backend.send_email(to, subject, body_text, body_html)
        else:
            return {
                'success': False,
                'error': f'Provider {self.provider} not implemented'
            }
    
    def send_password_reset_email(self, to, reset_url, user_name=None):
        """
        Send password reset email
        
        Args:
            to: Recipient email
            reset_url: Password reset URL with token
            user_name: Optional user's name
        """
        subject = "Reset Your Password - TTS System"
        
        greeting = f"Hello {user_name}," if user_name else "Hello,"
        
        body_text = f"""
{greeting}

You requested to reset your password for the TTS (Ticket Tracking System).

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request a password reset, please ignore this email. Your password will remain unchanged.

Best regards,
TTS System Team
"""
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .button {{ 
            background-color: #4CAF50; 
            color: white; 
            padding: 12px 30px; 
            text-decoration: none; 
            border-radius: 5px; 
            display: inline-block;
            margin: 20px 0;
        }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>{greeting}</p>
            <p>You requested to reset your password for the <strong>TTS (Ticket Tracking System)</strong>.</p>
            <p>Click the button below to reset your password:</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p><em>This link will expire in 1 hour.</em></p>
            <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
        </div>
        <div class="footer">
            <p>TTS System Team</p>
            <p>This is an automated message, please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(to, subject, body_text, body_html)
    
    def send_ticket_notification(self, to, ticket_id, ticket_title, action, user_name=None, ticket_url=None):
        """
        Send ticket notification email
        
        Args:
            to: Recipient email
            ticket_id: Ticket ID
            ticket_title: Ticket title
            action: Action performed (created, updated, assigned, etc.)
            user_name: Optional user's name
            ticket_url: Optional URL to view ticket
        """
        subject = f"Ticket #{ticket_id}: {action.title()}"
        
        greeting = f"Hello {user_name}," if user_name else "Hello,"
        view_ticket_link = f"\n\nView ticket: {ticket_url}" if ticket_url else ""
        
        body_text = f"""
{greeting}

A ticket has been {action}:

Ticket ID: #{ticket_id}
Title: {ticket_title}
Action: {action.title()}{view_ticket_link}

Log in to your TTS dashboard to view details.

Best regards,
TTS System Team
"""
        
        ticket_button = f'<p style="text-align: center;"><a href="{ticket_url}" class="button">View Ticket</a></p>' if ticket_url else ''
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .button {{ 
            background-color: #2196F3; 
            color: white; 
            padding: 12px 30px; 
            text-decoration: none; 
            border-radius: 5px; 
            display: inline-block;
            margin: 20px 0;
        }}
        .ticket-info {{ background-color: white; padding: 15px; border-left: 4px solid #2196F3; margin: 15px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Ticket Update</h1>
        </div>
        <div class="content">
            <p>{greeting}</p>
            <p>A ticket has been <strong>{action}</strong>:</p>
            <div class="ticket-info">
                <p><strong>Ticket ID:</strong> #{ticket_id}</p>
                <p><strong>Title:</strong> {ticket_title}</p>
                <p><strong>Action:</strong> {action.title()}</p>
            </div>
            {ticket_button}
            <p>Log in to your TTS dashboard to view more details.</p>
        </div>
        <div class="footer">
            <p>TTS System Team</p>
            <p>This is an automated message, please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(to, subject, body_text, body_html)
    
    def send_invitation_email(self, to, invitation_url, invited_by=None, organization=None):
        """
        Send user invitation email
        
        Args:
            to: Recipient email
            invitation_url: URL to accept invitation
            invited_by: Name of person who sent invitation
            organization: Organization name
        """
        subject = "You've been invited to TTS System"
        
        invited_by_text = f" by {invited_by}" if invited_by else ""
        org_text = f" to join {organization}" if organization else ""
        
        body_text = f"""
Hello,

You've been invited{invited_by_text}{org_text} on the TTS (Ticket Tracking System).

Click the link below to accept your invitation and set up your account:
{invitation_url}

This invitation link will expire in 7 days.

If you didn't expect this invitation, you can safely ignore this email.

Best regards,
TTS System Team
"""
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .button {{ 
            background-color: #FF9800; 
            color: white; 
            padding: 12px 30px; 
            text-decoration: none; 
            border-radius: 5px; 
            display: inline-block;
            margin: 20px 0;
        }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>You're Invited!</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>You've been invited{invited_by_text}{org_text} on the <strong>TTS (Ticket Tracking System)</strong>.</p>
            <p style="text-align: center;">
                <a href="{invitation_url}" class="button">Accept Invitation</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p><a href="{invitation_url}">{invitation_url}</a></p>
            <p><em>This invitation link will expire in 7 days.</em></p>
            <p>If you didn't expect this invitation, you can safely ignore this email.</p>
        </div>
        <div class="footer">
            <p>TTS System Team</p>
            <p>This is an automated message, please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(to, subject, body_text, body_html)
    
    def get_provider_info(self):
        """Get information about current email provider"""
        if not self.backend:
            return {'provider': self.provider, 'status': 'not configured'}
        
        if self.provider == 'gmail':
            return self.backend.get_quota_info()
        
        return {'provider': self.provider}
    
    def test_connection(self):
        """Test email service connection"""
        if not self.backend:
            return {
                'success': False,
                'error': 'No backend configured'
            }
        
        if self.provider == 'gmail':
            return self.backend.test_connection()
        
        return {
            'success': False,
            'error': f'Test not implemented for {self.provider}'
        }


# Singleton instance
_email_service = None

def get_email_service():
    """Get or create email service singleton"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
