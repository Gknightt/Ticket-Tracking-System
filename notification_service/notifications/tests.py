from django.test import TestCase
from django.utils import timezone
from django.core import mail
from django.conf import settings
from unittest.mock import Mock, patch, MagicMock
import uuid

from .models import NotificationTemplate, NotificationLog, NotificationRequest
from .services import NotificationService


class NotificationServiceTests(TestCase):
    """Test cases for NotificationService"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test template (using Django template syntax)
        self.template = NotificationTemplate.objects.create(
            notification_type='account_created',
            subject='Welcome {{ user_name }}!',
            body_text='Hello {{ user_name }}, your account has been created at {{ timestamp }}.',
            is_active=True
        )
        
        self.user_id = uuid.uuid4()
        self.user_email = 'test@example.com'
        self.user_name = 'John Doe'
    
    def test_send_notification_success(self):
        """Test successfully sending a notification"""
        success = NotificationService.send_notification(
            user_id=self.user_id,
            user_email=self.user_email,
            user_name=self.user_name,
            notification_type='account_created',
            context_data={'extra_info': 'test'}
        )
        
        self.assertTrue(success)
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Welcome John Doe!', mail.outbox[0].subject)
        self.assertIn('John Doe', mail.outbox[0].body)
        
        # Check that log was created
        log = NotificationLog.objects.get(user_email=self.user_email)
        self.assertEqual(log.status, 'sent')
        self.assertEqual(log.notification_type, 'account_created')
        self.assertIsNotNone(log.sent_at)
    
    def test_send_notification_no_template(self):
        """Test sending notification when template doesn't exist"""
        success = NotificationService.send_notification(
            user_id=self.user_id,
            user_email=self.user_email,
            user_name=self.user_name,
            notification_type='nonexistent_type'
        )
        
        self.assertFalse(success)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_notification_inactive_template(self):
        """Test that inactive templates are not used"""
        self.template.is_active = False
        self.template.save()
        
        success = NotificationService.send_notification(
            user_id=self.user_id,
            user_email=self.user_email,
            user_name=self.user_name,
            notification_type='account_created'
        )
        
        self.assertFalse(success)
        self.assertEqual(len(mail.outbox), 0)
    
    @patch('notifications.services.send_mail')
    def test_send_notification_email_failure(self, mock_send_mail):
        """Test handling of email sending failure"""
        mock_send_mail.side_effect = Exception('SMTP error')
        
        success = NotificationService.send_notification(
            user_id=self.user_id,
            user_email=self.user_email,
            user_name=self.user_name,
            notification_type='account_created'
        )
        
        self.assertFalse(success)
        
        # Check that log shows failure
        log = NotificationLog.objects.get(user_email=self.user_email)
        self.assertEqual(log.status, 'failed')
        self.assertIn('SMTP error', log.error_message)
    
    def test_send_notification_with_context_data(self):
        """Test notification with additional context data"""
        context_data = {
            'custom_field': 'custom_value',
            'another_field': 123
        }
        
        success = NotificationService.send_notification(
            user_id=self.user_id,
            user_email=self.user_email,
            user_name=self.user_name,
            notification_type='account_created',
            context_data=context_data
        )
        
        self.assertTrue(success)
        
        # Check that context was saved in log
        log = NotificationLog.objects.get(user_email=self.user_email)
        self.assertEqual(log.context_data['custom_field'], 'custom_value')
        self.assertEqual(log.context_data['another_field'], 123)
    
    def test_send_notification_no_user_name(self):
        """Test notification when user_name is not provided"""
        success = NotificationService.send_notification(
            user_id=self.user_id,
            user_email=self.user_email,
            user_name=None,
            notification_type='account_created'
        )
        
        self.assertTrue(success)
        
        # Should use email prefix as fallback
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('test', mail.outbox[0].body)
    
    def test_process_notification_request_dict(self):
        """Test processing notification request from dict"""
        request_data = {
            'user_id': str(self.user_id),
            'user_email': self.user_email,
            'user_name': self.user_name,
            'notification_type': 'account_created',
            'context_data': {'test': 'data'},
            'ip_address': '127.0.0.1',
            'user_agent': 'Test Agent'
        }
        
        success = NotificationService.process_notification_request(request_data)
        
        self.assertTrue(success)
        
        # Check that request was created and marked as processed
        request = NotificationRequest.objects.get(user_email=self.user_email)
        self.assertTrue(request.processed)
        self.assertIsNotNone(request.processed_at)
        self.assertEqual(request.ip_address, '127.0.0.1')
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
    
    def test_process_notification_request_model(self):
        """Test processing notification request from model instance"""
        request_obj = NotificationRequest.objects.create(
            user_id=self.user_id,
            user_email=self.user_email,
            user_name=self.user_name,
            notification_type='account_created',
            context_data={'test': 'data'}
        )
        
        success = NotificationService.process_notification_request(request_obj)
        
        self.assertTrue(success)
        
        # Check that request was marked as processed
        request_obj.refresh_from_db()
        self.assertTrue(request_obj.processed)
        self.assertIsNotNone(request_obj.processed_at)
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
    
    def test_process_notification_request_no_user_id(self):
        """Test processing notification request without user_id"""
        request_data = {
            'user_id': None,
            'user_email': self.user_email,
            'user_name': self.user_name,
            'notification_type': 'account_created'
        }
        
        success = NotificationService.process_notification_request(request_data)
        
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
    
    @patch('notifications.services.NotificationService.send_notification')
    def test_process_notification_request_failure(self, mock_send):
        """Test handling of notification request processing failure"""
        mock_send.side_effect = Exception('Processing error')
        
        request_data = {
            'user_email': self.user_email,
            'user_name': self.user_name,
            'notification_type': 'account_created'
        }
        
        success = NotificationService.process_notification_request(request_data)
        
        self.assertFalse(success)
    
    def test_get_notification_history_all(self):
        """Test getting all notification history"""
        # Create multiple notifications
        for i in range(3):
            NotificationLog.objects.create(
                user_id=self.user_id,
                user_email=f'test{i}@example.com',
                notification_type='account_created',
                recipient_email=f'test{i}@example.com',
                subject='Test',
                message='Test message',
                status='sent'
            )
        
        history = NotificationService.get_notification_history()
        
        self.assertEqual(history.count(), 3)
    
    def test_get_notification_history_by_user_id(self):
        """Test filtering notification history by user_id"""
        user_id_1 = uuid.uuid4()
        user_id_2 = uuid.uuid4()
        
        NotificationLog.objects.create(
            user_id=user_id_1,
            user_email='test1@example.com',
            notification_type='account_created',
            recipient_email='test1@example.com',
            subject='Test',
            message='Test message',
            status='sent'
        )
        
        NotificationLog.objects.create(
            user_id=user_id_2,
            user_email='test2@example.com',
            notification_type='account_created',
            recipient_email='test2@example.com',
            subject='Test',
            message='Test message',
            status='sent'
        )
        
        history = NotificationService.get_notification_history(user_id=user_id_1)
        
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().user_id, user_id_1)
    
    def test_get_notification_history_by_email(self):
        """Test filtering notification history by email"""
        NotificationLog.objects.create(
            user_id=self.user_id,
            user_email='test1@example.com',
            notification_type='account_created',
            recipient_email='test1@example.com',
            subject='Test',
            message='Test message',
            status='sent'
        )
        
        NotificationLog.objects.create(
            user_id=self.user_id,
            user_email='test2@example.com',
            notification_type='account_created',
            recipient_email='test2@example.com',
            subject='Test',
            message='Test message',
            status='sent'
        )
        
        history = NotificationService.get_notification_history(user_email='test1@example.com')
        
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().user_email, 'test1@example.com')
    
    def test_get_notification_history_by_type(self):
        """Test filtering notification history by notification type"""
        NotificationLog.objects.create(
            user_id=self.user_id,
            user_email=self.user_email,
            notification_type='account_created',
            recipient_email=self.user_email,
            subject='Test',
            message='Test message',
            status='sent'
        )
        
        NotificationLog.objects.create(
            user_id=self.user_id,
            user_email=self.user_email,
            notification_type='password_reset',
            recipient_email=self.user_email,
            subject='Test',
            message='Test message',
            status='sent'
        )
        
        history = NotificationService.get_notification_history(notification_type='account_created')
        
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().notification_type, 'account_created')
    
    def test_get_notification_history_limit(self):
        """Test limiting notification history results"""
        for i in range(100):
            NotificationLog.objects.create(
                user_id=self.user_id,
                user_email=self.user_email,
                notification_type='account_created',
                recipient_email=self.user_email,
                subject='Test',
                message='Test message',
                status='sent'
            )
        
        history = NotificationService.get_notification_history(limit=10)
        
        self.assertEqual(history.count(), 10)
    
    def test_send_email_direct_text(self):
        """Test sending direct email with text content"""
        success = NotificationService.send_email_direct(
            recipient_email='test@example.com',
            subject='Test Subject',
            message='Test plain text message'
        )
        
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Test Subject')
        self.assertEqual(mail.outbox[0].body, 'Test plain text message')
    
    def test_send_email_direct_html(self):
        """Test sending direct email with HTML content"""
        success = NotificationService.send_email_direct(
            recipient_email='test@example.com',
            subject='Test Subject',
            message='Test plain text',
            html_message='<html><body><h1>Test HTML</h1></body></html>'
        )
        
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Test Subject')
        # Check that HTML alternative was added
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
    
    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_send_email_direct_failure(self, mock_send):
        """Test handling of direct email sending failure"""
        mock_send.side_effect = Exception('Email error')
        
        success = NotificationService.send_email_direct(
            recipient_email='test@example.com',
            subject='Test Subject',
            message='Test message'
        )
        
        self.assertFalse(success)


