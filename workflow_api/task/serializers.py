from rest_framework import serializers
from .models import Task

# task/serializers.py
from rest_framework import serializers
from task.models import Task
from tickets.serializers import WorkflowTicketSerializer

class TaskSerializer(serializers.ModelSerializer):
    ticket = WorkflowTicketSerializer(source='ticket_id', read_only=True)  # ✅ display full ticket data

    class Meta:
        model = Task
        fields = ['task_id', 'workflow_id', 'ticket', 'fetched_at']  # customize as needed
