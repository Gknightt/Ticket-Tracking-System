from rest_framework import serializers
from .models import Task, TaskItem
from tickets.models import WorkflowTicket
from workflow.models import Workflows
from step.models import Steps

class TaskItemSerializer(serializers.ModelSerializer):
    """Serializer for TaskItem (user assignment in a task)"""
    class Meta:
        model = TaskItem
        fields = [
            'task_item_id', 'user_id', 'username', 'email', 'status', 
            'role', 'assigned_on', 'status_updated_on', 'acted_on'
        ]
        read_only_fields = ['task_item_id', 'assigned_on']

class TaskSerializer(serializers.ModelSerializer):
    ticket_subject = serializers.CharField(source='ticket_id.subject', read_only=True)
    workflow_name = serializers.CharField(source='workflow_id.name', read_only=True)
    current_step_name = serializers.CharField(source='current_step.name', read_only=True)
    current_step_role = serializers.CharField(source='current_step.role_id.name', read_only=True)
    assigned_users = serializers.SerializerMethodField()
    assigned_users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'task_id', 'ticket_id', 'workflow_id', 'current_step',
            'status', 'created_at', 'updated_at', 'fetched_at',
            # Read-only fields for easier frontend consumption
            'ticket_subject', 'workflow_name', 'current_step_name', 
            'current_step_role', 'assigned_users', 'assigned_users_count'
        ]
        read_only_fields = ['task_id', 'created_at', 'updated_at']
    
    def get_assigned_users(self, obj):
        """Return all TaskItems for this task"""
        task_items = TaskItem.objects.filter(task=obj)
        return TaskItemSerializer(task_items, many=True).data
    
    def get_assigned_users_count(self, obj):
        """Return the count of assigned users"""
        return TaskItem.objects.filter(task=obj).count()

class TaskCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating tasks manually"""
    class Meta:
        model = Task
        fields = ['ticket_id', 'workflow_id', 'current_step', 'status']
    
    def create(self, validated_data):
        return super().create(validated_data)

class UserAssignmentSerializer(serializers.Serializer):
    """Serializer for user assignment data"""
    user_id = serializers.IntegerField()
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    status = serializers.CharField(max_length=50, default='assigned')
    role = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_status(self, value):
        valid_statuses = ['assigned', 'in_progress', 'completed', 'on_hold', 'acted']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {valid_statuses}")
        return value

class UserAssignmentDetailSerializer(serializers.Serializer):
    """Serializer for individual user assignment in a task"""
    user_id = serializers.IntegerField()
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    status = serializers.CharField(max_length=50)
    assigned_on = serializers.DateTimeField()
    role = serializers.CharField(max_length=100, required=False, allow_blank=True)
    status_updated_on = serializers.DateTimeField(required=False, allow_null=True)
    acted_on = serializers.DateTimeField(required=False, allow_null=True)


class UserTaskListSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying tasks assigned to a specific user.
    Returns task details with related information for easy frontend consumption.
    """
    ticket_subject = serializers.CharField(source='ticket_id.subject', read_only=True)
    ticket_description = serializers.CharField(source='ticket_id.description', read_only=True)
    workflow_name = serializers.CharField(source='workflow_id.name', read_only=True)
    current_step_name = serializers.CharField(source='current_step.name', read_only=True)
    current_step_role = serializers.CharField(source='current_step.role_id.name', read_only=True, allow_null=True)
    user_assignment = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'task_id',
            'ticket_id',
            'ticket_subject',
            'ticket_description',
            'workflow_id',
            'workflow_name',
            'current_step',
            'current_step_name',
            'current_step_role',
            'status',
            'user_assignment',
            'created_at',
            'updated_at',
            'fetched_at',
        ]
        read_only_fields = fields
    
    def get_user_assignment(self, obj):
        """
        Extract the current user's assignment details from TaskItem.
        Called when filtering by user_id.
        """
        user_id = self.context.get('user_id')
        if user_id:
            try:
                task_item = TaskItem.objects.get(task=obj, user_id=user_id)
                return {
                    'user_id': task_item.user_id,
                    'username': task_item.username,
                    'email': task_item.email,
                    'status': task_item.status,
                    'role': task_item.role,
                    'assigned_on': task_item.assigned_on,
                    'status_updated_on': task_item.status_updated_on,
                    'acted_on': task_item.acted_on,
                }
            except TaskItem.DoesNotExist:
                return None
        return None