class NotificationTemplateModelTests(TestCase):
    """Test cases for NotificationTemplate model"""
    
    def test_create_template(self):
        """Test creating a notification template"""
        template = NotificationTemplate.objects.create(
            notification_type='account_locked',
            subject='Account Locked',
            body_text='Your account has been locked.',
            is_active=True
        )
        
        self.assertIsNotNone(template.id)
        self.assertEqual(template.notification_type, 'account_locked')
        self.assertTrue(template.is_active)
    
    def test_template_str_representation(self):
        """Test string representation of template"""
        template = NotificationTemplate.objects.create(
            notification_type='account_locked',
            subject='Account Locked',
            body_text='Your account has been locked.'
        )
        
        self.assertIn('Account Locked', str(template))
    
    def test_unique_notification_type(self):
        """Test that notification_type is unique"""
        NotificationTemplate.objects.create(
            notification_type='account_locked',
            subject='Account Locked',
            body_text='Your account has been locked.'
        )
        
        with self.assertRaises(Exception):
            NotificationTemplate.objects.create(
                notification_type='account_locked',
                subject='Duplicate',
                body_text='Duplicate template'
            )


class NotificationLogModelTests(TestCase):
    """Test cases for NotificationLog model"""
    
    def test_create_log(self):
        """Test creating a notification log"""
        log = NotificationLog.objects.create(
            user_id=uuid.uuid4(),
            user_email='test@example.com',
            notification_type='account_created',
            recipient_email='test@example.com',
            subject='Welcome',
            message='Welcome message',
            status='sent'
        )
        
        self.assertIsNotNone(log.id)
        self.assertEqual(log.status, 'sent')
    
    def test_log_default_status(self):
        """Test that default status is 'pending'"""
        log = NotificationLog.objects.create(
            user_email='test@example.com',
            notification_type='account_created',
            recipient_email='test@example.com',
            subject='Test',
            message='Test message'
        )
        
        self.assertEqual(log.status, 'pending')
    
    def test_log_str_representation(self):
        """Test string representation of log"""
        log = NotificationLog.objects.create(
            user_email='test@example.com',
            notification_type='account_created',
            recipient_email='test@example.com',
            subject='Test',
            message='Test message',
            status='sent'
        )
        
        log_str = str(log)
        self.assertIn('account_created', log_str)
        self.assertIn('test@example.com', log_str)
        self.assertIn('sent', log_str)


