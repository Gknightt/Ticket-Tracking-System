"""
Task item analytics views
"""
from django.db.models import Count, F, Case, When, Avg, Min, Max, DurationField, OuterRef, Subquery, Value
from django.db.models.functions import TruncDate, Coalesce
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from authentication import JWTCookieAuthentication

from task.models import TaskItem, TaskItemHistory
from role.models import RoleUsers

from .utils import convert_timedelta_to_hours


class TaskItemStatusAnalyticsView(APIView):
    """Task Item Status Distribution and Transitions"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Status distribution from TaskItemHistory
            status_data = TaskItemHistory.objects.values('status').annotate(
                count=Count('task_item_id', distinct=True),
                latest_record=Max('created_at')
            )
            
            total_items = TaskItem.objects.count()
            
            data = []
            for stat in status_data:
                item_status = stat['status']
                count = stat['count']
                data.append({
                    'status': item_status,
                    'count': count,
                    'percentage': round((count / total_items * 100), 2) if total_items > 0 else 0,
                })
            
            return Response({
                'total_task_items': total_items,
                'status_distribution': data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskItemAssignmentOriginAnalyticsView(APIView):
    """Task Item Assignment Origin Analytics (System vs Transferred vs Escalation)"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Distribution by origin
            origin_data = TaskItem.objects.values('origin').annotate(
                count=Count('task_item_id')
            )
            
            total_items = TaskItem.objects.count()
            
            data = []
            for item in origin_data:
                origin = item['origin']
                count = item['count']
                data.append({
                    'origin': origin,
                    'count': count,
                    'percentage': round((count / total_items * 100), 2) if total_items > 0 else 0,
                })
            
            return Response({
                'total_assignments': total_items,
                'origin_distribution': data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskItemPerformanceAnalyticsView(APIView):
    """Task Item Performance: Time-to-Action, Resolution Time, SLA Compliance"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Time-to-action (assigned_on to acted_on)
            time_to_action = TaskItem.objects.filter(
                acted_on__isnull=False,
                assigned_on__isnull=False
            ).aggregate(
                avg_hours=Avg(
                    Case(
                        When(acted_on__isnull=False, assigned_on__isnull=False,
                             then=F('acted_on') - F('assigned_on')),
                        default=None,
                        output_field=DurationField(),
                    )
                ),
                min_hours=Min(
                    Case(
                        When(acted_on__isnull=False, assigned_on__isnull=False,
                             then=F('acted_on') - F('assigned_on')),
                        default=None,
                        output_field=DurationField(),
                    )
                ),
                max_hours=Max(
                    Case(
                        When(acted_on__isnull=False, assigned_on__isnull=False,
                             then=F('acted_on') - F('assigned_on')),
                        default=None,
                        output_field=DurationField(),
                    )
                )
            )
            
            # Resolution time (assigned_on to resolution_time)
            resolution_time = TaskItem.objects.filter(
                resolution_time__isnull=False,
                assigned_on__isnull=False
            ).aggregate(
                avg_hours=Avg(
                    Case(
                        When(resolution_time__isnull=False, assigned_on__isnull=False,
                             then=F('resolution_time') - F('assigned_on')),
                        default=None,
                        output_field=DurationField(),
                    )
                ),
                min_hours=Min(
                    Case(
                        When(resolution_time__isnull=False, assigned_on__isnull=False,
                             then=F('resolution_time') - F('assigned_on')),
                        default=None,
                        output_field=DurationField(),
                    )
                ),
                max_hours=Max(
                    Case(
                        When(resolution_time__isnull=False, assigned_on__isnull=False,
                             then=F('resolution_time') - F('assigned_on')),
                        default=None,
                        output_field=DurationField(),
                    )
                )
            )
            
            # SLA compliance
            sla_targets = TaskItem.objects.filter(
                target_resolution__isnull=False
            ).count()
            sla_met = TaskItem.objects.filter(
                target_resolution__isnull=False,
                resolution_time__lte=F('target_resolution')
            ).count()
            sla_breached = sla_targets - sla_met
            sla_compliance = (sla_met / sla_targets * 100) if sla_targets > 0 else 0
            
            # Active items (not yet resolved)
            active_items = TaskItem.objects.filter(
                taskitemhistory_set__status__in=['new', 'in progress']
            ).distinct().count()
            
            # Overdue items
            overdue_items = TaskItem.objects.filter(
                target_resolution__lt=timezone.now(),
                taskitemhistory_set__status__in=['new', 'in progress']
            ).distinct().count()
            
            return Response({
                'time_to_action_hours': {
                    'average': convert_timedelta_to_hours(time_to_action['avg_hours']),
                    'minimum': convert_timedelta_to_hours(time_to_action['min_hours']),
                    'maximum': convert_timedelta_to_hours(time_to_action['max_hours']),
                },
                'resolution_time_hours': {
                    'average': convert_timedelta_to_hours(resolution_time['avg_hours']),
                    'minimum': convert_timedelta_to_hours(resolution_time['min_hours']),
                    'maximum': convert_timedelta_to_hours(resolution_time['max_hours']),
                },
                'sla_compliance': {
                    'total_with_sla': sla_targets,
                    'sla_met': sla_met,
                    'sla_breached': sla_breached,
                    'compliance_rate': round(sla_compliance, 2),
                },
                'active_items': active_items,
                'overdue_items': overdue_items,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskItemUserPerformanceAnalyticsView(APIView):
    """Per-User Task Item Performance"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get unique users from task items
            users = RoleUsers.objects.filter(
                taskitem__isnull=False
            ).values('user_id', 'user_full_name').distinct()
            
            data = []
            for user_info in users:
                user_id = user_info['user_id']
                user_name = user_info['user_full_name']
                
                items = TaskItem.objects.filter(role_user__user_id=user_id)
                total = items.count()
                
                # Get latest status for each item from history
                items_ids = list(items.values_list('task_item_id', flat=True))
                
                # Count by latest status (most recent history entry)
                latest_statuses = {}
                for item_id in items_ids:
                    latest_history = TaskItemHistory.objects.filter(
                        task_item_id=item_id
                    ).order_by('-created_at').first()
                    if latest_history:
                        status_name = latest_history.status
                        latest_statuses[status_name] = latest_statuses.get(status_name, 0) + 1
                
                new_count = latest_statuses.get('new', 0)
                in_progress = latest_statuses.get('in progress', 0)
                resolved = latest_statuses.get('resolved', 0)
                reassigned = latest_statuses.get('reassigned', 0)
                escalated = latest_statuses.get('escalated', 0)
                
                # Breached: items where target_resolution < now AND status is NOT resolved/reassigned/escalated
                breached = items.filter(
                    target_resolution__isnull=False,
                    target_resolution__lt=timezone.now()
                ).exclude(
                    taskitemhistory_set__status__in=['resolved', 'reassigned', 'escalated']
                ).distinct().count()
                
                # Time metrics - average time to action
                avg_action_time = items.filter(
                    acted_on__isnull=False,
                    assigned_on__isnull=False
                ).aggregate(
                    avg=Avg(F('acted_on') - F('assigned_on'), output_field=DurationField())
                )
                
                avg_action_hours = None
                if avg_action_time['avg']:
                    avg_action_hours = convert_timedelta_to_hours(avg_action_time['avg'])
                
                data.append({
                    'user_id': user_id,
                    'user_name': user_name,
                    'total_items': total,
                    'new': new_count,
                    'in_progress': in_progress,
                    'resolved': resolved,
                    'reassigned': reassigned,
                    'escalated': escalated,
                    'breached': breached,
                    'resolution_rate': round((resolved / total * 100), 2) if total > 0 else 0,
                    'escalation_rate': round((escalated / total * 100), 2) if total > 0 else 0,
                    'breach_rate': round((breached / total * 100), 2) if total > 0 else 0,
                    'avg_action_time_hours': avg_action_hours,
                })
            
            return Response(sorted(data, key=lambda x: x['total_items'], reverse=True), 
                          status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskItemHistoryTrendAnalyticsView(APIView):
    """Task Item Status Trends Over Time"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            days = int(request.query_params.get('days', 30))
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # Group by date and status using TruncDate
            trends = TaskItemHistory.objects.filter(
                created_at__gte=cutoff_date
            ).annotate(
                date=TruncDate('created_at')
            ).values('date', 'status').annotate(
                count=Count('task_item_history_id')
            ).order_by('date', 'status')
            
            # Organize by date
            data_by_date = {}
            for trend in trends:
                date_str = str(trend['date'])
                if date_str not in data_by_date:
                    data_by_date[date_str] = {}
                data_by_date[date_str][trend['status']] = trend['count']
            
            # Convert to list format
            data = []
            for date, statuses in sorted(data_by_date.items()):
                data.append({
                    'date': date,
                    'statuses': statuses,
                })
            
            return Response({
                'time_period_days': days,
                'trends': data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskItemTransferAnalyticsView(APIView):
    """Task Item Transfer and Escalation Analytics"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Transfers
            transferred = TaskItem.objects.filter(
                transferred_to__isnull=False
            ).count()
            
            # Transfers by origin user
            transfers_by_user = TaskItem.objects.filter(
                transferred_to__isnull=False
            ).values('role_user__user_id', 'role_user__user_full_name').annotate(
                transfer_count=Count('task_item_id')
            ).order_by('-transfer_count')
            
            # Transfers by destination user
            transfers_to_user = TaskItem.objects.filter(
                transferred_to__isnull=False
            ).values('transferred_to__user_id', 'transferred_to__user_full_name').annotate(
                received_count=Count('task_item_id')
            ).order_by('-received_count')
            
            # Escalations
            escalated = TaskItem.objects.filter(
                origin='Escalation'
            ).count()
            
            escalations_by_step = TaskItem.objects.filter(
                origin='Escalation'
            ).values('assigned_on_step__name').annotate(
                escalation_count=Count('task_item_id')
            ).order_by('-escalation_count')
            
            return Response({
                'total_transfers': transferred,
                'top_transferrers': list(transfers_by_user[:10]),
                'top_transfer_recipients': list(transfers_to_user[:10]),
                'total_escalations': escalated,
                'escalations_by_step': list(escalations_by_step),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
