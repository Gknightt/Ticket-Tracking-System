"""
Gmail API Backend for Notification Service
Handles email sending via Gmail API using OAuth2
"""
import os
import base64
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings


# Gmail API scopes
# Need both send and readonly for profile access (testing connection)
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]


class GmailBackend:
    """Gmail API backend for sending emails"""
    
    def __init__(self):
        self.creds = None
        self.service = None
        self.token_file = os.path.join(settings.BASE_DIR, 'token.pickle')
        self.credentials_file = os.path.join(settings.BASE_DIR, 'credentials.json')
        
    def authenticate(self):
        """Authenticate with Gmail API using OAuth2"""
        # Load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("🔄 Refreshing Gmail API access token...")
                try:
                    self.creds.refresh(Request())
                    print("✅ Token refreshed successfully!")
                except Exception as e:
                    print(f"❌ Token refresh failed: {e}")
                    print("⚠️  You may need to re-authenticate. Delete token.pickle and run again.")
                    raise
            else:
                print("🔐 No valid credentials found. Starting OAuth flow...")
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"❌ credentials.json not found at {self.credentials_file}\n"
                        f"Please download it from Google Cloud Console:\n"
                        f"1. Go to https://console.cloud.google.com/apis/credentials\n"
                        f"2. Create OAuth 2.0 Client ID (Desktop app)\n"
                        f"3. Download JSON and save as 'credentials.json' in notification_service folder"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                self.creds = flow.run_local_server(port=0)
                print("✅ OAuth flow completed successfully!")
            
            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)
                print(f"💾 Token saved to {self.token_file}")
        
        # Build Gmail service
        self.service = build('gmail', 'v1', credentials=self.creds)
        print("✅ Gmail API authenticated successfully!")
        return True
    
    def create_message(self, sender, to, subject, body_text, body_html=None):
        """Create email message in Gmail API format"""
        if body_html:
            # Create multipart message with both plain text and HTML
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['from'] = sender
            message['subject'] = subject
            
            part1 = MIMEText(body_text, 'plain')
            part2 = MIMEText(body_html, 'html')
            
            message.attach(part1)
            message.attach(part2)
        else:
            # Plain text only
            message = MIMEText(body_text)
            message['to'] = to
            message['from'] = sender
            message['subject'] = subject
        
        # Encode message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {'raw': raw}
    
    def send_email(self, to, subject, body_text, body_html=None, sender='me'):
        """
        Send email via Gmail API
        
        Args:
            to: Recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body
            sender: Sender (use 'me' for authenticated user)
            
        Returns:
            dict: Result with success status and message_id or error
        """
        try:
            # Authenticate if not already done
            if not self.service:
                self.authenticate()
            
            # Create message
            message = self.create_message(sender, to, subject, body_text, body_html)
            
            # Send message
            sent_message = self.service.users().messages().send(
                userId='me', 
                body=message
            ).execute()
            
            print(f"✅ Email sent successfully to {to}! Message ID: {sent_message['id']}")
            return {
                'success': True,
                'message_id': sent_message['id'],
                'to': to,
                'provider': 'gmail'
            }
            
        except HttpError as error:
            error_message = str(error)
            print(f"❌ Gmail API HTTP error: {error_message}")
            
            # Parse specific error types
            if 'quotaExceeded' in error_message:
                print("⚠️  Gmail API quota exceeded. Daily limit reached.")
            elif 'invalid_grant' in error_message:
                print("⚠️  Invalid credentials. Token may have expired. Delete token.pickle and re-authenticate.")
            
            return {
                'success': False,
                'error': error_message,
                'error_type': 'http_error',
                'provider': 'gmail'
            }
            
        except Exception as e:
            error_message = str(e)
            print(f"❌ Error sending email: {error_message}")
            return {
                'success': False,
                'error': error_message,
                'error_type': 'general_error',
                'provider': 'gmail'
            }
    
    def get_quota_info(self):
        """Get Gmail API quota information"""
        return {
            'provider': 'gmail',
            'daily_limit_free': '250 emails per day (free Gmail account)',
            'daily_limit_workspace': '2000 emails per day (Google Workspace)',
            'quota_check_url': 'https://console.cloud.google.com/apis/api/gmail.googleapis.com/quotas',
            'note': 'Check your actual usage and limits in Google Cloud Console'
        }
    
    def test_connection(self):
        """Test Gmail API connection"""
        try:
            if not self.service:
                self.authenticate()
            
            # Try to get user profile
            profile = self.service.users().getProfile(userId='me').execute()
            
            return {
                'success': True,
                'email': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal'),
                'threads_total': profile.get('threadsTotal')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
