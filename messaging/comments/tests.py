from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image

from .models import Comment, CommentRating, DocumentStorage, CommentDocument, Ticket
from .services import CommentNotificationService, DocumentAttachmentService, CommentService
from .serializers import CommentSerializer


class CommentNotificationServiceTests(TestCase):
    """Test cases for CommentNotificationService"""
    
    def setUp(self):
        """Set up test data"""
        self.ticket = Ticket.objects.create(ticket_id='T12345', status='open')
        self.comment = Comment.objects.create(
            ticket=self.ticket,
            user_id='user123',
            firstname='John',
            lastname='Doe',
            role='Agent',
            content='Test comment'
        )
        self.service = CommentNotificationService()
    
    @patch('comments.services.get_channel_layer')
    def test_send_notification_no_channel_layer(self, mock_get_channel):
        """Test that service handles missing channel layer gracefully"""
        mock_get_channel.return_value = None
        service = CommentNotificationService()
        
        # Should not raise an exception
        service.send_notification(self.comment, 'create')
    
    @patch('comments.services.get_channel_layer')
    @patch('comments.services.async_to_sync')
    def test_send_notification_create(self, mock_async, mock_get_channel):
        """Test sending notification for comment creation"""
        mock_channel = MagicMock()
        mock_get_channel.return_value = mock_channel
        service = CommentNotificationService()
        
        service.send_notification(self.comment, 'create')
        
        mock_async.assert_called_once()
        call_args = mock_async.call_args[0][0]
        self.assertEqual(call_args, mock_channel.group_send)
    
    @patch('comments.services.get_channel_layer')
    @patch('comments.services.async_to_sync')
    def test_send_notification_delete(self, mock_async, mock_get_channel):
        """Test sending notification for comment deletion"""
        mock_channel = MagicMock()
        mock_get_channel.return_value = mock_channel
        service = CommentNotificationService()
        
        service.send_notification(self.comment, 'delete')
        
        mock_async.assert_called_once()
    
    @patch('comments.services.get_channel_layer')
    @patch('comments.services.async_to_sync')
    def test_send_notification_rate(self, mock_async, mock_get_channel):
        """Test sending notification for comment rating"""
        mock_channel = MagicMock()
        mock_get_channel.return_value = mock_channel
        service = CommentNotificationService()
        
        rating_data = {'rating': True, 'user_id': 'user456'}
        service.send_notification(self.comment, 'rate', rating_data=rating_data)
        
        mock_async.assert_called_once()
    
    def test_prepare_message_data_create(self):
        """Test message preparation for create action"""
        data = self.service._prepare_message_data(self.comment, 'create')
        
        self.assertEqual(data['type'], 'comment_create')
        self.assertIn('timestamp', data)
        self.assertIn('message', data)
        self.assertEqual(data['action'], 'create')
    
    def test_prepare_message_data_delete(self):
        """Test message preparation for delete action"""
        data = self.service._prepare_message_data(self.comment, 'delete')
        
        self.assertEqual(data['type'], 'comment_delete')
        self.assertIn('deleted_comment_id', data)
        self.assertEqual(data['message']['ticket_id'], self.ticket.ticket_id)
    
    @patch('comments.services.get_channel_layer')
    def test_send_comment_create(self, mock_get_channel):
        """Test convenience method for comment creation"""
        mock_channel = MagicMock()
        mock_get_channel.return_value = mock_channel
        service = CommentNotificationService()
        
        with patch.object(service, 'send_notification') as mock_send:
            service.send_comment_create(self.comment)
            mock_send.assert_called_once_with(self.comment, 'create')
    
    @patch('comments.services.get_channel_layer')
    def test_send_comment_update(self, mock_get_channel):
        """Test convenience method for comment update"""
        mock_channel = MagicMock()
        mock_get_channel.return_value = mock_channel
        service = CommentNotificationService()
        
        with patch.object(service, 'send_notification') as mock_send:
            service.send_comment_update(self.comment)
            mock_send.assert_called_once_with(self.comment, 'update')
    
    @patch('comments.services.get_channel_layer')
    def test_send_comment_delete(self, mock_get_channel):
        """Test convenience method for comment deletion"""
        mock_channel = MagicMock()
        mock_get_channel.return_value = mock_channel
        service = CommentNotificationService()
        
        with patch.object(service, 'send_notification') as mock_send:
            service.send_comment_delete(self.comment)
            mock_send.assert_called_once_with(self.comment, 'delete')
    
    @patch('comments.services.get_channel_layer')
    def test_send_comment_reply(self, mock_get_channel):
        """Test convenience method for comment reply"""
        mock_channel = MagicMock()
        mock_get_channel.return_value = mock_channel
        service = CommentNotificationService()
        
        with patch.object(service, 'send_notification') as mock_send:
            service.send_comment_reply(self.comment)
            mock_send.assert_called_once_with(self.comment, 'reply')


