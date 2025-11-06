from rest_framework.generics import ListAPIView
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from .models import StepInstance
from tickets.serializers import WorkflowTicketSerializer
from authentication import JWTCookieAuthentication, TTSSystemPermission


class SimpleStepInstanceSerializer(serializers.ModelSerializer):
    """
    Simple serializer that returns ticket data directly without employee aggregation
    """
    ticket = WorkflowTicketSerializer(source='task_id.ticket_id', read_only=True)
    step_id = serializers.IntegerField(source='step_transition_id.to_step_id.step_id', read_only=True)
    workflow_id = serializers.CharField(source='task_id.workflow_id.workflow_id', read_only=True)
    task_id = serializers.CharField(source='task_id.task_id', read_only=True)
    step_transition_id = serializers.CharField(source='step_transition_id.transition_id', read_only=True)
    employee_id = serializers.IntegerField(source='user_id', read_only=True)

    class Meta:
        model = StepInstance
        fields = [
            'user_id',
            'step_instance_id', 
            'step_transition_id',
            'step_id',
            'task_id',
            'workflow_id',
            'ticket',
            'employee_id',
            'has_acted'
        ]


class SimpleStepInstanceView(ListAPIView):
    """
    Simple view for listing step instances with ticket information.
    Returns data in a flattened format without employee aggregation.
    Requires JWT authentication with TTS system access and filters by authenticated user's ID.
    """
    serializer_class = SimpleStepInstanceSerializer
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [TTSSystemPermission]

    def get_queryset(self):
        # Get authenticated user's ID
        authenticated_user_id = self.request.user.user_id

        # Base queryset with optimized select_related - only return records for authenticated user
        queryset = StepInstance.objects.select_related(
            'task_id',
            'task_id__ticket_id',
            'task_id__workflow_id',
            'step_transition_id',
            'step_transition_id__to_step_id'
        ).filter(
            user_id=authenticated_user_id  # Only return records for authenticated user
        )

        # Additional filtering from query parameters
        task_id = self.request.query_params.get('task_id')

        if task_id:
            queryset = queryset.filter(task_id=task_id)

        # Sort by latest created
        queryset = queryset.order_by('-created_at')

        return queryset