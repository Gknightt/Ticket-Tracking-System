from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
import logging

from .models import Task, TaskItem
from .serializers import TaskSerializer, UserTaskListSerializer, TaskCreateSerializer
from .utils.assignment import assign_users_for_step
from authentication import JWTCookieAuthentication, MultiSystemPermission
from step.models import Steps, StepTransition

logger = logging.getLogger(__name__)


class UserTaskListView(ListAPIView):
    """
    View to list tasks assigned to the authenticated user.
    """
    
    serializer_class = UserTaskListSerializer
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'workflow_id']
    search_fields = ['ticket_id__subject', 'ticket_id__description']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter tasks to only those assigned to the current user.
        Extended filtering based on query parameters.
        """
        user_id = self.request.user.user_id
        
        # Get all tasks that have this user assigned via TaskItem
        queryset = Task.objects.filter(
            taskitem__user_id=user_id
        ).distinct()
        
        # Apply additional filters from query parameters
        role = self.request.query_params.get('role')
        assignment_status = self.request.query_params.get('assignment_status')
        
        if role:
            # Filter by role - check TaskItems for matching role
            queryset = queryset.filter(taskitem__user_id=user_id, taskitem__role=role)
        
        if assignment_status:
            # Filter by assignment status - check TaskItems for matching status
            queryset = queryset.filter(taskitem__user_id=user_id, taskitem__status=assignment_status)
        
        return queryset.select_related('ticket_id', 'workflow_id', 'current_step').distinct()
    
    def get_serializer_context(self):
        """Add user_id to serializer context for extracting user-specific assignment data"""
        context = super().get_serializer_context()
        context['user_id'] = self.request.user.user_id
        return context


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tasks with authentication.
    
    Actions:
    - list: GET /tasks/ - List all tasks
    - retrieve: GET /tasks/{id}/ - Get task details
    - create: POST /tasks/ - Create new task
    - update: PUT /tasks/{id}/ - Update task
    - partial_update: PATCH /tasks/{id}/ - Partially update task
    - destroy: DELETE /tasks/{id}/ - Delete task
    - my-tasks: GET /tasks/my-tasks/ - Get user's assigned tasks
    - update-user-status: POST /tasks/{id}/update-user-status/ - Update user's task status
    
    Note: Task transitions are handled by a separate endpoint at POST /transitions/
    """
    
    queryset = Task.objects.select_related('ticket_id', 'workflow_id', 'current_step')
    serializer_class = TaskSerializer
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'workflow_id', 'ticket_id']
    search_fields = ['ticket_id__subject', 'ticket_id__ticket_id']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'], url_path='my-tasks')
    def my_tasks(self, request):
        """
        Get all tasks assigned to the current user.
        This is a convenience endpoint that wraps UserTaskListView functionality.
        
        Same query parameters as UserTaskListView apply here.
        """
        user_id = request.user.user_id
        
        # Filter tasks by user ID via TaskItems
        filtered_tasks = Task.objects.filter(
            taskitem__user_id=user_id
        ).select_related('ticket_id', 'workflow_id', 'current_step').distinct()
        
        # Apply pagination if needed
        page = self.paginate_queryset(filtered_tasks)
        if page is not None:
            serializer = UserTaskListSerializer(
                page, 
                many=True, 
                context={**self.get_serializer_context(), 'user_id': user_id}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = UserTaskListSerializer(
            filtered_tasks, 
            many=True, 
            context={**self.get_serializer_context(), 'user_id': user_id}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='update-user-status')
    def update_user_status(self, request, pk=None):
        """
        Update the status of a specific user's assignment in this task.
        
        Request Body:
        {
            "status": "in_progress"  # or "completed", "on_hold", "assigned"
        }
        
        Returns updated task with user assignment details.
        """
        task = self.get_object()
        user_id = request.user.user_id
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'status field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status
        valid_statuses = ['assigned', 'in_progress', 'completed', 'on_hold', 'acted']
        if new_status not in valid_statuses:
            return Response(
                {'error': f'status must be one of: {valid_statuses}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create TaskItem for this user
        try:
            task_item = TaskItem.objects.get(task=task, user_id=user_id)
            task_item.status = new_status
            task_item.save()
        except TaskItem.DoesNotExist:
            return Response(
                {'error': f'User {user_id} is not assigned to this task'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserTaskListSerializer(
            task,
            context={**self.get_serializer_context(), 'user_id': user_id}
        )
        return Response(serializer.data)
