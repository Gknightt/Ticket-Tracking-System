"""
Team and user performance analytics views
"""
from django.db.models import Count, F, Case, When, Avg, DurationField
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from authentication import JWTCookieAuthentication

from task.models import Task, TaskItem, TaskItemHistory
from role.models import RoleUsers, Roles
from audit.models import AuditEvent
from datetime import timedelta

from .serializers import (
    TeamPerformanceSerializer,
    AssignmentAnalyticsSerializer,
)


class TeamPerformanceView(APIView):
    """Team/User performance metrics"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            role_filter = request.query_params.get('role', None)
            
            # Get all unique users with task assignments via role_user
            unique_user_ids = list(set(TaskItem.objects.values_list('role_user__user_id', flat=True)))
            unique_user_ids = [uid for uid in unique_user_ids if uid is not None]

            data = []
            for user_id in unique_user_ids:
                # Get user name from RoleUsers model
                user_name = 'Unknown'
                try:
                    user_role = RoleUsers.objects.filter(user_id=user_id).first()
                    user_name = user_role.user_full_name if user_role else 'Unknown'
                except Exception:
                    user_name = 'Unknown'
                
                # Task counts by status
                total_tasks = Task.objects.filter(
                    taskitem__role_user__user_id=user_id
                ).distinct().count()
                
                completed = Task.objects.filter(
                    taskitem__role_user__user_id=user_id,
                    status='completed'
                ).distinct().count()
                
                in_progress = Task.objects.filter(
                    taskitem__role_user__user_id=user_id,
                    status='in progress'
                ).distinct().count()

                completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0

                # Average resolution time
                avg_res = Task.objects.filter(
                    taskitem__role_user__user_id=user_id,
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

                # Escalation count
                escalations = TaskItem.objects.filter(
                    role_user__user_id=user_id,
                    taskitemhistory_set__status='escalated'
                ).distinct().count()

                data.append({
                    'user_id': user_id,
                    'user_name': user_name,
                    'total_tasks': total_tasks,
                    'completed_tasks': completed,
                    'in_progress_tasks': in_progress,
                    'completion_rate': round(completion_rate, 2),
                    'avg_resolution_hours': round(avg_hours, 2) if avg_hours else None,
                    'escalation_count': escalations,
                })

            # Sort by completion rate (descending)
            data.sort(key=lambda x: x['completion_rate'], reverse=True)

            serializer = TeamPerformanceSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssignmentAnalyticsView(APIView):
    """Task assignment analytics by role"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get all unique roles with assignments
            unique_role_ids = list(set(TaskItem.objects.values_list('role_user__role_id', flat=True)))
            unique_role_ids = [rid for rid in unique_role_ids if rid is not None]

            data = []
            for role_id in unique_role_ids:
                role_name = 'Unknown'
                try:
                    role = Roles.objects.get(role_id=role_id)
                    role_name = role.name
                except Roles.DoesNotExist:
                    role_name = 'Unknown'

                # Get assignments for this role
                assignments = TaskItem.objects.filter(
                    role_user__role_id=role_id
                )
                
                total_assignments = assignments.count()
                reassignments = assignments.filter(
                    taskitemhistory_set__status='reassigned'
                ).distinct().count()
                
                # Users in role
                users_in_role = len(set(assignments.values_list('role_user__user_id', flat=True)))
                avg_assignments_per_user = (total_assignments / users_in_role) if users_in_role > 0 else 0

                data.append({
                    'role_name': role_name,
                    'total_assignments': total_assignments,
                    'avg_assignments_per_user': round(avg_assignments_per_user, 2),
                    'total_users_in_role': users_in_role,
                    'reassignment_count': reassignments,
                })

            serializer = AssignmentAnalyticsSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AuditActivityView(APIView):
    """User and system audit activity"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            days = int(request.query_params.get('days', 30))
            cutoff_date = timezone.now() - timedelta(days=days)

            # Activity by user
            user_activity = AuditEvent.objects.filter(
                timestamp__gte=cutoff_date
            ).values('user_id', 'username').annotate(
                action_count=Count('id'),
                last_action=Max('timestamp')
            ).order_by('-action_count')

            # Activity by action type
            action_activity = AuditEvent.objects.filter(
                timestamp__gte=cutoff_date
            ).values('action').annotate(
                count=Count('id')
            ).order_by('-count')

            from django.db.models import Max
            
            return Response({
                'time_period_days': days,
                'total_events': AuditEvent.objects.filter(timestamp__gte=cutoff_date).count(),
                'user_activity': list(user_activity[:20]),  # Top 20 users
                'action_activity': list(action_activity),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
