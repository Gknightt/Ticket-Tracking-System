"""
Workflow and step-level analytics views
"""
from django.db.models import Count, F, Case, When, Avg, DurationField, IntegerField
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from authentication import JWTCookieAuthentication

from task.models import Task, TaskItem, TaskItemHistory
from workflow.models import Workflows
from step.models import Steps

from .serializers import (
    WorkflowMetricsSerializer,
    StepPerformanceSerializer,
    DepartmentAnalyticsSerializer,
)


class WorkflowMetricsView(APIView):
    """Workflow performance metrics"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            department_filter = request.query_params.get('department', None)
            workflow_id_filter = request.query_params.get('workflow_id', None)

            workflows = Workflows.objects.all()

            if department_filter:
                workflows = workflows.filter(department=department_filter)

            if workflow_id_filter:
                workflows = workflows.filter(workflow_id=workflow_id_filter)

            data = []
            for workflow in workflows:
                tasks = Task.objects.filter(workflow_id=workflow.workflow_id)
                
                total = tasks.count()
                completed = tasks.filter(status='completed').count()
                pending = tasks.filter(status='pending').count()
                in_progress = tasks.filter(status='in progress').count()

                completion_rate = (completed / total * 100) if total > 0 else 0

                # Average completion time
                avg_comp = tasks.filter(
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

                avg_hours = None
                if avg_comp['avg_hours']:
                    avg_hours = avg_comp['avg_hours'].total_seconds() / 3600

                data.append({
                    'workflow_id': workflow.workflow_id,
                    'workflow_name': workflow.name,
                    'total_tasks': total,
                    'completed_tasks': completed,
                    'pending_tasks': pending,
                    'in_progress_tasks': in_progress,
                    'completion_rate': round(completion_rate, 2),
                    'avg_completion_hours': round(avg_hours, 2) if avg_hours else None,
                    'department': workflow.department,
                    'category': workflow.category,
                })

            # Sort by completion rate (descending)
            data.sort(key=lambda x: x['completion_rate'], reverse=True)

            serializer = WorkflowMetricsSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StepPerformanceView(APIView):
    """Step-level performance metrics"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            workflow_id_filter = request.query_params.get('workflow_id', None)

            steps = Steps.objects.all()

            if workflow_id_filter:
                steps = steps.filter(workflow_id=workflow_id_filter)

            data = []
            for step in steps:
                tasks_at_step = Task.objects.filter(current_step=step.step_id)
                
                total = tasks_at_step.count()
                completed = tasks_at_step.filter(status='completed').count()
                escalated = TaskItem.objects.filter(
                    task__current_step=step.step_id,
                    taskitemhistory_set__status='escalated'
                ).distinct().count()

                # Average time at step
                avg_time = tasks_at_step.filter(
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

                avg_hours = None
                if avg_time['avg_hours']:
                    avg_hours = avg_time['avg_hours'].total_seconds() / 3600

                # Get role name
                role_name = step.role_id.name if step.role_id else 'Unknown'

                data.append({
                    'step_id': step.step_id,
                    'step_name': step.name,
                    'workflow_id': step.workflow_id.workflow_id,
                    'total_tasks': total,
                    'completed_tasks': completed,
                    'escalated_tasks': escalated,
                    'avg_time_hours': round(avg_hours, 2) if avg_hours else None,
                    'role_name': role_name,
                })

            serializer = StepPerformanceSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DepartmentAnalyticsView(APIView):
    """Department-level analytics"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get all departments from workflows
            departments = Task.objects.values(
                dept=F('workflow_id__department')
            ).distinct()

            data = []
            for dept_obj in departments:
                dept = dept_obj['dept']
                if not dept:
                    continue

                tasks = Task.objects.filter(workflow_id__department=dept)
                
                total = tasks.count()
                completed = tasks.filter(status='completed').count()
                completion_rate = (completed / total * 100) if total > 0 else 0

                # Average resolution time
                avg_res = tasks.filter(
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

                avg_hours = None
                if avg_res['avg_hours']:
                    avg_hours = avg_res['avg_hours'].total_seconds() / 3600

                data.append({
                    'department': dept,
                    'total_tickets': total,
                    'completed_tickets': completed,
                    'completion_rate': round(completion_rate, 2),
                    'avg_resolution_hours': round(avg_hours, 2) if avg_hours else None,
                })

            serializer = DepartmentAnalyticsSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