class DocumentAttachmentServiceTests(TestCase):
    """Test cases for DocumentAttachmentService"""
    
    def setUp(self):
        """Set up test data"""
        self.ticket = Ticket.objects.create(ticket_id='T12345', status='open')
        self.comment = Comment.objects.create(
            ticket=self.ticket,
            user_id='user123',
            firstname='John',
            lastname='Doe',
            role='Agent',
            content='Test comment'
        )
        self.user_data = {
            'user_id': 'user123',
            'firstname': 'John',
            'lastname': 'Doe'
        }
    
    def _create_test_file(self, name='test.txt', content=b'test content'):
        """Helper to create a test file"""
        return SimpleUploadedFile(name, content, content_type='text/plain')
    
    def _create_test_image(self, name='test.jpg'):
        """Helper to create a test image file"""
        # Create a simple test image
        image = Image.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        image.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(name, img_io.read(), content_type='image/jpeg')
    
    def test_attach_files_to_comment_success(self):
        """Test successfully attaching files to a comment"""
        file1 = self._create_test_file('file1.txt', b'content 1')
        file2 = self._create_test_file('file2.txt', b'content 2')
        
        attached, errors = DocumentAttachmentService.attach_files_to_comment(
            self.comment, [file1, file2], self.user_data
        )
        
        self.assertEqual(len(attached), 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(CommentDocument.objects.filter(comment=self.comment).count(), 2)
    
    def test_attach_files_empty_file(self):
        """Test handling of empty files"""
        empty_file = SimpleUploadedFile('empty.txt', b'', content_type='text/plain')
        
        attached, errors = DocumentAttachmentService.attach_files_to_comment(
            self.comment, [empty_file], self.user_data
        )
        
        self.assertEqual(len(attached), 0)
        self.assertEqual(len(errors), 0)
    
    def test_attach_files_duplicate(self):
        """Test handling of duplicate file attachments"""
        file1 = self._create_test_file('duplicate.txt', b'same content')
        
        # Attach first time
        attached1, errors1 = DocumentAttachmentService.attach_files_to_comment(
            self.comment, [file1], self.user_data
        )
        
        # Try to attach same file again
        file2 = self._create_test_file('duplicate.txt', b'same content')
        attached2, errors2 = DocumentAttachmentService.attach_files_to_comment(
            self.comment, [file2], self.user_data
        )
        
        self.assertEqual(len(attached1), 1)
        self.assertEqual(len(attached2), 0)
        self.assertEqual(len(errors2), 1)
        self.assertIn('already attached', errors2[0])
    
    def test_attach_files_deduplication(self):
        """Test that identical files are deduplicated in storage"""
        file1 = self._create_test_file('file1.txt', b'identical content')
        file2 = self._create_test_file('file2.txt', b'identical content')
        
        attached, errors = DocumentAttachmentService.attach_files_to_comment(
            self.comment, [file1, file2], self.user_data
        )
        
        # Only one should be attached since they have identical content
        self.assertEqual(len(attached), 1)
        # The second one should generate an error
        self.assertEqual(len(errors), 1)
        self.assertIn('already attached', errors[0])
        # Only one DocumentStorage should exist
        self.assertEqual(DocumentStorage.objects.count(), 1)
    
    def test_handle_document_attachments(self):
        """Test the handle_document_attachments wrapper method"""
        file1 = self._create_test_file('test.txt', b'test')
        
        mock_request = Mock()
        mock_request.FILES.getlist.return_value = [file1]
        
        data = {
            'user_id': 'user123',
            'firstname': 'John',
            'lastname': 'Doe'
        }
        
        attached, errors = DocumentAttachmentService.handle_document_attachments(
            mock_request, self.comment, data
        )
        
        self.assertEqual(len(attached), 1)
        self.assertEqual(len(errors), 0)


class CommentServiceTests(TestCase):
    """Test cases for CommentService"""
    
    def setUp(self):
        """Set up test data"""
        self.ticket = Ticket.objects.create(ticket_id='T12345', status='open')
    
    def test_extract_user_data_from_jwt(self):
        """Test extracting user data from JWT token"""
        mock_user = Mock()
        mock_user.user_id = 'user123'
        mock_user.full_name = 'John Doe'
        mock_user.username = 'johndoe'
        mock_user.get_systems.return_value = ['Admin']
        
        user_data = CommentService.extract_user_data_from_jwt(mock_user)
        
        self.assertEqual(user_data['user_id'], 'user123')
        self.assertEqual(user_data['firstname'], 'John')
        self.assertEqual(user_data['lastname'], 'Doe')
        self.assertEqual(user_data['role'], 'Admin')
    
    def test_extract_user_data_no_full_name(self):
        """Test extracting user data when full_name is not available"""
        mock_user = Mock()
        mock_user.user_id = 'user123'
        mock_user.full_name = None
        mock_user.username = 'johndoe'
        mock_user.get_systems.return_value = ['User']
        
        user_data = CommentService.extract_user_data_from_jwt(mock_user)
        
        self.assertEqual(user_data['firstname'], 'johndoe')
        self.assertEqual(user_data['lastname'], '')
    
    def test_extract_user_data_no_systems(self):
        """Test extracting user data when systems list is empty"""
        mock_user = Mock()
        mock_user.user_id = 'user123'
        mock_user.full_name = 'John Doe'
        mock_user.username = 'johndoe'
        mock_user.get_systems.return_value = []
        
        user_data = CommentService.extract_user_data_from_jwt(mock_user)
        
        self.assertEqual(user_data['role'], 'User')
    
    def test_create_comment_with_attachments(self):
        """Test creating a comment with file attachments"""
        validated_data = {
            'ticket_id': self.ticket.ticket_id,
            'content': 'Test comment'
        }
        
        user_data = {
            'user_id': 'user123',
            'firstname': 'John',
            'lastname': 'Doe',
            'role': 'Agent'
        }
        
        # Create test file
        test_file = SimpleUploadedFile('test.txt', b'test content', content_type='text/plain')
        files = [test_file]
        
        comment = CommentService.create_comment_with_attachments(validated_data, files, user_data)
        
        self.assertIsNotNone(comment)
        self.assertEqual(comment.user_id, 'user123')
        self.assertEqual(comment.firstname, 'John')
        self.assertEqual(comment.lastname, 'Doe')
        self.assertEqual(comment.role, 'Agent')
        self.assertEqual(comment.content, 'Test comment')
        self.assertEqual(CommentDocument.objects.filter(comment=comment).count(), 1)
    
    def test_create_comment_without_attachments(self):
        """Test creating a comment without file attachments"""
        validated_data = {
            'ticket_id': self.ticket.ticket_id,
            'content': 'Test comment no files'
        }
        
        user_data = {
            'user_id': 'user123',
            'firstname': 'Jane',
            'lastname': 'Smith',
            'role': 'Admin'
        }
        
        comment = CommentService.create_comment_with_attachments(validated_data, [], user_data)
        
        self.assertIsNotNone(comment)
        self.assertEqual(comment.content, 'Test comment no files')
        self.assertEqual(CommentDocument.objects.filter(comment=comment).count(), 0)


class DocumentStorageModelTests(TestCase):
    """Test cases for DocumentStorage model"""
    
    def test_create_from_file_new(self):
        """Test creating a new DocumentStorage from file"""
        file = SimpleUploadedFile('test.txt', b'test content', content_type='text/plain')
        
        doc, created = DocumentStorage.create_from_file(file, 'user123', 'John', 'Doe')
        
        self.assertTrue(created)
        self.assertEqual(doc.original_filename, 'test.txt')
        self.assertEqual(doc.file_size, 12)
        self.assertEqual(doc.uploaded_by_user_id, 'user123')
        self.assertEqual(doc.uploaded_by_name, 'John Doe')
    
    def test_create_from_file_duplicate(self):
        """Test that duplicate files return existing DocumentStorage"""
        file1 = SimpleUploadedFile('test1.txt', b'same content', content_type='text/plain')
        file2 = SimpleUploadedFile('test2.txt', b'same content', content_type='text/plain')
        
        doc1, created1 = DocumentStorage.create_from_file(file1, 'user123', 'John', 'Doe')
        doc2, created2 = DocumentStorage.create_from_file(file2, 'user456', 'Jane', 'Smith')
        
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(doc1.id, doc2.id)
    
    def test_calculate_image_info(self):
        """Test image info calculation for image files"""
        # Create a test image
        image = Image.new('RGB', (200, 100), color='blue')
        img_io = BytesIO()
        image.save(img_io, format='PNG')
        img_content = img_io.getvalue()
        
        file = SimpleUploadedFile('image.png', img_content, content_type='image/png')
        doc, created = DocumentStorage.create_from_file(file, 'user123', 'John', 'Doe')
        
        self.assertTrue(doc.is_image)
        self.assertEqual(doc.image_width, 200)
        self.assertEqual(doc.image_height, 100)
        self.assertEqual(doc.image_ratio, 2.0)
    
    def test_calculate_image_info_non_image(self):
        """Test that non-image files don't get image metadata"""
        file = SimpleUploadedFile('test.txt', b'not an image', content_type='text/plain')
        doc, created = DocumentStorage.create_from_file(file, 'user123', 'John', 'Doe')
        
        self.assertFalse(doc.is_image)
        self.assertIsNone(doc.image_width)
        self.assertIsNone(doc.image_height)


class CommentModelTests(TestCase):
    """Test cases for Comment model"""
    
    def setUp(self):
        """Set up test data"""
        self.ticket = Ticket.objects.create(ticket_id='T12345', status='open')
    
    def test_comment_id_generation(self):
        """Test that comment_id is automatically generated"""
        comment = Comment.objects.create(
            ticket=self.ticket,
            user_id='user123',
            firstname='John',
            lastname='Doe',
            role='Agent',
            content='Test'
        )
        
        self.assertIsNotNone(comment.comment_id)
        self.assertTrue(comment.comment_id.startswith('C'))
    
    def test_replies_property(self):
        """Test the replies property returns child comments"""
        parent = Comment.objects.create(
            ticket=self.ticket,
            user_id='user123',
            firstname='John',
            lastname='Doe',
            role='Agent',
            content='Parent comment'
        )
        
        reply1 = Comment.objects.create(
            ticket=self.ticket,
            user_id='user456',
            firstname='Jane',
            lastname='Smith',
            role='User',
            content='Reply 1',
            parent=parent.comment_id
        )
        
        reply2 = Comment.objects.create(
            ticket=self.ticket,
            user_id='user789',
            firstname='Bob',
            lastname='Jones',
            role='User',
            content='Reply 2',
            parent=parent.comment_id
        )
        
        replies = parent.replies
        self.assertEqual(replies.count(), 2)
        self.assertIn(reply1, replies)
        self.assertIn(reply2, replies)


class CommentRatingModelTests(TestCase):
    """Test cases for CommentRating model"""
    
    def setUp(self):
        """Set up test data"""
        self.ticket = Ticket.objects.create(ticket_id='T12345', status='open')
        self.comment = Comment.objects.create(
            ticket=self.ticket,
            user_id='user123',
            firstname='John',
            lastname='Doe',
            role='Agent',
            content='Test comment'
        )
    
    def test_rating_updates_comment_counts(self):
        """Test that creating a rating updates comment counts"""
        CommentRating.objects.create(
            comment=self.comment,
            user_id='user456',
            firstname='Jane',
            lastname='Smith',
            role='User',
            rating=True
        )
        
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.thumbs_up_count, 1)
        self.assertEqual(self.comment.thumbs_down_count, 0)
    
    def test_multiple_ratings(self):
        """Test multiple ratings update counts correctly"""
        CommentRating.objects.create(
            comment=self.comment,
            user_id='user456',
            firstname='Jane',
            lastname='Smith',
            role='User',
            rating=True
        )
        
        CommentRating.objects.create(
            comment=self.comment,
            user_id='user789',
            firstname='Bob',
            lastname='Jones',
            role='User',
            rating=False
        )
        
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.thumbs_up_count, 1)
        self.assertEqual(self.comment.thumbs_down_count, 1)
    
    def test_unique_user_rating(self):
        """Test that a user can only rate a comment once"""
        CommentRating.objects.create(
            comment=self.comment,
            user_id='user456',
            firstname='Jane',
            lastname='Smith',
            role='User',
            rating=True
        )
        
        # Try to create duplicate rating
        with self.assertRaises(Exception):
            CommentRating.objects.create(
                comment=self.comment,
                user_id='user456',
                firstname='Jane',
                lastname='Smith',
                role='User',
                rating=False
            )
