"""
Ticket-related analytics views (SLA, priority, age)
"""
from django.db.models import Count, Q, F, Case, When, Avg, DurationField
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from authentication import JWTCookieAuthentication

from task.models import Task

from .serializers import (
    SLAComplianceSerializer,
    PriorityDistributionSerializer,
    TicketAgeAnalyticsSerializer,
)


class SLAComplianceView(APIView):
    """SLA compliance metrics by priority"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get priority filter from query params
            priority_filter = request.query_params.get('priority', None)

            # Query tasks with SLA targets
            query = Task.objects.filter(target_resolution__isnull=False)

            if priority_filter:
                query = query.filter(ticket_id__priority=priority_filter)

            # Group by priority
            priority_stats = query.values(priority=F('ticket_id__priority')).annotate(
                total_tasks=Count('task_id'),
                sla_met=Count(
                    Case(
                        When(resolution_time__lte=F('target_resolution'), then=1),
                        When(status__in=['pending', 'in progress'], then=1),
                        default=None
                    )
                ),
            )

            data = []
            for stat in priority_stats:
                priority = stat['priority'] or 'Unknown'
                total = stat['total_tasks']
                met = stat['sla_met']
                breached = total - met
                compliance_rate = (met / total * 100) if total > 0 else 0

                # Average resolution time
                avg_res = Task.objects.filter(
                    ticket_id__priority=priority,
                    target_resolution__isnull=False,
                    resolution_time__isnull=False
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
                    'priority': priority,
                    'total_tasks': total,
                    'sla_met': met,
                    'sla_breached': breached,
                    'compliance_rate': round(compliance_rate, 2),
                    'avg_resolution_hours': round(avg_hours, 2) if avg_hours else None,
                })

            serializer = SLAComplianceSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PriorityDistributionView(APIView):
    """Priority distribution and metrics"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            priority_data = Task.objects.values(
                priority=F('ticket_id__priority')
            ).annotate(count=Count('task_id'))

            total = sum([item['count'] for item in priority_data])

            data = []
            for item in priority_data:
                priority = item['priority'] or 'Unknown'
                count = item['count']

                # Average resolution for this priority
                avg_res = Task.objects.filter(
                    ticket_id__priority=priority,
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
                    'priority': priority,
                    'count': count,
                    'percentage': round((count / total * 100), 2) if total > 0 else 0,
                    'avg_resolution_hours': round(avg_hours, 2) if avg_hours else None,
                })

            serializer = PriorityDistributionSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TicketAgeAnalyticsView(APIView):
    """Analyze ticket age/aging tickets"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            now = timezone.now()
            
            # Define age buckets
            one_day_ago = now - timedelta(days=1)
            seven_days_ago = now - timedelta(days=7)
            thirty_days_ago = now - timedelta(days=30)
            ninety_days_ago = now - timedelta(days=90)

            buckets = [
                {
                    'name': '0-1 days',
                    'condition': Q(created_at__gte=one_day_ago),
                },
                {
                    'name': '1-7 days',
                    'condition': Q(created_at__gte=seven_days_ago, created_at__lt=one_day_ago),
                },
                {
                    'name': '7-30 days',
                    'condition': Q(created_at__gte=thirty_days_ago, created_at__lt=seven_days_ago),
                },
                {
                    'name': '30-90 days',
                    'condition': Q(created_at__gte=ninety_days_ago, created_at__lt=thirty_days_ago),
                },
                {
                    'name': '90+ days',
                    'condition': Q(created_at__lt=ninety_days_ago),
                },
            ]

            total_tasks = Task.objects.count()
            data = []

            for bucket in buckets:
                count = Task.objects.filter(bucket['condition']).count()
                percentage = (count / total_tasks * 100) if total_tasks > 0 else 0

                data.append({
                    'age_bucket': bucket['name'],
                    'count': count,
                    'percentage': round(percentage, 2),
                })

            serializer = TicketAgeAnalyticsSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