class NotificationRequestModelTests(TestCase):
    """Test cases for NotificationRequest model"""
    
    def test_create_request(self):
        """Test creating a notification request"""
        request = NotificationRequest.objects.create(
            user_id=uuid.uuid4(),
            user_email='test@example.com',
            user_name='John Doe',
            notification_type='account_created',
            context_data={'key': 'value'}
        )
        
        self.assertIsNotNone(request.id)
        self.assertFalse(request.processed)
        self.assertEqual(request.context_data['key'], 'value')
    
    def test_request_default_processed(self):
        """Test that default processed is False"""
        request = NotificationRequest.objects.create(
            user_email='test@example.com',
            notification_type='account_created'
        )
        
        self.assertFalse(request.processed)
        self.assertIsNone(request.processed_at)
    
    def test_request_optional_user_id(self):
        """Test that user_id is optional"""
        request = NotificationRequest.objects.create(
            user_id=None,
            user_email='test@example.com',
            notification_type='account_created'
        )
        
        self.assertIsNone(request.user_id)
    
    def test_request_str_representation(self):
        """Test string representation of request"""
        request = NotificationRequest.objects.create(
            user_email='test@example.com',
            notification_type='account_created'
        )
        
        request_str = str(request)
        self.assertIn('account_created', request_str)
        self.assertIn('test@example.com', request_str)
