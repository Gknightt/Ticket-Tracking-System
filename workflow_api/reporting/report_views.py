"""
Aggregated reporting views with time filtering support
"""
from django.db.models import Count, Q, F, Case, When, IntegerField, Avg, Min, Max, DurationField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta, datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from authentication import JWTCookieAuthentication

from task.models import Task, TaskItem, TaskItemHistory

from .utils import build_date_range_filters, convert_timedelta_to_hours


class AggregatedTicketsReportView(APIView):
    """Aggregated tickets reporting endpoint with time filtering"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Parse date filters
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            start_display, end_display, filters = build_date_range_filters(start_date_str, end_date_str)
            
            # Build queryset with date filtering
            queryset = Task.objects.filter(**filters)
            
            # Dashboard metrics
            total_tickets = queryset.count()
            completed_tickets = queryset.filter(status='completed').count()
            pending_tickets = queryset.filter(status='pending').count()
            in_progress_tickets = queryset.filter(status='in progress').count()
            
            total_with_sla = queryset.filter(target_resolution__isnull=False).count()
            sla_met = queryset.filter(
                Q(status='completed'),
                Q(resolution_time__lte=F('target_resolution')) | Q(resolution_time__isnull=True),
                target_resolution__isnull=False
            ).count()
            sla_compliance_rate = (sla_met / total_with_sla * 100) if total_with_sla > 0 else 0
            
            # Count completed with resolved status (skip datetime aggregation - not supported in SQLite)
            total_users = queryset.values('taskitem__role_user__user_id').distinct().count()
            total_workflows = queryset.values('workflow_id').distinct().count()
            # Count escalations from TaskItem with escalated origin
            escalated_count = TaskItem.objects.filter(
                task__in=queryset,
                origin='Escalation'
            ).distinct().count()
            escalation_rate = (escalated_count / total_tickets * 100) if total_tickets > 0 else 0
            
            # Status summary - aggregate by status
            status_summary_data = list(queryset.values('status').annotate(count=Count('task_id')).order_by('-count'))
            
            # SLA compliance by priority (skip datetime aggregation)
            sla_compliance = queryset.filter(
                ticket_id__priority__isnull=False
            ).values('ticket_id__priority').annotate(
                total_tasks=Count('task_id'),
                sla_met=Count(Case(
                    When(Q(resolution_time__lte=F('target_resolution')) | Q(resolution_time__isnull=True), then=1),
                    output_field=IntegerField()
                ))
            ).order_by('-total_tasks')
            
            sla_compliance_data = []
            for item in sla_compliance:
                breached = item['total_tasks'] - item['sla_met']
                sla_compliance_data.append({
                    'priority': item['ticket_id__priority'],
                    'total_tasks': item['total_tasks'],
                    'sla_met': item['sla_met'],
                    'sla_breached': breached,
                    'compliance_rate': (item['sla_met'] / item['total_tasks'] * 100) if item['total_tasks'] > 0 else 0,
                })
            
            # Priority distribution
            priority_dist = queryset.values('ticket_id__priority').annotate(count=Count('task_id')).order_by('-count')
            priority_data = []
            for item in priority_dist:
                priority_data.append({
                    'priority': item['ticket_id__priority'],
                    'count': item['count'],
                    'percentage': (item['count'] / total_tickets * 100) if total_tickets > 0 else 0,
                })
            
            # Ticket age
            now = timezone.now()
            age_buckets = [
                ('0-1 days', queryset.filter(created_at__gte=now - timedelta(days=1)).count()),
                ('1-7 days', queryset.filter(created_at__gte=now - timedelta(days=7), created_at__lt=now - timedelta(days=1)).count()),
                ('7-30 days', queryset.filter(created_at__gte=now - timedelta(days=30), created_at__lt=now - timedelta(days=7)).count()),
                ('30-90 days', queryset.filter(created_at__gte=now - timedelta(days=90), created_at__lt=now - timedelta(days=30)).count()),
                ('90+ days', queryset.filter(created_at__lt=now - timedelta(days=90)).count()),
            ]
            
            ticket_age_data = []
            for bucket, count in age_buckets:
                ticket_age_data.append({
                    'age_bucket': bucket,
                    'count': count,
                    'percentage': (count / total_tickets * 100) if total_tickets > 0 else 0,
                })
            
            return Response({
                'date_range': {
                    'start_date': start_display,
                    'end_date': end_display,
                },
                'dashboard': {
                    'total_tickets': total_tickets,
                    'completed_tickets': completed_tickets,
                    'pending_tickets': pending_tickets,
                    'in_progress_tickets': in_progress_tickets,
                    'sla_compliance_rate': sla_compliance_rate,
                    'total_users': total_users,
                    'total_workflows': total_workflows,
                    'escalation_rate': escalation_rate,
                },
                'status_summary': status_summary_data,
                'sla_compliance': sla_compliance_data,
                'priority_distribution': priority_data,
                'ticket_age': ticket_age_data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e), 'type': type(e).__name__}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AggregatedWorkflowsReportView(APIView):
    """Aggregated workflows reporting endpoint with time filtering"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Parse date filters
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            start_display, end_display, filters = build_date_range_filters(start_date_str, end_date_str)
            
            # Build queryset with date filtering
            queryset = Task.objects.filter(**filters)
            
            # Workflow metrics
            workflows = queryset.values('workflow_id', 'workflow_id__name').annotate(
                total_tasks=Count('task_id'),
                completed_tasks=Count(Case(When(status='completed', then=1), output_field=IntegerField())),
                pending_tasks=Count(Case(When(status='pending', then=1), output_field=IntegerField())),
                in_progress_tasks=Count(Case(When(status='in progress', then=1), output_field=IntegerField()))
            ).order_by('-total_tasks')
            
            workflow_data = []
            for wf in workflows:
                total = wf['total_tasks']
                completed = wf['completed_tasks']
                completion_rate = (completed / total * 100) if total > 0 else 0
                workflow_data.append({
                    'workflow_id': wf['workflow_id'],
                    'workflow_name': wf['workflow_id__name'],
                    'total_tasks': total,
                    'completed_tasks': completed,
                    'pending_tasks': wf['pending_tasks'],
                    'in_progress_tasks': wf['in_progress_tasks'],
                    'completion_rate': round(completion_rate, 2),
                })
            
            # Department analytics
            departments = queryset.filter(
                workflow_id__isnull=False
            ).values('workflow_id__department').annotate(
                total_tickets=Count('task_id'),
                completed_tickets=Count(Case(When(status='completed', then=1), output_field=IntegerField()))
            ).order_by('-total_tickets')
            
            department_data = []
            for dept in departments:
                total = dept['total_tickets']
                completed = dept['completed_tickets']
                completion_rate = (completed / total * 100) if total > 0 else 0
                department_data.append({
                    'department': dept['workflow_id__department'],
                    'total_tickets': total,
                    'completed_tickets': completed,
                    'completion_rate': round(completion_rate, 2),
                })
            
            # Step performance (skip avg_time_hours - datetime aggregation not supported in SQLite)
            steps = queryset.filter(
                current_step__isnull=False
            ).values('current_step_id', 'current_step__name', 'workflow_id').annotate(
                total_tasks=Count('task_id'),
                completed_tasks=Count(Case(When(status='completed', then=1), output_field=IntegerField()))
            ).order_by('-total_tasks')
            
            step_data = []
            for step in steps:
                total = step['total_tasks']
                completed = step['completed_tasks']
                completion_rate = (completed / total * 100) if total > 0 else 0
                step_data.append({
                    'step_id': step['current_step_id'],
                    'step_name': step['current_step__name'],
                    'total_tasks': total,
                    'completed_tasks': completed,
                    'completion_rate': round(completion_rate, 2),
                })
            
            return Response({
                'date_range': {
                    'start_date': start_display,
                    'end_date': end_display,
                },
                'workflow_metrics': workflow_data,
                'department_analytics': department_data,
                'step_performance': step_data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e), 'type': type(e).__name__}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AggregatedTasksReportView(APIView):
    """Aggregated task items reporting endpoint with time filtering"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Parse date filters
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            start_display, end_display, filters = build_date_range_filters(start_date_str, end_date_str)
            
            # Build queryset with date filtering
            queryset = TaskItem.objects.filter(**filters)
            
            # Task Item Status Distribution - get LATEST status from taskitemhistory_set only
            # Use Subquery to get only the most recent status for each task item
            latest_status = TaskItemHistory.objects.filter(
                task_item_id=OuterRef('task_item_id')
            ).order_by('-created_at').values('status')[:1]
            
            queryset_with_status = queryset.annotate(
                latest_status=Coalesce(Subquery(latest_status), Value('new'))
            )
            
            status_dist = queryset_with_status.values('latest_status').annotate(
                count=Count('task_item_id', distinct=True)
            ).order_by('-count')
            
            status_data = []
            total_items = queryset.count()
            for item in status_dist:
                count = item['count']
                status_data.append({
                    'status': item['latest_status'],
                    'count': count,
                    'percentage': round((count / total_items * 100), 2) if total_items > 0 else 0,
                })
            
            # Task Item Origin Distribution
            origin_dist = queryset.values('origin').annotate(
                count=Count('task_item_id')
            ).order_by('-count')
            
            origin_data = []
            for item in origin_dist:
                count = item['count']
                origin_data.append({
                    'origin': item['origin'],
                    'count': count,
                    'percentage': round((count / total_items * 100), 2) if total_items > 0 else 0,
                })
            
            # Task Item Performance
            time_to_action = queryset.filter(
                assigned_on__isnull=False,
                acted_on__isnull=False
            ).annotate(
                time_delta=F('acted_on') - F('assigned_on')
            ).aggregate(
                average=Avg('time_delta'),
                minimum=Min('time_delta'),
                maximum=Max('time_delta')
            )
            
            time_to_action_hours = {
                'average': float(time_to_action['average'] / timedelta(hours=1)) if time_to_action['average'] else None,
                'minimum': float(time_to_action['minimum'] / timedelta(hours=1)) if time_to_action['minimum'] else None,
                'maximum': float(time_to_action['maximum'] / timedelta(hours=1)) if time_to_action['maximum'] else None,
            }
            
            # SLA Compliance
            sla_items = queryset.filter(target_resolution__isnull=False)
            
            # Get latest status for each task item to determine SLA compliance
            latest_status_subquery = TaskItemHistory.objects.filter(
                task_item_id=OuterRef('task_item_id')
            ).order_by('-created_at').values('status')[:1]
            
            sla_items_with_status = sla_items.annotate(
                latest_status=Coalesce(Subquery(latest_status_subquery), Value('new'))
            )
            
            # Calculate by status
            status_breakdown = {}
            all_statuses = ['new', 'in progress', 'resolved', 'escalated', 'reassigned']
            
            for status_name in all_statuses:
                status_items = sla_items_with_status.filter(latest_status=status_name)
                on_track = status_items.filter(target_resolution__gt=timezone.now()).count()
                breached = status_items.filter(target_resolution__lte=timezone.now()).count()
                status_breakdown[status_name] = {
                    'count': on_track + breached,
                    'on_track': on_track,
                    'breached': breached,
                }
            
            # Calculate summary
            tasks_on_track = sla_items_with_status.filter(
                latest_status__in=['resolved', 'completed', 'escalated', 'reassigned']
            ).count() + sla_items_with_status.filter(
                latest_status__in=['new', 'in progress'],
                target_resolution__gt=timezone.now()
            ).count()
            
            tasks_breached = sla_items_with_status.filter(
                latest_status__in=['new', 'in progress'],
                target_resolution__lte=timezone.now()
            ).count()
            
            total_sla = sla_items.count()
            compliance_rate = (tasks_on_track / total_sla * 100) if total_sla > 0 else 0
            
            # Ensure all status keys exist with default values
            for status_name in all_statuses:
                if status_name not in status_breakdown:
                    status_breakdown[status_name] = {
                        'count': 0,
                        'on_track': 0,
                        'breached': 0,
                    }
            
            sla_compliance_data = {
                'summary': {
                    'total_tasks_with_sla': total_sla,
                    'tasks_on_track': tasks_on_track,
                    'tasks_breached': tasks_breached,
                    'current_compliance_rate_percent': round(compliance_rate, 1),
                },
                'by_current_status': status_breakdown
            }
            
            performance_data = {
                'time_to_action_hours': time_to_action_hours,
                'resolution_time_hours': {
                    'average': None,
                    'minimum': None,
                    'maximum': None,
                },
                'sla_compliance': sla_compliance_data,
                'active_items': queryset.exclude(taskitemhistory_set__status__in=['resolved', 'reassigned', 'escalated']).count(),
                'overdue_items': queryset.filter(target_resolution__isnull=False, target_resolution__lt=timezone.now()).exclude(taskitemhistory_set__status__in=['resolved', 'reassigned', 'escalated']).count(),
            }
            
            # User Performance
            from role.models import RoleUsers
            user_perf_list = []
            # Get distinct user IDs - convert to set to avoid duplicates
            unique_user_ids = set(queryset.values_list('role_user__user_id', flat=True).distinct())
            for user_id in unique_user_ids:
                user_items = queryset.filter(role_user__user_id=user_id)
                try:
                    user_name = RoleUsers.objects.filter(user_id=user_id).first().user_full_name
                except:
                    user_name = f"User {user_id}"
                
                total_user_items = user_items.count()
                user_items_ids = list(user_items.values_list('task_item_id', flat=True))
                
                status_counts = {}
                for item_id in user_items_ids:
                    latest = TaskItemHistory.objects.filter(
                        task_item_id=item_id
                    ).order_by('-created_at').first()
                    if latest:
                        status_counts[latest.status] = status_counts.get(latest.status, 0) + 1
                
                user_perf_list.append({
                    'user_id': user_id,
                    'user_name': user_name,
                    'total_items': total_user_items,
                    'status_breakdown': status_counts,
                })
            
            # Transfer Analytics
            transferred = queryset.filter(transferred_to__isnull=False).count()
            
            transfers_by_user = queryset.filter(
                transferred_to__isnull=False
            ).values('role_user__user_id', 'role_user__user_full_name').annotate(
                transfer_count=Count('task_item_id')
            ).order_by('-transfer_count')
            
            transfers_to_user = queryset.filter(
                transferred_to__isnull=False
            ).values('transferred_to__user_id', 'transferred_to__user_full_name').annotate(
                received_count=Count('task_item_id')
            ).order_by('-received_count')
            
            escalated = queryset.filter(origin='Escalation').count()
            
            escalations_by_step = queryset.filter(
                origin='Escalation'
            ).values('assigned_on_step__name').annotate(
                escalation_count=Count('task_item_id')
            ).order_by('-escalation_count')
            
            return Response({
                'date_range': {
                    'start_date': start_display,
                    'end_date': end_display,
                },
                'summary': {
                    'total_task_items': total_items,
                },
                'status_distribution': status_data,
                'origin_distribution': origin_data,
                'performance': performance_data,
                'user_performance': user_perf_list,
                'transfer_analytics': {
                    'total_transfers': transferred,
                    'top_transferrers': list(transfers_by_user[:10]),
                    'top_transfer_recipients': list(transfers_to_user[:10]),
                    'total_escalations': escalated,
                    'escalations_by_step': list(escalations_by_step),
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e), 'type': type(e).__name__}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
