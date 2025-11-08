from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiExample

from .models import Comment, CommentRating, DocumentStorage, CommentDocument
from .serializers import CommentSerializer, CommentRatingSerializer
from .permissions import CommentPermission
from .services import CommentNotificationService, DocumentAttachmentService
from tickets.models import Ticket


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for comments on tickets with document attachment support
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    lookup_field = 'comment_id'
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [CommentPermission]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notification_service = CommentNotificationService()
    
    def get_queryset(self):
        """Dynamic queryset filtering"""
        qs = Comment.objects.all()
        
        # Filter to top-level comments for list views
        if self.action == 'list':
            qs = qs.filter(parent=None)
            ticket_id = self.request.query_params.get('ticket_id')
            if ticket_id:
                qs = qs.filter(ticket__ticket_id=ticket_id)
        
        return qs.order_by('-created_at')
    
    @action(detail=False, methods=['get'], url_path='by-ticket/(?P<ticket_id>[^/.]+)')
    def comments_by_ticket(self, request, ticket_id=None):
        """Get all comments for a specific ticket ID"""
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id)
            comments = Comment.objects.filter(ticket=ticket, parent=None).order_by('-created_at')
            serializer = self.get_serializer(comments, many=True)
            return Response(serializer.data)
        except Ticket.DoesNotExist:
            return Response(
                {"error": f"Ticket with ID {ticket_id} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string'},
                    'firstname': {'type': 'string'},
                    'lastname': {'type': 'string'},
                    'role': {'type': 'string'},
                    'content': {'type': 'string', 'description': 'Content of the reply'},
                    'documents': {'type': 'array', 'items': {'type': 'string', 'format': 'binary'}},
                },
                'required': ['user_id', 'firstname', 'lastname', 'role', 'content']
            }
        }
    )
    @action(detail=True, methods=['post'])
    def reply(self, request, comment_id=None):
        """Add a reply to an existing comment with optional document attachments"""
        parent_comment = self.get_object()
        
        data = request.data.copy()
        data['ticket_id'] = parent_comment.ticket.ticket_id
        data['parent'] = parent_comment.id
        
        # Validate required fields
        required_fields = ['user_id', 'firstname', 'lastname', 'role']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return Response(
                {field: "This field is required" for field in missing_fields},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            reply = serializer.save()
            
            # Handle document attachments
            DocumentAttachmentService.handle_document_attachments(request, reply, data)
            
            # Send notification
            self.notification_service.send_notification(reply, action='reply')
            
            reply_serializer = CommentSerializer(reply, context={'request': request})
            return Response(reply_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def create(self, request, *args, **kwargs):
        """Override create to handle document attachments"""
        uploaded_files = request.FILES.getlist('documents') if 'documents' in request.FILES else []
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save()
            
            # Handle file attachments
            if uploaded_files:
                DocumentAttachmentService.attach_files_to_comment(
                    comment, uploaded_files, request.data
                )
            
            # Send notification
            self.notification_service.send_notification(comment, action='create')
            
            comment_serializer = CommentSerializer(comment, context={'request': request})
            return Response(comment_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string'},
                    'firstname': {'type': 'string'},
                    'lastname': {'type': 'string'},
                    'role': {'type': 'string'},
                    'documents': {'type': 'array', 'items': {'type': 'string', 'format': 'binary'}},
                },
                'required': ['user_id', 'firstname', 'lastname', 'role', 'documents']
            }
        }
    )
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def attach_document(self, request, comment_id=None):
        """Attach documents to an existing comment"""
        comment = self.get_object()
        
        # Validate required fields
        required_fields = ['user_id', 'firstname', 'lastname', 'role']
        missing_fields = [field for field in required_fields if field not in request.data]
        
        if missing_fields:
            return Response(
                {field: "This field is required" for field in missing_fields},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        files = request.FILES.getlist('documents')
        if not files:
            return Response(
                {"documents": "At least one file is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_data = {
            'user_id': request.data.get('user_id'),
            'firstname': request.data.get('firstname'),
            'lastname': request.data.get('lastname')
        }
        
        attached_documents, errors = DocumentAttachmentService.attach_files_to_comment(
            comment, files, user_data
        )
        
        # Send notification
        self.notification_service.send_notification(comment, action='attach_document')
        
        # Return updated comment
        comment_serializer = CommentSerializer(comment, context={'request': request})
        response_data = comment_serializer.data
        response_data['attachment_results'] = {
            'attached': attached_documents,
            'errors': errors
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], url_path='detach-document/(?P<document_id>[^/.]+)')
    def detach_document(self, request, comment_id=None, document_id=None):
        """Detach a document from a comment"""
        comment = self.get_object()
        
        try:
            comment_doc = CommentDocument.objects.get(
                comment=comment,
                document_id=document_id
            )
            
            # Check permissions
            user_id = request.query_params.get('user_id')
            if user_id and comment_doc.attached_by_user_id != user_id:
                return Response(
                    {"error": "You can only detach documents you attached"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            document_name = comment_doc.document.original_filename
            comment_doc.delete()
            
            # Send notification
            self.notification_service.send_notification(comment, action='detach_document')
            
            return Response({
                "message": f"Document '{document_name}' detached successfully"
            }, status=status.HTTP_200_OK)
            
        except CommentDocument.DoesNotExist:
            return Response(
                {"error": "Document attachment not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path='download-document/(?P<document_id>[^/.]+)')
    def download_document(self, request, document_id=None):
        """Download a document by ID"""
        try:
            document = DocumentStorage.objects.get(id=document_id)
            
            from django.http import FileResponse
            response = FileResponse(
                document.file_path.open('rb'),
                as_attachment=True,
                filename=document.original_filename
            )
            response['Content-Type'] = document.content_type
            return response
            
        except DocumentStorage.DoesNotExist:
            raise Http404("Document not found")
    
    @extend_schema(
        request=CommentRatingSerializer,
        examples=[
            OpenApiExample(
                'Rate Comment',
                value={
                    'user_id': '123',
                    'firstname': 'John',
                    'lastname': 'Doe',
                    'role': 'Customer',
                    'rating': True
                }
            )
        ]
    )
    @action(detail=True, methods=['post'])
    def rate(self, request, comment_id=None):
        """Rate a comment (thumbs up/down)"""
        comment = self.get_object()
        
        rating_data = request.data.copy()
        rating_data['comment'] = comment.id
        
        # Check for existing rating
        try:
            existing_rating = CommentRating.objects.get(
                comment=comment,
                user_id=rating_data.get('user_id')
            )
            serializer = CommentRatingSerializer(existing_rating, data=rating_data, partial=True)
        except CommentRating.DoesNotExist:
            serializer = CommentRatingSerializer(data=rating_data)
        
        if serializer.is_valid():
            serializer.save()
            
            # Send notification
            self.notification_service.send_notification(comment, action='rate')
            
            comment_serializer = CommentSerializer(comment, context={'request': request})
            return Response({
                'message': 'Rating updated successfully',
                'comment': comment_serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentRatingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for comment ratings
    """
    queryset = CommentRating.objects.all()
    serializer_class = CommentRatingSerializer
    permission_classes = [CommentPermission]
    
    def get_queryset(self):
        """Filter ratings by comment if comment_id is provided"""
        queryset = CommentRating.objects.all()
        comment_id = self.request.query_params.get('comment_id', None)
        
        if comment_id is not None:
            try:
                comment = Comment.objects.get(comment_id=comment_id)
                queryset = queryset.filter(comment=comment)
            except Comment.DoesNotExist:
                queryset = CommentRating.objects.none()
                
        return queryset
    
    @action(detail=False, methods=['get'], url_path='by-comment/(?P<comment_id>[^/.]+)')
    def ratings_by_comment(self, request, comment_id=None):
        """Get all ratings for a specific comment ID"""
        try:
            comment = Comment.objects.get(comment_id=comment_id)
            ratings = CommentRating.objects.filter(comment=comment)
            
            serializer = self.get_serializer(ratings, many=True)
            return Response({
                'comment_id': comment_id,
                'total_ratings': ratings.count(),
                'thumbs_up_count': ratings.filter(rating=True).count(),
                'thumbs_down_count': ratings.filter(rating=False).count(),
                'ratings': serializer.data
            })
        except Comment.DoesNotExist:
            return Response(
                {"error": f"Comment with ID {comment_id} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )