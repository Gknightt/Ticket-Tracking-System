from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Comment, CommentDocument, DocumentStorage
from .serializers import CommentSerializer
import logging

logger = logging.getLogger(__name__)


class CommentNotificationService:
    """
    Service class for handling comment notifications via WebSocket
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_notification(self, comment, action='create'):
        """Send WebSocket notification for comment updates"""
        if self.channel_layer:
            ticket_id = comment.ticket.ticket_id
            room_group_name = f'comments_{ticket_id}'
            
            serializer = CommentSerializer(comment)
            
            async_to_sync(self.channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'comment_message',
                    'message': serializer.data,
                    'action': action
                }
            )


class DocumentAttachmentService:
    """
    Service class for handling document attachments to comments
    """
    
    @staticmethod
    def attach_files_to_comment(comment, files, user_data):
        """
        Helper method to attach files to a comment after creation
        """
        user_id = user_data.get('user_id')
        firstname = user_data.get('firstname')
        lastname = user_data.get('lastname')
        
        attached_documents = []
        errors = []
        
        for file_obj in files:
            try:
                # Only process files with actual content
                if file_obj and hasattr(file_obj, 'size') and file_obj.size > 0:
                    # Create or get existing document with deduplication
                    document, created = DocumentStorage.create_from_file(
                        file_obj, user_id, firstname, lastname
                    )
                    
                    # Attach document to comment (if not already attached)
                    comment_doc, doc_created = CommentDocument.objects.get_or_create(
                        comment=comment,
                        document=document,
                        defaults={
                            'attached_by_user_id': user_id,
                            'attached_by_name': f"{firstname} {lastname}"
                        }
                    )
                    
                    if doc_created:
                        attached_documents.append({
                            'filename': document.original_filename,
                            'size': document.file_size,
                            'hash': document.file_hash,
                            'newly_uploaded': created
                        })
                    else:
                        errors.append(f"Document '{document.original_filename}' is already attached to this comment")
                        
            except Exception as e:
                # Log error but don't fail the comment creation
                logger.error(f"Error attaching document {file_obj.name}: {str(e)}")
                errors.append(f"Error uploading {file_obj.name}: {str(e)}")
        
        return attached_documents, errors
    
    @staticmethod
    def handle_document_attachments(request, comment, data):
        """
        Helper method to handle document attachments for comments
        """
        files = request.FILES.getlist('documents')
        user_data = {
            'user_id': data.get('user_id'),
            'firstname': data.get('firstname'),
            'lastname': data.get('lastname')
        }
        
        return DocumentAttachmentService.attach_files_to_comment(comment, files, user_data)


class CommentService:
    """
    Service class for comment-related business logic
    """
    
    @staticmethod
    def extract_user_data_from_jwt(user):
        """Extract user data from JWT token"""
        return {
            'user_id': user.user_id,
            'firstname': user.full_name.split(' ')[0] if user.full_name else user.username,
            'lastname': user.full_name.split(' ', 1)[1] if user.full_name and ' ' in user.full_name else '',
            'role': user.get_systems()[0] if user.get_systems() else 'User'
        }
    
    @staticmethod
    def create_comment_with_attachments(validated_data, files, user_data):
        """Create a comment with file attachments"""
        # Create comment with JWT user data
        comment = Comment.objects.create(
            ticket_id=validated_data['ticket_id'],
            user_id=user_data['user_id'],
            firstname=user_data['firstname'],
            lastname=user_data['lastname'],
            role=user_data['role'],
            text=validated_data['text']
        )
        
        # Handle attachments using the correct models
        for file in files:
            # Create or get existing document with deduplication
            document, created = DocumentStorage.create_from_file(
                file, user_data['user_id'], user_data['firstname'], user_data['lastname']
            )
            
            # Attach document to comment
            CommentDocument.objects.create(
                comment=comment,
                document=document,
                attached_by_user_id=user_data['user_id'],
                attached_by_name=f"{user_data['firstname']} {user_data['lastname']}"
            )
        
        return comment