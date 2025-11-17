from django.core.management.base import BaseCommand
from notifications.models import NotificationTemplate


class Command(BaseCommand):
    help = 'Setup default notification templates for the notification service'

    def handle(self, *args, **options):
        templates = [
            {
                'notification_type': 'account_locked',
                'subject': 'Security Alert: Account Locked - {{ user_name }}',
                'body_text': '''Hello {{ user_name }},

Your account has been locked due to {{ failed_attempts }} failed login attempts.

For security reasons, your account will remain locked for {{ lockout_duration }}.

If this wasn't you, please contact our support team immediately.

Timestamp: {{ timestamp }}

Best regards,
Security Team'''
            },
            {
                'notification_type': 'account_unlocked',
                'subject': 'Account Unlocked - {{ user_name }}',
                'body_text': '''Hello {{ user_name }},

Your account has been successfully unlocked and you can now log in again.

If you didn't request this unlock or have any concerns, please contact our support team.

Timestamp: {{ timestamp }}

Best regards,
Security Team'''
            },
            {
                'notification_type': 'failed_login_attempt',
                'subject': 'Security Alert: Failed Login Attempt - {{ user_name }}',
                'body_text': '''Hello {{ user_name }},

We detected a failed login attempt for your account.

Details:
- Time: {{ timestamp }}
- IP Address: {{ ip_address }}

If this was you, please make sure you're using the correct credentials. If this wasn't you, please secure your account immediately.

Best regards,
Security Team'''
            },
            {
                'notification_type': 'password_reset',
                'subject': 'Password Reset Request - {{ user_name }}',
                'body_text': '''Hello {{ user_name }},

A password reset was requested for your account.

If you requested this reset, please use the provided link to reset your password.
If you didn't request this, please ignore this email and contact support if you have concerns.

Timestamp: {{ timestamp }}

Best regards,
Security Team''',
                'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset Request</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #007bff; padding: 30px 40px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">Password Reset Request</h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px 0; color: #333333; font-size: 16px; line-height: 1.6;">
                                Hello <strong>{{ user_name }}</strong>,
                            </p>
                            
                            <p style="margin: 0 0 20px 0; color: #333333; font-size: 16px; line-height: 1.6;">
                                We received a request to reset your password. Click the button below to reset it:
                            </p>
                            
                            <!-- Button -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{{ reset_url }}" style="display: inline-block; padding: 14px 40px; background-color: #007bff; color: #ffffff; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: 600; box-shadow: 0 2px 4px rgba(0,123,255,0.3);">
                                            Reset Password
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 20px 0; color: #666666; font-size: 14px; line-height: 1.6;">
                                If the button doesn't work, copy and paste this link into your browser:
                            </p>
                            
                            <p style="margin: 0 0 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #007bff; word-break: break-all;">
                                <a href="{{ reset_url }}" style="color: #007bff; text-decoration: none; font-size: 14px;">{{ reset_url }}</a>
                            </p>
                            
                            <div style="margin: 30px 0; padding: 20px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                                <p style="margin: 0 0 10px 0; color: #856404; font-size: 14px; font-weight: 600;">
                                    ⚠️ Security Notice
                                </p>
                                <p style="margin: 0; color: #856404; font-size: 14px; line-height: 1.6;">
                                    This link will expire in <strong>1 hour</strong> for security reasons.
                                </p>
                            </div>
                            
                            <p style="margin: 20px 0 0 0; color: #666666; font-size: 14px; line-height: 1.6;">
                                If you didn't request a password reset, please ignore this email or contact support if you have concerns about your account security.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f8f9fa; border-top: 1px solid #e9ecef;">
                            <p style="margin: 0 0 10px 0; color: #999999; font-size: 12px; text-align: center; line-height: 1.6;">
                                This is an automated message, please do not reply to this email.
                            </p>
                            <p style="margin: 0; color: #999999; font-size: 12px; text-align: center; line-height: 1.6;">
                                © 2025 Ticket Tracking System. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
'''
            },
            {
                'notification_type': 'account_created',
                'subject': 'Welcome to our platform - {{ user_name }}',
                'body_text': '''Hello {{ user_name }},

Welcome to our platform! Your account has been successfully created.

You can now log in using your email address and the password you provided during registration.

If you have any questions, please don't hesitate to contact our support team.

Timestamp: {{ timestamp }}

Best regards,
Support Team'''
            },
            {
                'notification_type': 'login_success',
                'subject': 'Successful Login - {{ user_name }}',
                'body_text': '''Hello {{ user_name }},

We're notifying you of a successful login to your account.

Details:
- Time: {{ timestamp }}
- IP Address: {{ ip_address }}

If this wasn't you, please contact our support team immediately.

Best regards,
Security Team'''
            },
        ]

        created_count = 0
        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                notification_type=template_data['notification_type'],
                defaults={
                    'subject': template_data['subject'],
                    'body_text': template_data['body_text'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created template: {template.notification_type}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Template already exists: {template.notification_type}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up {created_count} new notification templates.'
            )
        )