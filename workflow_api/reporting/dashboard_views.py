"""
Dashboard and summary analytics views
"""
from django.db.models import Count, Q, F, Case, When, DecimalField, IntegerField, Avg, DurationField
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from authentication import JWTCookieAuthentication

from task.models import Task, TaskItem, TaskItemHistory
from tickets.models import WorkflowTicket

from .serializers import (
    DashboardSummarySerializer,
    StatusSummarySerializer,
)


class AnalyticsRootView(APIView):
    """Root view for analytics endpoints"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """
        Analytics API Root
        
        Comprehensive analytics and reporting endpoints for the Ticket Tracking System.
        """
        return Response({
            'message': 'Welcome to Analytics API',
            'endpoints': {
                'dashboard': reverse('reporting:dashboard-summary', request=request),
                'status_summary': reverse('reporting:status-summary', request=request),
                'sla_compliance': reverse('reporting:sla-compliance', request=request),
                'team_performance': reverse('reporting:team-performance', request=request),
                'workflow_metrics': reverse('reporting:workflow-metrics', request=request),
                'step_performance': reverse('reporting:step-performance', request=request),
                'department_analytics': reverse('reporting:department-analytics', request=request),
                'priority_distribution': reverse('reporting:priority-distribution', request=request),
                'ticket_age': reverse('reporting:ticket-age', request=request),
                'assignment_analytics': reverse('reporting:assignment-analytics', request=request),
                'audit_activity': reverse('reporting:audit-activity', request=request),
                'task_item_status': reverse('reporting:task-item-status', request=request),
                'task_item_assignment_origin': reverse('reporting:task-item-origin', request=request),
                'task_item_performance': reverse('reporting:task-item-performance', request=request),
                'task_item_user_performance': reverse('reporting:task-item-user-performance', request=request),
                'task_item_history_trends': reverse('reporting:task-item-history-trends', request=request),
                'task_item_transfer_analytics': reverse('reporting:task-item-transfer', request=request),
            }
        }, status=status.HTTP_200_OK)


class DashboardSummaryView(APIView):
    """Dashboard summary with overall system metrics"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            total_tickets = Task.objects.count()
            completed_tickets = Task.objects.filter(status='completed').count()
            pending_tickets = Task.objects.filter(status='pending').count()
            in_progress_tickets = Task.objects.filter(status='in progress').count()
            
            # SLA Compliance
            total_with_sla = Task.objects.filter(target_resolution__isnull=False).count()
            sla_met = Task.objects.filter(
                Q(status='completed'),
                Q(resolution_time__lte=F('target_resolution')) | Q(resolution_time__isnull=True),
                target_resolution__isnull=False
            ).count()
            sla_compliance_rate = (sla_met / total_with_sla * 100) if total_with_sla > 0 else 0
            
            # Average resolution time
            avg_resolution = Task.objects.filter(
                status='completed',
                resolution_time__isnull=False,
                created_at__isnull=False
            ).aggregate(
                avg_hours=Avg(
                    Case(
                        When(resolution_time__isnull=False, created_at__isnull=False,
                             then=F('resolution_time') - F('created_at')),
                        default=None,
                        output_field=DurationField(),
                    )
                )
            )
            
            avg_resolution_hours = None
            if avg_resolution['avg_hours']:
                avg_resolution_hours = avg_resolution['avg_hours'].total_seconds() / 3600

            # Escalation rate - get latest status from TaskItemHistory
            escalated_count = TaskItem.objects.filter(
                taskitemhistory_set__status='escalated'
            ).distinct().count()
            total_assignments = TaskItem.objects.count()
            escalation_rate = (escalated_count / total_assignments * 100) if total_assignments > 0 else 0

            # Unique metrics
            total_users = TaskItem.objects.values('role_user__user_id').distinct().count()
            from workflow.models import Workflows
            total_workflows = Workflows.objects.count()

            data = {
                'total_tickets': total_tickets,
                'completed_tickets': completed_tickets,
                'pending_tickets': pending_tickets,
                'in_progress_tickets': in_progress_tickets,
                'sla_compliance_rate': round(sla_compliance_rate, 2),
                'avg_resolution_time_hours': round(avg_resolution_hours, 2) if avg_resolution_hours else None,
                'total_users': total_users,
                'total_workflows': total_workflows,
                'escalation_rate': round(escalation_rate, 2),
            }

            serializer = DashboardSummarySerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StatusSummaryView(APIView):
    """Task status distribution"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            status_counts = Task.objects.values('status').annotate(count=Count('task_id'))
            total = sum([item['count'] for item in status_counts])

            data = [
                {
                    'status': item['status'],
                    'count': item['count'],
                    'percentage': round((item['count'] / total * 100), 2) if total > 0 else 0
                }
                for item in status_counts
            ]

            serializer = StatusSummarySerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
