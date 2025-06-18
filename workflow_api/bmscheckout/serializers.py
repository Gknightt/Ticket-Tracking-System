# serializers.py

from rest_framework import serializers
from .models import Project

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'id', 'ticket_id', 'title', 'project_summary', 'project_description',
            'performance_notes', 'department', 'fiscal_year', 'submitted_by_name',
            'status', 'performance_start_date', 'performance_end_date',
            'external_system_id', 'items', 'is_approved'
        ]