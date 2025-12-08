"""
Simple SendGrid Email Service

Pure template-based email sending without database models
"""

import logging
from django.conf import settings
from django.template.loader import render_to_string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)


class SendGridEmailService:
    """
    Simple SendGrid email service using template files (no database)
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        self.from_email = getattr(settings, 'SENDGRID_FROM_EMAIL', 'noreply@ticketflow.com')
        self.from_name = getattr(settings, 'SENDGRID_FROM_NAME', 'TicketFlow')
        
        if not self.api_key:
            logger.warning("SendGrid API key not configured")
    
    def send_email(self, to_email, subject, template_name, context=None):
        """
        Send email using a template file
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Template file name (e.g., 'password_reset.html')
            context: Dictionary of context variables for the template
        
        Returns:
            tuple: (success: bool, message_id: str or None, error: str or None)
        """
        if not self.api_key:
            error_msg = "SendGrid API key not configured"
            logger.error(error_msg)
            return False, None, error_msg
        
        try:
            # Render the HTML template
            if context is None:
                context = {}
            
            # Add default context variables
            context.setdefault('site_name', 'TicketFlow')
            context.setdefault('support_email', getattr(settings, 'SUPPORT_EMAIL', 'support@ticketflow.com'))
            context.setdefault('current_year', 2025)
            
            # Render template
            template_path = f'emails/{template_name}'
            html_content = render_to_string(template_path, context)
            
            # Create SendGrid message
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            # Send email
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email} using template {template_name}")
                # SendGrid doesn't return message ID in the same way, use headers if available
                message_id = response.headers.get('X-Message-Id', 'sent')
                return True, message_id, None
            else:
                error_msg = f"SendGrid returned status {response.status_code}"
                logger.error(error_msg)
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, None, error_msg
    
    def send_password_reset_email(self, user_email, user_name, reset_url, reset_token):
        """
        Send password reset email
        """
        context = {
            'user_name': user_name,
            'reset_url': reset_url,
            'reset_token': reset_token,
            'expiry_hours': 1,
        }
        return self.send_email(
            to_email=user_email,
            subject='Password Reset Request - TicketFlow',
            template_name='password_reset.html',
            context=context
        )
    
    def send_otp_email(self, user_email, user_name, otp_code):
        """
        Send OTP verification email
        """
        context = {
            'user_name': user_name,
            'otp_code': otp_code,
            'expiry_minutes': 10,
        }
        return self.send_email(
            to_email=user_email,
            subject='Your Verification Code - TicketFlow',
            template_name='otp.html',
            context=context
        )
    
    def send_account_locked_email(self, user_email, user_name, locked_until=None, failed_attempts=None, lockout_duration=None, ip_address=None):
        """
        Send account locked notification
        """
        context = {
            'user_name': user_name,
            'locked_until': locked_until,
            'failed_attempts': failed_attempts or 10,
            'lockout_duration': lockout_duration or '15 minutes',
            'ip_address': ip_address,
        }
        return self.send_email(
            to_email=user_email,
            subject='Account Locked - TicketFlow',
            template_name='account_locked.html',
            context=context
        )
    
    def send_account_unlocked_email(self, user_email, user_name, ip_address=None):
        """
        Send account unlocked notification
        """
        context = {
            'user_name': user_name,
            'ip_address': ip_address,
        }
        return self.send_email(
            to_email=user_email,
            subject='Account Unlocked - TicketFlow',
            template_name='account_unlocked.html',
            context=context
        )
    
    def send_failed_login_email(self, user_email, user_name, ip_address, attempt_time=None, failed_attempts=None):
        """
        Send failed login attempt notification
        """
        context = {
            'user_name': user_name,
            'ip_address': ip_address,
            'attempt_time': attempt_time,
            'failed_attempts': failed_attempts or 1,
        }
        return self.send_email(
            to_email=user_email,
            subject='Failed Login Attempt - TicketFlow',
            template_name='failed_login.html',
            context=context
        )


# Singleton instance
_email_service = None

def get_email_service():
    """Get or create the email service singleton"""
    global _email_service
    if _email_service is None:
        _email_service = SendGridEmailService()
    return _email_service


# Convenience alias
get_sendgrid_service = get_email_service
