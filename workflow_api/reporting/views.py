from django.db.models import Count, Q, F, Case, When, IntegerField, Avg, Max, Min, OuterRef, Subquery, Value
from django.db.models.functions import TruncDate, Coalesce
from django.utils import timezone
from datetime import timedelta, datetime
from functools import wraps
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from authentication import JWTCookieAuthentication

from task.models import Task, TaskItem, TaskItemHistory
from tickets.models import WorkflowTicket
from workflow.models import Workflows
from step.models import Steps


# ==================== HELPER UTILITIES ====================

def parse_date(date_str, end_of_day=False):
    """Parse date string to timezone-aware datetime. Returns None if invalid."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d').date()
        time_part = datetime.max.time() if end_of_day else datetime.min.time()
        return timezone.make_aware(datetime.combine(dt, time_part))
    except ValueError:
        return None


def apply_date_filter(queryset, request, date_field='created_at'):
    """Apply start/end date filters to queryset."""
    start_date = parse_date(request.query_params.get('start_date'))
    end_date = parse_date(request.query_params.get('end_date'), end_of_day=True)
    
    if start_date:
        queryset = queryset.filter(**{f'{date_field}__gte': start_date})
    if end_date:
        queryset = queryset.filter(**{f'{date_field}__lte': end_date})
    return queryset


def get_date_params(request):
    """Extract date parameters from request for passing to sub-endpoints."""
    return {
        'start_date': request.query_params.get('start_date'),
        'end_date': request.query_params.get('end_date'),
    }


def get_date_range_display(request):
    """Get date range display values for response."""
    return {
        'start_date': request.query_params.get('start_date') or 'all time',
        'end_date': request.query_params.get('end_date') or 'all time',
    }


def build_base_response(request, data):
    """Build standard response with date range info."""
    return {
        'date_range': get_date_range_display(request),
        **data
    }


def paginate_queryset(queryset, request, order_by='-created_at'):
    """Apply pagination and return (paginated_queryset, pagination_info)."""
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    total_count = queryset.count() if hasattr(queryset, 'count') else len(queryset)
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    if hasattr(queryset, 'order_by'):
        paginated = queryset.order_by(order_by)[start_idx:end_idx]
    else:
        paginated = queryset[start_idx:end_idx]
    
    return paginated, {
        'total_count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
    }


def paginate_list(items, request):
    """Paginate a list and return (paginated_list, pagination_info)."""
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    total_count = len(items)
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    return items[start_idx:end_idx], {
        'total_count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
    }


def calculate_sla_status(task, now=None):
    """Calculate SLA status for a task."""
    now = now or timezone.now()
    if not task.target_resolution:
        return 'no_sla'
    
    if task.status == 'completed':
        if task.resolution_time and task.resolution_time <= task.target_resolution:
            return 'met'
        return 'breached'
    
    return 'on_track' if task.target_resolution > now else 'at_risk'


def calculate_task_item_sla_status(item, current_status, now=None):
    """Calculate SLA status for a task item."""
    now = now or timezone.now()
    if not item.target_resolution:
        return 'no_sla'
    
    if current_status in ['resolved', 'escalated', 'reassigned']:
        return 'met'
    
    return 'on_track' if item.target_resolution > now else 'at_risk'


def get_latest_status_subquery():
    """Get subquery for latest task item status."""
    return TaskItemHistory.objects.filter(
        task_item_id=OuterRef('task_item_id')
    ).order_by('-created_at').values('status')[:1]


def get_task_item_current_status(item):
    """Get current status from task item's history."""
    latest_history = item.taskitemhistory_set.order_by('-created_at').first()
    return latest_history.status if latest_history else 'new'


def safe_percentage(value, total):
    """Calculate percentage safely, returning 0 if total is 0."""
    return (value / total * 100) if total > 0 else 0


def extract_ticket_data(task):
    """Extract common ticket data from a task."""
    return {
        'task_id': task.task_id,
        'ticket_number': task.ticket_id.ticket_number if task.ticket_id else '',
        'subject': task.ticket_id.ticket_data.get('subject', '') if task.ticket_id else '',
        'status': task.status,
        'priority': task.ticket_id.priority if task.ticket_id else None,
        'workflow_name': task.workflow_id.name if task.workflow_id else None,
        'created_at': task.created_at,
    }


def extract_task_item_data(item, include_status=True):
    """Extract common task item data."""
    data = {
        'task_item_id': item.task_item_id,
        'ticket_number': item.task.ticket_id.ticket_number if item.task and item.task.ticket_id else '',
        'subject': item.task.ticket_id.ticket_data.get('subject', '') if item.task and item.task.ticket_id else '',
        'user_name': item.role_user.user_full_name if item.role_user else None,
        'origin': item.origin,
        'assigned_on': item.assigned_on,
        'step_name': item.assigned_on_step.name if item.assigned_on_step else None,
    }
    if include_status:
        data['status'] = get_task_item_current_status(item)
    return data


# ==================== BASE VIEW CLASS ====================

class BaseReportingView(APIView):
    """Base class for reporting views with common authentication and error handling."""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def handle_exception(self, exc):
        """Common exception handler."""
        return Response(
            {'error': str(exc), 'type': type(exc).__name__},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== ANALYTICS VIEWS ====================

class TicketTrendAnalyticsView(BaseReportingView):
    """Ticket Trends Over Time - based on Task statuses."""

    def get(self, request):
        try:
            days = int(request.query_params.get('days', 30))
            cutoff_date = timezone.now() - timedelta(days=days)
            
            created_trends = Task.objects.filter(
                created_at__gte=cutoff_date
            ).annotate(date=TruncDate('created_at')).values('date').annotate(
                count=Count('task_id')
            ).order_by('date')
            
            resolved_trends = Task.objects.filter(
                status='completed', resolution_time__gte=cutoff_date
            ).annotate(date=TruncDate('resolution_time')).values('date').annotate(
                count=Count('task_id')
            ).order_by('date')
            
            # Merge trends by date
            data_by_date = {}
            for trend in created_trends:
                date_str = str(trend['date'])
                data_by_date.setdefault(date_str, {'created': 0, 'resolved': 0})
                data_by_date[date_str]['created'] = trend['count']
            
            for trend in resolved_trends:
                date_str = str(trend['date'])
                data_by_date.setdefault(date_str, {'created': 0, 'resolved': 0})
                data_by_date[date_str]['resolved'] = trend['count']
            
            data = [{'date': date, **values} for date, values in sorted(data_by_date.items())]
            
            return Response({
                'time_period_days': days,
                'summary': {
                    'total_created': sum(d['created'] for d in data),
                    'total_resolved': sum(d['resolved'] for d in data),
                },
                'trends': data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class TaskItemTrendAnalyticsView(BaseReportingView):
    """Task Item Status Trends Over Time."""

    def get(self, request):
        try:
            days = int(request.query_params.get('days', 30))
            cutoff_date = timezone.now() - timedelta(days=days)
            tracked_statuses = ['new', 'in progress', 'escalated', 'reassigned', 'resolved']
            
            trends = TaskItemHistory.objects.filter(
                created_at__gte=cutoff_date, status__in=tracked_statuses
            ).annotate(date=TruncDate('created_at')).values('date', 'status').annotate(
                count=Count('task_item_history_id')
            ).order_by('date', 'status')
            
            # Organize by date
            data_by_date = {}
            for trend in trends:
                date_str = str(trend['date'])
                data_by_date.setdefault(date_str, {s: 0 for s in tracked_statuses})
                data_by_date[date_str][trend['status']] = trend['count']
            
            data = [{
                'date': date,
                'new': statuses.get('new', 0),
                'in_progress': statuses.get('in progress', 0),
                'escalated': statuses.get('escalated', 0),
                'transferred': statuses.get('reassigned', 0),
                'resolved': statuses.get('resolved', 0),
            } for date, statuses in sorted(data_by_date.items())]
            
            summary = {
                'new': sum(d['new'] for d in data),
                'in_progress': sum(d['in_progress'] for d in data),
                'escalated': sum(d['escalated'] for d in data),
                'transferred': sum(d['transferred'] for d in data),
                'reassigned': sum(d['transferred'] for d in data),
                'resolved': sum(d['resolved'] for d in data),
            }
            
            return Response({
                'time_period_days': days,
                'summary': summary,
                'trends': data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class TicketCategoryAnalyticsView(BaseReportingView):
    """Ticket Category, Sub-Category, and Department Analytics."""

    def get(self, request):
        try:
            queryset = apply_date_filter(WorkflowTicket.objects.all(), request)
            
            category_counts = {}
            sub_category_counts = {}
            department_counts = {}
            category_sub_category_map = {}
            total_tickets = 0
            
            for ticket in queryset:
                ticket_data = ticket.ticket_data or {}
                total_tickets += 1
                
                category = ticket_data.get('category') or ticket_data.get('Category') or 'Uncategorized'
                sub_category = (ticket_data.get('sub_category') or ticket_data.get('subcategory') 
                               or ticket_data.get('SubCategory') or 'Uncategorized')
                department = ticket_data.get('department') or ticket_data.get('Department') or ticket.department or 'Unassigned'
                
                category_counts[category] = category_counts.get(category, 0) + 1
                sub_category_counts[sub_category] = sub_category_counts.get(sub_category, 0) + 1
                department_counts[department] = department_counts.get(department, 0) + 1
                
                category_sub_category_map.setdefault(category, {})
                category_sub_category_map[category][sub_category] = category_sub_category_map[category].get(sub_category, 0) + 1
            
            def to_sorted_list(counts, key_name):
                return [
                    {key_name: k, 'count': v, 'percentage': round(safe_percentage(v, total_tickets), 1)}
                    for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)
                ]
            
            hierarchical_data = [
                {
                    'category': cat,
                    'total': sum(sub_cats.values()),
                    'sub_categories': [{'name': sc, 'count': cnt} for sc, cnt in sorted(sub_cats.items(), key=lambda x: x[1], reverse=True)]
                }
                for cat, sub_cats in sorted(category_sub_category_map.items(), key=lambda x: sum(x[1].values()), reverse=True)
            ]
            
            return Response({
                'total_tickets': total_tickets,
                'by_category': to_sorted_list(category_counts, 'category'),
                'by_sub_category': to_sorted_list(sub_category_counts, 'sub_category'),
                'by_department': to_sorted_list(department_counts, 'department'),
                'hierarchical': hierarchical_data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)



class AggregatedTicketsReportView(BaseReportingView):
    """Aggregated tickets reporting endpoint with time filtering.
    
    DEPRECATED: This endpoint returns all ticket analytics in one call.
    Prefer using the individual endpoints for better performance:
    - /tickets/dashboard/ - KPI metrics
    - /tickets/status/ - Status summary
    - /tickets/priority/ - Priority distribution
    - /tickets/age/ - Ticket age buckets
    - /tickets/sla/ - SLA compliance by priority
    """

    def get(self, request):
        try:
            queryset = apply_date_filter(Task.objects.all(), request)
            total_tickets = queryset.count()
            now = timezone.now()
            
            # Dashboard metrics
            completed_tickets = queryset.filter(status='completed').count()
            pending_tickets = queryset.filter(status='pending').count()
            in_progress_tickets = queryset.filter(status='in progress').count()
            
            total_with_sla = queryset.filter(target_resolution__isnull=False).count()
            sla_met = queryset.filter(
                Q(status='completed'),
                Q(resolution_time__lte=F('target_resolution')) | Q(resolution_time__isnull=True),
                target_resolution__isnull=False
            ).count()
            
            total_users = queryset.values('taskitem__role_user__user_id').distinct().count()
            total_workflows = queryset.values('workflow_id').distinct().count()
            escalated_count = TaskItem.objects.filter(task__in=queryset, origin='Escalation').distinct().count()
            
            # Status summary
            status_summary_data = list(queryset.values('status').annotate(count=Count('task_id')).order_by('-count'))
            
            # SLA compliance by priority
            sla_compliance = queryset.filter(ticket_id__priority__isnull=False).values('ticket_id__priority').annotate(
                total_tasks=Count('task_id'),
                sla_met=Count(Case(
                    When(Q(resolution_time__lte=F('target_resolution')) | Q(resolution_time__isnull=True), then=1),
                    output_field=IntegerField()
                ))
            ).order_by('-total_tasks')
            
            sla_compliance_data = [{
                'priority': item['ticket_id__priority'],
                'total_tasks': item['total_tasks'],
                'sla_met': item['sla_met'],
                'sla_breached': item['total_tasks'] - item['sla_met'],
                'compliance_rate': safe_percentage(item['sla_met'], item['total_tasks']),
            } for item in sla_compliance]
            
            # Priority distribution
            priority_data = [{
                'priority': item['ticket_id__priority'],
                'count': item['count'],
                'percentage': safe_percentage(item['count'], total_tickets),
            } for item in queryset.values('ticket_id__priority').annotate(count=Count('task_id')).order_by('-count')]
            
            # Ticket age buckets
            age_buckets = [
                ('0-1 days', queryset.filter(created_at__gte=now - timedelta(days=1)).count()),
                ('1-7 days', queryset.filter(created_at__gte=now - timedelta(days=7), created_at__lt=now - timedelta(days=1)).count()),
                ('7-30 days', queryset.filter(created_at__gte=now - timedelta(days=30), created_at__lt=now - timedelta(days=7)).count()),
                ('30-90 days', queryset.filter(created_at__gte=now - timedelta(days=90), created_at__lt=now - timedelta(days=30)).count()),
                ('90+ days', queryset.filter(created_at__lt=now - timedelta(days=90)).count()),
            ]
            ticket_age_data = [{'age_bucket': bucket, 'count': count, 'percentage': safe_percentage(count, total_tickets)} for bucket, count in age_buckets]
            
            return Response({
                'date_range': get_date_range_display(request),
                'dashboard': {
                    'total_tickets': total_tickets,
                    'completed_tickets': completed_tickets,
                    'pending_tickets': pending_tickets,
                    'in_progress_tickets': in_progress_tickets,
                    'sla_compliance_rate': safe_percentage(sla_met, total_with_sla),
                    'total_users': total_users,
                    'total_workflows': total_workflows,
                    'escalation_rate': safe_percentage(escalated_count, total_tickets),
                },
                'status_summary': status_summary_data,
                'sla_compliance': sla_compliance_data,
                'priority_distribution': priority_data,
                'ticket_age': ticket_age_data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


# ==================== TICKET ANALYTICS ENDPOINTS (NEW) ====================

class TicketDashboardView(BaseReportingView):
    """Ticket Dashboard KPIs - high-level metrics for tickets."""

    def get(self, request):
        try:
            queryset = apply_date_filter(Task.objects.all(), request)
            total_tickets = queryset.count()
            now = timezone.now()
            
            completed_tickets = queryset.filter(status='completed').count()
            pending_tickets = queryset.filter(status='pending').count()
            in_progress_tickets = queryset.filter(status='in progress').count()
            
            total_with_sla = queryset.filter(target_resolution__isnull=False).count()
            sla_met = queryset.filter(
                Q(status='completed'),
                Q(resolution_time__lte=F('target_resolution')) | Q(resolution_time__isnull=True),
                target_resolution__isnull=False
            ).count()
            
            total_users = queryset.values('taskitem__role_user__user_id').distinct().count()
            total_workflows = queryset.values('workflow_id').distinct().count()
            escalated_count = TaskItem.objects.filter(task__in=queryset, origin='Escalation').distinct().count()
            
            return Response(build_base_response(request, {
                'total_tickets': total_tickets,
                'completed_tickets': completed_tickets,
                'pending_tickets': pending_tickets,
                'in_progress_tickets': in_progress_tickets,
                'sla_compliance_rate': safe_percentage(sla_met, total_with_sla),
                'total_users': total_users,
                'total_workflows': total_workflows,
                'escalation_rate': safe_percentage(escalated_count, total_tickets),
            }), status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class TicketStatusSummaryView(BaseReportingView):
    """Ticket Status Summary - count of tickets by status."""

    def get(self, request):
        try:
            queryset = apply_date_filter(Task.objects.all(), request)
            total_tickets = queryset.count()
            
            status_data = [{
                'status': item['status'],
                'count': item['count'],
                'percentage': safe_percentage(item['count'], total_tickets),
            } for item in queryset.values('status').annotate(count=Count('task_id')).order_by('-count')]
            
            return Response(build_base_response(request, {
                'total_tickets': total_tickets,
                'status_summary': status_data,
            }), status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class TicketPriorityDistributionView(BaseReportingView):
    """Ticket Priority Distribution - count of tickets by priority."""

    def get(self, request):
        try:
            queryset = apply_date_filter(Task.objects.all(), request)
            total_tickets = queryset.count()
            
            priority_data = [{
                'priority': item['ticket_id__priority'],
                'count': item['count'],
                'percentage': safe_percentage(item['count'], total_tickets),
            } for item in queryset.values('ticket_id__priority').annotate(count=Count('task_id')).order_by('-count')]
            
            return Response(build_base_response(request, {
                'total_tickets': total_tickets,
                'priority_distribution': priority_data,
            }), status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class TicketAgeDistributionView(BaseReportingView):
    """Ticket Age Distribution - tickets grouped by age buckets."""

    AGE_BUCKETS = [
        ('0-1 days', timedelta(days=1), None),
        ('1-7 days', timedelta(days=7), timedelta(days=1)),
        ('7-30 days', timedelta(days=30), timedelta(days=7)),
        ('30-90 days', timedelta(days=90), timedelta(days=30)),
        ('90+ days', None, timedelta(days=90)),
    ]

    def get(self, request):
        try:
            queryset = apply_date_filter(Task.objects.all(), request)
            total_tickets = queryset.count()
            now = timezone.now()
            
            age_data = []
            for bucket_name, start_delta, end_delta in self.AGE_BUCKETS:
                filters = {}
                if start_delta:
                    filters['created_at__gte'] = now - start_delta
                if end_delta:
                    filters['created_at__lt'] = now - end_delta
                count = queryset.filter(**filters).count()
                age_data.append({
                    'age_bucket': bucket_name,
                    'count': count,
                    'percentage': safe_percentage(count, total_tickets),
                })
            
            return Response(build_base_response(request, {
                'total_tickets': total_tickets,
                'ticket_age': age_data,
            }), status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class TicketSLAComplianceView(BaseReportingView):
    """Ticket SLA Compliance - compliance metrics grouped by priority."""

    def get(self, request):
        try:
            queryset = apply_date_filter(Task.objects.all(), request)
            total_with_sla = queryset.filter(target_resolution__isnull=False).count()
            
            sla_compliance = queryset.filter(ticket_id__priority__isnull=False).values('ticket_id__priority').annotate(
                total_tasks=Count('task_id'),
                sla_met=Count(Case(
                    When(Q(resolution_time__lte=F('target_resolution')) | Q(resolution_time__isnull=True), then=1),
                    output_field=IntegerField()
                ))
            ).order_by('-total_tasks')
            
            sla_compliance_data = [{
                'priority': item['ticket_id__priority'],
                'total_tasks': item['total_tasks'],
                'sla_met': item['sla_met'],
                'sla_breached': item['total_tasks'] - item['sla_met'],
                'compliance_rate': safe_percentage(item['sla_met'], item['total_tasks']),
            } for item in sla_compliance]
            
            # Overall SLA metrics
            total_sla_met = sum(item['sla_met'] for item in sla_compliance_data)
            total_tasks = sum(item['total_tasks'] for item in sla_compliance_data)
            
            return Response(build_base_response(request, {
                'total_with_sla': total_with_sla,
                'overall_compliance_rate': safe_percentage(total_sla_met, total_tasks),
                'sla_compliance': sla_compliance_data,
            }), status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


# ==================== WORKFLOW ANALYTICS ENDPOINTS (NEW) ====================

class WorkflowMetricsView(BaseReportingView):
    """Workflow Metrics - task counts and completion rates per workflow."""

    def get(self, request):
        try:
            queryset = apply_date_filter(Task.objects.all(), request)
            
            workflows = queryset.values('workflow_id', 'workflow_id__name').annotate(
                total_tasks=Count('task_id'),
                completed_tasks=Count(Case(When(status='completed', then=1), output_field=IntegerField())),
                pending_tasks=Count(Case(When(status='pending', then=1), output_field=IntegerField())),
                in_progress_tasks=Count(Case(When(status='in progress', then=1), output_field=IntegerField()))
            ).order_by('-total_tasks')
            
            workflow_data = [{
                'workflow_id': wf['workflow_id'],
                'workflow_name': wf['workflow_id__name'],
                'total_tasks': wf['total_tasks'],
                'completed_tasks': wf['completed_tasks'],
                'pending_tasks': wf['pending_tasks'],
                'in_progress_tasks': wf['in_progress_tasks'],
                'completion_rate': safe_percentage(wf['completed_tasks'], wf['total_tasks']),
            } for wf in workflows]
            
            return Response(build_base_response(request, {
                'workflow_metrics': workflow_data,
            }), status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class DepartmentAnalyticsView(BaseReportingView):
    """Department Analytics - ticket counts and completion rates per department."""

    def get(self, request):
        try:
            queryset = apply_date_filter(Task.objects.all(), request)
            
            departments = queryset.filter(workflow_id__isnull=False).values('workflow_id__department').annotate(
                total_tickets=Count('task_id'),
                completed_tickets=Count(Case(When(status='completed', then=1), output_field=IntegerField()))
            ).order_by('-total_tickets')
            
            department_data = [{
                'department': dept['workflow_id__department'],
                'total_tickets': dept['total_tickets'],
                'completed_tickets': dept['completed_tickets'],
                'completion_rate': safe_percentage(dept['completed_tickets'], dept['total_tickets']),
            } for dept in departments]
            
            return Response(build_base_response(request, {
                'department_analytics': department_data,
            }), status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class StepPerformanceView(BaseReportingView):
    """Step Performance - task counts per workflow step."""

    def get(self, request):
        try:
            queryset = apply_date_filter(Task.objects.all(), request)
            
            steps = queryset.filter(current_step__isnull=False).values(
                'current_step_id', 'current_step__name', 'workflow_id', 'workflow_id__name'
            ).annotate(
                total_tasks=Count('task_id'),
                completed_tasks=Count(Case(When(status='completed', then=1), output_field=IntegerField()))
            ).order_by('-total_tasks')
            
            step_data = [{
                'step_id': step['current_step_id'],
                'step_name': step['current_step__name'],
                'workflow_id': step['workflow_id'],
                'workflow_name': step['workflow_id__name'],
                'total_tasks': step['total_tasks'],
                'completed_tasks': step['completed_tasks'],
                'completion_rate': safe_percentage(step['completed_tasks'], step['total_tasks']),
            } for step in steps]
            
            return Response(build_base_response(request, {
                'step_performance': step_data,
            }), status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


# ==================== TASK ITEM ANALYTICS ENDPOINTS (NEW) ====================

class TaskItemStatusDistributionView(BaseReportingView):
    """Task Item Status Distribution - count of task items by current status."""

    def get(self, request):
        try:
            queryset = apply_date_filter(TaskItem.objects.all(), request, date_field='assigned_on')
            total_items = queryset.count()
            
            queryset_with_status = queryset.annotate(
                latest_status=Coalesce(Subquery(get_latest_status_subquery()), Value('new'))
            )
            status_data = [{
                'status': item['latest_status'],
                'count': item['count'],
                'percentage': safe_percentage(item['count'], total_items),
            } for item in queryset_with_status.values('latest_status').annotate(
                count=Count('task_item_id', distinct=True)
            ).order_by('-count') if item['latest_status']]
            
            return Response(build_base_response(request, {
                'total_task_items': total_items,
                'status_distribution': status_data,
            }), status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class TaskItemOriginDistributionView(BaseReportingView):
    """Task Item Origin Distribution - count of task items by origin type."""

    def get(self, request):
        try:
            queryset = apply_date_filter(TaskItem.objects.all(), request, date_field='assigned_on')
            total_items = queryset.count()
            
            origin_data = [{
                'origin': item['origin'],
                'count': item['count'],
                'percentage': safe_percentage(item['count'], total_items),
            } for item in queryset.values('origin').annotate(count=Count('task_item_id')).order_by('-count')]
            
            return Response(build_base_response(request, {
                'total_task_items': total_items,
                'origin_distribution': origin_data,
            }), status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class TaskItemPerformanceView(BaseReportingView):
    """Task Item Performance - time to action, SLA compliance, active/overdue items."""

    def _get_time_to_action_hours(self, queryset):
        """Calculate time to action statistics."""
        time_to_action = queryset.filter(
            assigned_on__isnull=False, acted_on__isnull=False
        ).annotate(time_delta=F('acted_on') - F('assigned_on')).aggregate(
            average=Avg('time_delta'), minimum=Min('time_delta'), maximum=Max('time_delta')
        )
        return {
            key: float(val / timedelta(hours=1)) if val else None
            for key, val in time_to_action.items()
        }

    def _get_sla_compliance(self, queryset):
        """Calculate SLA compliance data."""
        sla_items = queryset.filter(target_resolution__isnull=False)
        sla_items_with_status = sla_items.annotate(
            latest_status=Coalesce(Subquery(get_latest_status_subquery()), Value('new'))
        )
        
        all_statuses = ['new', 'in progress', 'resolved', 'escalated', 'reassigned']
        now = timezone.now()
        status_breakdown = {}
        
        for status_name in all_statuses:
            status_items = sla_items_with_status.filter(latest_status=status_name)
            count = status_items.count()
            
            if status_name in ['resolved', 'completed', 'escalated', 'reassigned']:
                status_breakdown[status_name] = {'total': count, 'met_sla': count, 'missed_sla': 0}
            else:
                on_track = status_items.filter(target_resolution__gt=now).count() if count > 0 else 0
                status_breakdown[status_name] = {'total': count, 'on_track': on_track, 'breached': count - on_track}
        
        tasks_on_track = sla_items_with_status.filter(
            latest_status__in=['resolved', 'completed', 'escalated', 'reassigned']
        ).count() + sla_items_with_status.filter(
            latest_status__in=['new', 'in progress'], target_resolution__gt=now
        ).count()
        
        tasks_breached = sla_items_with_status.filter(
            latest_status__in=['new', 'in progress'], target_resolution__lte=now
        ).count()
        
        total_sla = sla_items.count()
        return {
            'summary': {
                'total_tasks_with_sla': total_sla,
                'tasks_on_track': tasks_on_track,
                'tasks_breached': tasks_breached,
                'current_compliance_rate_percent': round(safe_percentage(tasks_on_track, total_sla), 1),
            },
            'by_current_status': status_breakdown
        }

    def get(self, request):
        try:
            queryset = apply_date_filter(TaskItem.objects.all(), request, date_field='assigned_on')
            now = timezone.now()
            
            return Response(build_base_response(request, {
                'time_to_action_hours': self._get_time_to_action_hours(queryset),
                'sla_compliance': self._get_sla_compliance(queryset),
                'active_items': queryset.exclude(taskitemhistory_set__status__in=['resolved', 'reassigned', 'escalated']).count(),
                'overdue_items': queryset.filter(target_resolution__isnull=False, target_resolution__lt=now).exclude(
                    taskitemhistory_set__status__in=['resolved', 'reassigned', 'escalated']
                ).count(),
            }), status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class UserPerformanceView(BaseReportingView):
    """User Performance - metrics for each user handling task items."""

    def get(self, request):
        try:
            queryset = apply_date_filter(TaskItem.objects.all(), request, date_field='assigned_on')
            now = timezone.now()
            
            user_perf_list = []
            unique_user_ids = set(queryset.values_list('role_user__user_id', flat=True).distinct())
            
            for user_id in unique_user_ids:
                user_items = queryset.filter(role_user__user_id=user_id)
                first_item = user_items.first()
                user_name = first_item.role_user.user_full_name if first_item and first_item.role_user else f'User {user_id}'
                total = user_items.count()
                
                user_items_with_status = user_items.annotate(
                    latest_status=Coalesce(Subquery(get_latest_status_subquery()), Value('new'))
                )
                
                counts = {
                    'new': user_items_with_status.filter(latest_status='new').count(),
                    'in_progress': user_items_with_status.filter(latest_status='in progress').count(),
                    'resolved': user_items_with_status.filter(latest_status='resolved').count(),
                    'reassigned': user_items_with_status.filter(latest_status='reassigned').count(),
                    'escalated': user_items_with_status.filter(latest_status='escalated').count(),
                    'breached': user_items_with_status.filter(
                        target_resolution__isnull=False, target_resolution__lt=now
                    ).exclude(latest_status__in=['resolved', 'reassigned', 'escalated']).count(),
                }
                
                user_perf_list.append({
                    'user_id': user_id,
                    'user_name': user_name,
                    'total_items': total,
                    **counts,
                    'resolution_rate': safe_percentage(counts['resolved'], total),
                    'escalation_rate': safe_percentage(counts['escalated'], total),
                    'breach_rate': safe_percentage(counts['breached'], total),
                })
            
            return Response(build_base_response(request, {
                'user_performance': user_perf_list,
            }), status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class TransferAnalyticsView(BaseReportingView):
    """Transfer Analytics - transfer/escalation metrics."""

    def get(self, request):
        try:
            queryset = apply_date_filter(TaskItem.objects.all(), request, date_field='assigned_on')
            
            transferred_qs = queryset.filter(transferred_to__isnull=False)
            
            return Response(build_base_response(request, {
                'total_transfers': transferred_qs.count(),
                'top_transferrers': list(transferred_qs.values(
                    'role_user__user_id', 'role_user__user_full_name'
                ).annotate(transfer_count=Count('task_item_id')).order_by('-transfer_count')[:10]),
                'top_transfer_recipients': list(transferred_qs.values(
                    'transferred_to__user_id', 'transferred_to__user_full_name'
                ).annotate(received_count=Count('task_item_id')).order_by('-received_count')[:10]),
                'total_escalations': queryset.filter(origin='Escalation').count(),
                'escalations_by_step': list(queryset.filter(origin='Escalation').values(
                    'assigned_on_step__name'
                ).annotate(escalation_count=Count('task_item_id')).order_by('-escalation_count')),
            }), status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


# ==================== LEGACY AGGREGATED ENDPOINTS (DEPRECATED) ====================

class AggregatedWorkflowsReportView(BaseReportingView):
    """Aggregated workflows reporting endpoint with time filtering."""

    def get(self, request):
        try:
            queryset = apply_date_filter(Task.objects.all(), request)
            
            # Workflow metrics
            workflows = queryset.values('workflow_id', 'workflow_id__name').annotate(
                total_tasks=Count('task_id'),
                completed_tasks=Count(Case(When(status='completed', then=1), output_field=IntegerField())),
                pending_tasks=Count(Case(When(status='pending', then=1), output_field=IntegerField())),
                in_progress_tasks=Count(Case(When(status='in progress', then=1), output_field=IntegerField()))
            ).order_by('-total_tasks')
            
            workflow_data = [{
                'workflow_id': wf['workflow_id'],
                'workflow_name': wf['workflow_id__name'],
                'total_tasks': wf['total_tasks'],
                'completed_tasks': wf['completed_tasks'],
                'pending_tasks': wf['pending_tasks'],
                'in_progress_tasks': wf['in_progress_tasks'],
                'completion_rate': safe_percentage(wf['completed_tasks'], wf['total_tasks']),
            } for wf in workflows]
            
            # Department analytics
            departments = queryset.filter(workflow_id__isnull=False).values('workflow_id__department').annotate(
                total_tickets=Count('task_id'),
                completed_tickets=Count(Case(When(status='completed', then=1), output_field=IntegerField()))
            ).order_by('-total_tickets')
            
            department_data = [{
                'department': dept['workflow_id__department'],
                'total_tickets': dept['total_tickets'],
                'completed_tickets': dept['completed_tickets'],
                'completion_rate': safe_percentage(dept['completed_tickets'], dept['total_tickets']),
            } for dept in departments]
            
            # Step performance
            steps = queryset.filter(current_step__isnull=False).values(
                'current_step_id', 'current_step__name', 'workflow_id'
            ).annotate(
                total_tasks=Count('task_id'),
                completed_tasks=Count(Case(When(status='completed', then=1), output_field=IntegerField()))
            ).order_by('-total_tasks')
            
            step_data = [{
                'step_id': step['current_step_id'],
                'step_name': step['current_step__name'],
                'workflow_id': step['workflow_id'],
                'total_tasks': step['total_tasks'],
                'completed_tasks': step['completed_tasks'],
            } for step in steps]
            
            return Response({
                'date_range': get_date_range_display(request),
                'workflow_metrics': workflow_data,
                'department_analytics': department_data,
                'step_performance': step_data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class AggregatedTasksReportView(BaseReportingView):
    """Aggregated task items reporting endpoint with time filtering."""

    def _get_time_to_action_hours(self, queryset):
        """Calculate time to action statistics."""
        time_to_action = queryset.filter(
            assigned_on__isnull=False, acted_on__isnull=False
        ).annotate(time_delta=F('acted_on') - F('assigned_on')).aggregate(
            average=Avg('time_delta'), minimum=Min('time_delta'), maximum=Max('time_delta')
        )
        return {
            key: float(val / timedelta(hours=1)) if val else None
            for key, val in time_to_action.items()
        }

    def _get_sla_compliance(self, queryset):
        """Calculate SLA compliance data."""
        sla_items = queryset.filter(target_resolution__isnull=False)
        sla_items_with_status = sla_items.annotate(
            latest_status=Coalesce(Subquery(get_latest_status_subquery()), Value('new'))
        )
        
        all_statuses = ['new', 'in progress', 'resolved', 'escalated', 'reassigned']
        now = timezone.now()
        status_breakdown = {}
        
        for status_name in all_statuses:
            status_items = sla_items_with_status.filter(latest_status=status_name)
            count = status_items.count()
            
            if status_name in ['resolved', 'completed', 'escalated', 'reassigned']:
                status_breakdown[status_name] = {'total': count, 'met_sla': count, 'missed_sla': 0}
            else:
                on_track = status_items.filter(target_resolution__gt=now).count() if count > 0 else 0
                status_breakdown[status_name] = {'total': count, 'on_track': on_track, 'breached': count - on_track}
        
        tasks_on_track = sla_items_with_status.filter(
            latest_status__in=['resolved', 'completed', 'escalated', 'reassigned']
        ).count() + sla_items_with_status.filter(
            latest_status__in=['new', 'in progress'], target_resolution__gt=now
        ).count()
        
        tasks_breached = sla_items_with_status.filter(
            latest_status__in=['new', 'in progress'], target_resolution__lte=now
        ).count()
        
        total_sla = sla_items.count()
        return {
            'summary': {
                'total_tasks_with_sla': total_sla,
                'tasks_on_track': tasks_on_track,
                'tasks_breached': tasks_breached,
                'current_compliance_rate_percent': round(safe_percentage(tasks_on_track, total_sla), 1),
            },
            'by_current_status': status_breakdown
        }

    def _get_user_performance(self, queryset):
        """Calculate user performance metrics."""
        user_perf_list = []
        unique_user_ids = set(queryset.values_list('role_user__user_id', flat=True).distinct())
        now = timezone.now()
        
        for user_id in unique_user_ids:
            user_items = queryset.filter(role_user__user_id=user_id)
            first_item = user_items.first()
            user_name = first_item.role_user.user_full_name if first_item and first_item.role_user else f'User {user_id}'
            total = user_items.count()
            
            user_items_with_status = user_items.annotate(
                latest_status=Coalesce(Subquery(get_latest_status_subquery()), Value('new'))
            )
            
            counts = {
                'new': user_items_with_status.filter(latest_status='new').count(),
                'in_progress': user_items_with_status.filter(latest_status='in progress').count(),
                'resolved': user_items_with_status.filter(latest_status='resolved').count(),
                'reassigned': user_items_with_status.filter(latest_status='reassigned').count(),
                'escalated': user_items_with_status.filter(latest_status='escalated').count(),
                'breached': user_items_with_status.filter(
                    target_resolution__isnull=False, target_resolution__lt=now
                ).exclude(latest_status__in=['resolved', 'reassigned', 'escalated']).count(),
            }
            
            user_perf_list.append({
                'user_id': user_id,
                'user_name': user_name,
                'total_items': total,
                **counts,
                'resolution_rate': safe_percentage(counts['resolved'], total),
                'escalation_rate': safe_percentage(counts['escalated'], total),
                'breach_rate': safe_percentage(counts['breached'], total),
            })
        
        return user_perf_list

    def get(self, request):
        try:
            queryset = apply_date_filter(TaskItem.objects.all(), request, date_field='assigned_on')
            total_items = queryset.count()
            now = timezone.now()
            
            # Status distribution
            queryset_with_status = queryset.annotate(
                latest_status=Coalesce(Subquery(get_latest_status_subquery()), Value('new'))
            )
            status_data = [{
                'status': item['latest_status'],
                'count': item['count'],
                'percentage': safe_percentage(item['count'], total_items),
            } for item in queryset_with_status.values('latest_status').annotate(
                count=Count('task_item_id', distinct=True)
            ).order_by('-count') if item['latest_status']]
            
            # Origin distribution
            origin_data = [{
                'origin': item['origin'],
                'count': item['count'],
                'percentage': safe_percentage(item['count'], total_items),
            } for item in queryset.values('origin').annotate(count=Count('task_item_id')).order_by('-count')]
            
            # Performance data
            performance_data = {
                'time_to_action_hours': self._get_time_to_action_hours(queryset),
                'resolution_time_hours': {'average': None, 'minimum': None, 'maximum': None},
                'sla_compliance': self._get_sla_compliance(queryset),
                'active_items': queryset.exclude(taskitemhistory_set__status__in=['resolved', 'reassigned', 'escalated']).count(),
                'overdue_items': queryset.filter(target_resolution__isnull=False, target_resolution__lt=now).exclude(
                    taskitemhistory_set__status__in=['resolved', 'reassigned', 'escalated']
                ).count(),
            }
            
            # Transfer analytics
            transferred_qs = queryset.filter(transferred_to__isnull=False)
            transfer_analytics = {
                'total_transfers': transferred_qs.count(),
                'top_transferrers': list(transferred_qs.values(
                    'role_user__user_id', 'role_user__user_full_name'
                ).annotate(transfer_count=Count('task_item_id')).order_by('-transfer_count')[:10]),
                'top_transfer_recipients': list(transferred_qs.values(
                    'transferred_to__user_id', 'transferred_to__user_full_name'
                ).annotate(received_count=Count('task_item_id')).order_by('-received_count')[:10]),
                'total_escalations': queryset.filter(origin='Escalation').count(),
                'escalations_by_step': list(queryset.filter(origin='Escalation').values(
                    'assigned_on_step__name'
                ).annotate(escalation_count=Count('task_item_id')).order_by('-escalation_count')),
            }
            
            return Response({
                'date_range': get_date_range_display(request),
                'summary': {'total_task_items': total_items},
                'status_distribution': status_data,
                'origin_distribution': origin_data,
                'performance': performance_data,
                'user_performance': self._get_user_performance(queryset),
                'transfer_analytics': transfer_analytics,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


# ==================== DRILLABLE ENDPOINTS ====================

class DrilldownTicketsByStatusView(BaseReportingView):
    """Drillable endpoint: Get detailed ticket list filtered by status."""

    def get(self, request):
        try:
            status_filter = request.query_params.get('status')
            priority_filter = request.query_params.get('priority')
            workflow_filter = request.query_params.get('workflow_id')

            queryset = Task.objects.select_related('ticket_id', 'workflow_id', 'current_step').all()
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            if priority_filter:
                queryset = queryset.filter(ticket_id__priority=priority_filter)
            if workflow_filter:
                queryset = queryset.filter(workflow_id=workflow_filter)
            
            queryset = apply_date_filter(queryset, request)
            paginated, pagination = paginate_queryset(queryset, request)
            
            now = timezone.now()
            data = []
            for task in paginated:
                sla_status = calculate_sla_status(task, now)
                assigned_users = list(task.taskitem_set.values_list('role_user__user_full_name', flat=True))
                data.append({
                    **extract_ticket_data(task),
                    'department': task.workflow_id.department if task.workflow_id else None,
                    'current_step': task.current_step.name if task.current_step else None,
                    'target_resolution': task.target_resolution,
                    'resolution_time': task.resolution_time,
                    'assigned_users': assigned_users,
                    'sla_status': sla_status,
                })

            return Response({
                **pagination,
                'filters_applied': {
                    'status': status_filter,
                    'priority': priority_filter,
                    'workflow_id': workflow_filter,
                    'start_date': request.query_params.get('start_date'),
                    'end_date': request.query_params.get('end_date'),
                },
                'tickets': data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class DrilldownTicketsByPriorityView(BaseReportingView):
    """Drillable endpoint: Get detailed ticket list filtered by priority."""

    def get(self, request):
        try:
            priority_filter = request.query_params.get('priority')
            status_filter = request.query_params.get('status')

            queryset = Task.objects.select_related('ticket_id', 'workflow_id', 'current_step').all()
            
            if priority_filter:
                queryset = queryset.filter(ticket_id__priority=priority_filter)
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            queryset = apply_date_filter(queryset, request)
            paginated, pagination = paginate_queryset(queryset, request)
            
            now = timezone.now()
            data = [{
                **extract_ticket_data(task),
                'target_resolution': task.target_resolution,
                'sla_status': calculate_sla_status(task, now),
            } for task in paginated]

            return Response({**pagination, 'tickets': data}, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class DrilldownTicketsByAgeView(BaseReportingView):
    """Drillable endpoint: Get detailed ticket list filtered by age bucket."""

    AGE_BUCKET_FILTERS = {
        '0-1 days': lambda now: {'created_at__gte': now - timedelta(days=1)},
        '1-7 days': lambda now: {'created_at__gte': now - timedelta(days=7), 'created_at__lt': now - timedelta(days=1)},
        '7-30 days': lambda now: {'created_at__gte': now - timedelta(days=30), 'created_at__lt': now - timedelta(days=7)},
        '30-90 days': lambda now: {'created_at__gte': now - timedelta(days=90), 'created_at__lt': now - timedelta(days=30)},
        '90+ days': lambda now: {'created_at__lt': now - timedelta(days=90)},
    }

    def get(self, request):
        try:
            age_bucket = request.query_params.get('age_bucket')
            status_filter = request.query_params.get('status')
            now = timezone.now()

            queryset = Task.objects.select_related('ticket_id', 'workflow_id', 'current_step').all()
            
            if age_bucket and age_bucket in self.AGE_BUCKET_FILTERS:
                queryset = queryset.filter(**self.AGE_BUCKET_FILTERS[age_bucket](now))
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            paginated, pagination = paginate_queryset(queryset, request, order_by='created_at')
            
            data = [{
                **extract_ticket_data(task),
                'age_days': (now - task.created_at).days if task.created_at else 0,
            } for task in paginated]

            return Response({**pagination, 'age_bucket': age_bucket, 'tickets': data}, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class DrilldownSLAComplianceView(BaseReportingView):
    """Drillable endpoint: Get detailed SLA compliance data."""

    def get(self, request):
        try:
            sla_status_filter = request.query_params.get('sla_status')
            priority_filter = request.query_params.get('priority')

            queryset = Task.objects.select_related('ticket_id', 'workflow_id').filter(target_resolution__isnull=False)
            if priority_filter:
                queryset = queryset.filter(ticket_id__priority=priority_filter)
            queryset = apply_date_filter(queryset, request)

            now = timezone.now()
            filtered_tasks = []
            
            for task in queryset:
                task_sla_status = calculate_sla_status(task, now)
                
                if not sla_status_filter or task_sla_status == sla_status_filter:
                    time_remaining = time_overdue = None
                    if task.status != 'completed' and task.target_resolution:
                        diff = (task.target_resolution - now).total_seconds() / 3600
                        if diff > 0:
                            time_remaining = round(diff, 2)
                        else:
                            time_overdue = round(abs(diff), 2)
                    
                    filtered_tasks.append({
                        'task_id': task.task_id,
                        'ticket_number': task.ticket_id.ticket_number if task.ticket_id else '',
                        'subject': task.ticket_id.ticket_data.get('subject', '') if task.ticket_id else '',
                        'priority': task.ticket_id.priority if task.ticket_id else None,
                        'status': task.status,
                        'target_resolution': task.target_resolution,
                        'resolution_time': task.resolution_time,
                        'sla_status': task_sla_status,
                        'time_remaining_hours': time_remaining,
                        'time_overdue_hours': time_overdue,
                    })

            paginated, pagination = paginate_list(filtered_tasks, request)
            return Response({**pagination, 'sla_status_filter': sla_status_filter, 'tickets': paginated}, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class DrilldownUserTasksView(BaseReportingView):
    """Drillable endpoint: Get detailed task items for a specific user."""

    def get(self, request):
        try:
            user_id = request.query_params.get('user_id')
            status_filter = request.query_params.get('status')

            if not user_id:
                return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            queryset = TaskItem.objects.select_related(
                'task', 'task__ticket_id', 'role_user', 'assigned_on_step'
            ).filter(role_user__user_id=user_id)
            queryset = apply_date_filter(queryset, request, date_field='assigned_on')

            now = timezone.now()
            filtered_items = []

            for item in queryset:
                current_status = get_task_item_current_status(item)
                if status_filter and current_status != status_filter:
                    continue

                time_to_action = None
                if item.acted_on and item.assigned_on:
                    time_to_action = round((item.acted_on - item.assigned_on).total_seconds() / 3600, 2)

                filtered_items.append({
                    'user_id': user_id,
                    'user_name': item.role_user.user_full_name if item.role_user else f'User {user_id}',
                    'task_item_id': item.task_item_id,
                    'ticket_number': item.task.ticket_id.ticket_number if item.task and item.task.ticket_id else '',
                    'subject': item.task.ticket_id.ticket_data.get('subject', '') if item.task and item.task.ticket_id else '',
                    'status': current_status,
                    'origin': item.origin,
                    'assigned_on': item.assigned_on,
                    'acted_on': item.acted_on,
                    'target_resolution': item.target_resolution,
                    'resolution_time': item.resolution_time,
                    'time_to_action_hours': time_to_action,
                    'sla_status': calculate_task_item_sla_status(item, current_status, now),
                })

            paginated, pagination = paginate_list(filtered_items, request)
            return Response({**pagination, 'user_id': user_id, 'task_items': paginated}, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class DrilldownWorkflowTasksView(BaseReportingView):
    """Drillable endpoint: Get detailed tasks for a specific workflow."""

    def get(self, request):
        try:
            workflow_id = request.query_params.get('workflow_id')
            status_filter = request.query_params.get('status')
            step_id = request.query_params.get('step_id')

            if not workflow_id:
                return Response({'error': 'workflow_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            queryset = Task.objects.select_related('ticket_id', 'workflow_id', 'current_step').filter(workflow_id=workflow_id)
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            if step_id:
                queryset = queryset.filter(current_step_id=step_id)
            queryset = apply_date_filter(queryset, request)

            paginated, pagination = paginate_queryset(queryset, request)
            workflow = Workflows.objects.filter(workflow_id=workflow_id).first()
            workflow_name = workflow.name if workflow else f'Workflow {workflow_id}'

            data = [{
                'workflow_id': int(workflow_id),
                'workflow_name': workflow_name,
                'task_id': task.task_id,
                'ticket_number': task.ticket_id.ticket_number if task.ticket_id else '',
                'subject': task.ticket_id.ticket_data.get('subject', '') if task.ticket_id else '',
                'status': task.status,
                'current_step': task.current_step.name if task.current_step else None,
                'created_at': task.created_at,
                'resolution_time': task.resolution_time,
            } for task in paginated]

            return Response({
                **pagination, 'workflow_id': workflow_id, 'workflow_name': workflow_name, 'tasks': data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class DrilldownStepTasksView(BaseReportingView):
    """Drillable endpoint: Get detailed tasks for a specific step."""

    def get(self, request):
        try:
            step_id = request.query_params.get('step_id')
            status_filter = request.query_params.get('status')

            if not step_id:
                return Response({'error': 'step_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            queryset = Task.objects.select_related('ticket_id', 'workflow_id', 'current_step').filter(current_step_id=step_id)
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            paginated, pagination = paginate_queryset(queryset, request)
            step = Steps.objects.filter(step_id=step_id).first()
            step_name = step.name if step else f'Step {step_id}'

            data = []
            for task in paginated:
                task_item = task.taskitem_set.first()
                data.append({
                    'step_id': int(step_id),
                    'step_name': step_name,
                    'task_id': task.task_id,
                    'ticket_number': task.ticket_id.ticket_number if task.ticket_id else '',
                    'status': task.status,
                    'assigned_user': task_item.role_user.user_full_name if task_item and task_item.role_user else None,
                    'entered_at': task.created_at,
                })

            return Response({**pagination, 'step_id': step_id, 'step_name': step_name, 'tasks': data}, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class DrilldownDepartmentTasksView(BaseReportingView):
    """Drillable endpoint: Get detailed tasks for a specific department."""

    def get(self, request):
        try:
            department = request.query_params.get('department')
            status_filter = request.query_params.get('status')

            if not department:
                return Response({'error': 'department is required'}, status=status.HTTP_400_BAD_REQUEST)

            queryset = Task.objects.select_related('ticket_id', 'workflow_id', 'current_step').filter(workflow_id__department=department)
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            queryset = apply_date_filter(queryset, request)

            paginated, pagination = paginate_queryset(queryset, request)
            data = [{
                **extract_ticket_data(task),
                'current_step': task.current_step.name if task.current_step else None,
            } for task in paginated]

            return Response({**pagination, 'department': department, 'tasks': data}, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class DrilldownTransfersView(BaseReportingView):
    """Drillable endpoint: Get detailed transfer/escalation records."""

    def get(self, request):
        try:
            origin_filter = request.query_params.get('origin')
            user_id = request.query_params.get('user_id')

            queryset = TaskItem.objects.select_related(
                'task', 'task__ticket_id', 'role_user', 'transferred_to', 'assigned_on_step'
            ).exclude(origin='System')

            if origin_filter:
                queryset = queryset.filter(origin=origin_filter)
            if user_id:
                queryset = queryset.filter(Q(role_user__user_id=user_id) | Q(transferred_to__user_id=user_id))
            queryset = apply_date_filter(queryset, request, date_field='assigned_on')

            paginated, pagination = paginate_queryset(queryset, request, order_by='-assigned_on')
            data = [{
                'task_item_id': item.task_item_id,
                'ticket_number': item.task.ticket_id.ticket_number if item.task and item.task.ticket_id else '',
                'from_user': item.role_user.user_full_name if item.role_user else None,
                'to_user': item.transferred_to.user_full_name if item.transferred_to else None,
                'transferred_at': item.assigned_on,
                'origin': item.origin,
                'step_name': item.assigned_on_step.name if item.assigned_on_step else None,
            } for item in paginated]

            return Response({**pagination, 'origin_filter': origin_filter, 'transfers': data}, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class DrilldownTaskItemsByStatusView(BaseReportingView):
    """Drillable endpoint: Get detailed task items filtered by status."""

    def get(self, request):
        try:
            status_filter = request.query_params.get('status')
            queryset = TaskItem.objects.select_related('task', 'task__ticket_id', 'role_user', 'assigned_on_step').all()
            queryset = apply_date_filter(queryset, request, date_field='assigned_on')

            filtered_items = []
            for item in queryset:
                current_status = get_task_item_current_status(item)
                if status_filter and current_status != status_filter:
                    continue
                filtered_items.append({**extract_task_item_data(item, include_status=False), 'status': current_status})

            paginated, pagination = paginate_list(filtered_items, request)
            return Response({**pagination, 'status_filter': status_filter, 'task_items': paginated}, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class DrilldownTaskItemsByOriginView(BaseReportingView):
    """Drillable endpoint: Get detailed task items filtered by origin."""

    def get(self, request):
        try:
            origin_filter = request.query_params.get('origin')
            queryset = TaskItem.objects.select_related('task', 'task__ticket_id', 'role_user', 'assigned_on_step').all()
            if origin_filter:
                queryset = queryset.filter(origin=origin_filter)
            queryset = apply_date_filter(queryset, request, date_field='assigned_on')

            paginated, pagination = paginate_queryset(queryset, request, order_by='-assigned_on')
            data = [{**extract_task_item_data(item)} for item in paginated]

            return Response({**pagination, 'origin_filter': origin_filter, 'task_items': data}, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


# ==================== OPERATIONAL INSIGHTS ====================

class OperationalInsightsView(BaseReportingView):
    """
    Comprehensive operational insights combining workload analysis, 
    anomaly detection, SLA risks, and performance warnings.
    
    Returns aggregated system health metrics and actionable alerts.
    """

    # Configurable thresholds
    THRESHOLDS = {
        # Workload thresholds
        'high_workload_per_user': 10,  # Tasks per user considered high
        'critical_workload_per_user': 15,  # Tasks per user considered critical
        
        # SLA thresholds
        'sla_warning_hours': 4,  # Hours before SLA breach to warn
        'sla_critical_hours': 2,  # Hours before SLA breach considered critical
        'sla_compliance_warning': 80,  # SLA compliance % warning threshold
        'sla_compliance_critical': 60,  # SLA compliance % critical threshold
        
        # Performance thresholds
        'slow_avg_resolution_hours': 48,  # Avg resolution hours considered slow
        'high_escalation_rate': 15,  # Escalation rate % considered high
        'high_transfer_rate': 20,  # Transfer rate % considered high
        
        # Queue thresholds
        'queue_backlog_warning': 20,  # Pending tasks warning threshold
        'queue_backlog_critical': 50,  # Pending tasks critical threshold
        
        # Age thresholds
        'stale_ticket_days': 7,  # Days without activity considered stale
        'aging_ticket_days': 30,  # Days considered aging
    }

    def get(self, request):
        try:
            now = timezone.now()
            queryset = apply_date_filter(Task.objects.all(), request)
            
            # Gather all insights
            workload_alerts = self._analyze_workload(queryset, now)
            sla_alerts = self._analyze_sla_risks(queryset, now)
            performance_alerts = self._analyze_performance(queryset, now)
            anomaly_alerts = self._detect_anomalies(queryset, now)
            queue_alerts = self._analyze_queue_health(queryset, now)
            
            # Combine all alerts
            all_alerts = workload_alerts + sla_alerts + performance_alerts + anomaly_alerts + queue_alerts
            
            # Sort by severity (critical > warning > info)
            severity_order = {'critical': 0, 'warning': 1, 'info': 2}
            all_alerts.sort(key=lambda x: (severity_order.get(x['severity'], 3), x.get('value', 0)))
            
            # Summary counts
            summary = {
                'total_alerts': len(all_alerts),
                'critical_count': sum(1 for a in all_alerts if a['severity'] == 'critical'),
                'warning_count': sum(1 for a in all_alerts if a['severity'] == 'warning'),
                'info_count': sum(1 for a in all_alerts if a['severity'] == 'info'),
            }
            
            # Calculate overall health score (0-100)
            health_score = self._calculate_health_score(summary, queryset)
            
            return Response({
                'generated_at': now.isoformat(),
                'date_range': get_date_range_display(request),
                'health_score': health_score,
                'summary': summary,
                'alerts': all_alerts,
                'thresholds': self.THRESHOLDS,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)

    def _analyze_workload(self, queryset, now):
        """Analyze workload distribution and identify overloaded agents."""
        alerts = []
        
        # Get active tasks per user - include ALL task items (System, Transferred, Escalation)
        user_workloads = TaskItem.objects.filter(
            task__in=queryset.filter(status__in=['pending', 'in progress']),
            role_user__isnull=False  # Only count items with assigned users
        ).values(
            'role_user__user_id', 'role_user__user_full_name'
        ).annotate(
            task_count=Count('task_item_id', distinct=True)
        ).order_by('-task_count')
        
        total_active = queryset.filter(status__in=['pending', 'in progress']).count()
        total_users = user_workloads.count()
        avg_per_user = total_active / total_users if total_users > 0 else 0
        
        for workload in user_workloads:
            task_count = workload['task_count']
            user_name = workload['role_user__user_full_name'] or f"User {workload['role_user__user_id']}"
            user_id = workload['role_user__user_id']
            
            if task_count >= self.THRESHOLDS['critical_workload_per_user']:
                alerts.append({
                    'type': 'workload',
                    'category': 'Agent Overload',
                    'severity': 'critical',
                    'title': f'Critical workload for {user_name}',
                    'message': f'{user_name} has {task_count} active tasks (threshold: {self.THRESHOLDS["critical_workload_per_user"]})',
                    'value': task_count,
                    'threshold': self.THRESHOLDS['critical_workload_per_user'],
                    'user_id': user_id,
                    'user_name': user_name,
                    'recommendation': 'Consider redistributing tasks or pausing new assignments to this agent.',
                })
            elif task_count >= self.THRESHOLDS['high_workload_per_user']:
                alerts.append({
                    'type': 'workload',
                    'category': 'Agent Overload',
                    'severity': 'warning',
                    'title': f'High workload for {user_name}',
                    'message': f'{user_name} has {task_count} active tasks (threshold: {self.THRESHOLDS["high_workload_per_user"]})',
                    'value': task_count,
                    'threshold': self.THRESHOLDS['high_workload_per_user'],
                    'user_id': user_id,
                    'user_name': user_name,
                    'recommendation': 'Monitor this agent\'s capacity and consider load balancing.',
                })
        
        # Workload imbalance detection
        if total_users > 1 and avg_per_user > 0:
            max_workload = user_workloads.first()['task_count'] if user_workloads.exists() else 0
            if max_workload > avg_per_user * 2:
                alerts.append({
                    'type': 'workload',
                    'category': 'Workload Imbalance',
                    'severity': 'warning',
                    'title': 'Significant workload imbalance detected',
                    'message': f'Workload varies significantly across agents (max: {max_workload}, avg: {avg_per_user:.1f})',
                    'value': max_workload,
                    'threshold': avg_per_user * 2,
                    'recommendation': 'Review task distribution algorithm and consider manual rebalancing.',
                })
        
        return alerts

    def _analyze_sla_risks(self, queryset, now):
        """Identify SLA breach risks and compliance issues."""
        alerts = []
        
        # Tasks at risk of SLA breach
        sla_tasks = queryset.filter(
            status__in=['pending', 'in progress'],
            target_resolution__isnull=False
        )
        
        at_risk_count = 0
        critical_count = 0
        breached_count = 0
        
        at_risk_tasks = []
        
        for task in sla_tasks:
            if task.target_resolution:
                hours_remaining = (task.target_resolution - now).total_seconds() / 3600
                
                if hours_remaining < 0:
                    breached_count += 1
                elif hours_remaining <= self.THRESHOLDS['sla_critical_hours']:
                    critical_count += 1
                    at_risk_tasks.append({
                        'task_id': task.task_id,
                        'ticket_number': task.ticket_id.ticket_number if task.ticket_id else '',
                        'hours_remaining': round(hours_remaining, 2),
                        'priority': task.ticket_id.priority if task.ticket_id else None,
                    })
                elif hours_remaining <= self.THRESHOLDS['sla_warning_hours']:
                    at_risk_count += 1
        
        if breached_count > 0:
            alerts.append({
                'type': 'sla',
                'category': 'SLA Breach',
                'severity': 'critical',
                'title': f'{breached_count} task(s) have breached SLA',
                'message': f'{breached_count} active tasks are past their target resolution time',
                'value': breached_count,
                'threshold': 0,
                'recommendation': 'Immediately prioritize these tasks and escalate if necessary.',
            })
        
        if critical_count > 0:
            alerts.append({
                'type': 'sla',
                'category': 'SLA Critical',
                'severity': 'critical',
                'title': f'{critical_count} task(s) approaching SLA breach',
                'message': f'{critical_count} tasks will breach SLA within {self.THRESHOLDS["sla_critical_hours"]} hours',
                'value': critical_count,
                'threshold': self.THRESHOLDS['sla_critical_hours'],
                'affected_tasks': at_risk_tasks[:5],  # Top 5 most urgent
                'recommendation': 'Urgent attention required. Escalate or reassign these tasks immediately.',
            })
        
        if at_risk_count > 0:
            alerts.append({
                'type': 'sla',
                'category': 'SLA Warning',
                'severity': 'warning',
                'title': f'{at_risk_count} task(s) at SLA risk',
                'message': f'{at_risk_count} tasks will breach SLA within {self.THRESHOLDS["sla_warning_hours"]} hours',
                'value': at_risk_count,
                'threshold': self.THRESHOLDS['sla_warning_hours'],
                'recommendation': 'Prioritize these tasks to avoid SLA breach.',
            })
        
        # Overall SLA compliance rate
        total_with_sla = queryset.filter(target_resolution__isnull=False).count()
        if total_with_sla > 0:
            completed_on_time = queryset.filter(
                status='completed',
                target_resolution__isnull=False,
                resolution_time__lte=F('target_resolution')
            ).count()
            compliance_rate = (completed_on_time / total_with_sla) * 100
            
            if compliance_rate < self.THRESHOLDS['sla_compliance_critical']:
                alerts.append({
                    'type': 'sla',
                    'category': 'SLA Compliance',
                    'severity': 'critical',
                    'title': 'Critical SLA compliance rate',
                    'message': f'SLA compliance is at {compliance_rate:.1f}% (threshold: {self.THRESHOLDS["sla_compliance_critical"]}%)',
                    'value': round(compliance_rate, 1),
                    'threshold': self.THRESHOLDS['sla_compliance_critical'],
                    'recommendation': 'Review SLA targets, staffing levels, and process bottlenecks.',
                })
            elif compliance_rate < self.THRESHOLDS['sla_compliance_warning']:
                alerts.append({
                    'type': 'sla',
                    'category': 'SLA Compliance',
                    'severity': 'warning',
                    'title': 'Low SLA compliance rate',
                    'message': f'SLA compliance is at {compliance_rate:.1f}% (threshold: {self.THRESHOLDS["sla_compliance_warning"]}%)',
                    'value': round(compliance_rate, 1),
                    'threshold': self.THRESHOLDS['sla_compliance_warning'],
                    'recommendation': 'Monitor closely and identify root causes of SLA breaches.',
                })
        
        return alerts

    def _analyze_performance(self, queryset, now):
        """Analyze performance metrics and identify issues."""
        alerts = []
        
        # Average resolution time
        completed_tasks = queryset.filter(
            status='completed',
            resolution_time__isnull=False
        )
        
        if completed_tasks.exists():
            avg_resolution = completed_tasks.aggregate(
                avg_hours=Avg(
                    (F('resolution_time') - F('created_at'))
                )
            )
            if avg_resolution['avg_hours']:
                avg_hours = avg_resolution['avg_hours'].total_seconds() / 3600
                if avg_hours > self.THRESHOLDS['slow_avg_resolution_hours']:
                    alerts.append({
                        'type': 'performance',
                        'category': 'Resolution Time',
                        'severity': 'warning',
                        'title': 'Slow average resolution time',
                        'message': f'Average resolution time is {avg_hours:.1f} hours (threshold: {self.THRESHOLDS["slow_avg_resolution_hours"]} hours)',
                        'value': round(avg_hours, 1),
                        'threshold': self.THRESHOLDS['slow_avg_resolution_hours'],
                        'recommendation': 'Review workflow efficiency and identify bottleneck steps.',
                    })
        
        # High escalation rate
        total_items = TaskItem.objects.filter(task__in=queryset).count()
        if total_items > 0:
            escalations = TaskItem.objects.filter(task__in=queryset, origin='Escalation').count()
            escalation_rate = (escalations / total_items) * 100
            
            if escalation_rate > self.THRESHOLDS['high_escalation_rate']:
                alerts.append({
                    'type': 'performance',
                    'category': 'Escalation Rate',
                    'severity': 'warning',
                    'title': 'High escalation rate',
                    'message': f'Escalation rate is {escalation_rate:.1f}% (threshold: {self.THRESHOLDS["high_escalation_rate"]}%)',
                    'value': round(escalation_rate, 1),
                    'threshold': self.THRESHOLDS['high_escalation_rate'],
                    'recommendation': 'Review initial assignment quality and agent training needs.',
                })
            
            # High transfer rate
            transfers = TaskItem.objects.filter(task__in=queryset, origin='Transferred').count()
            transfer_rate = (transfers / total_items) * 100
            
            if transfer_rate > self.THRESHOLDS['high_transfer_rate']:
                alerts.append({
                    'type': 'performance',
                    'category': 'Transfer Rate',
                    'severity': 'warning',
                    'title': 'High transfer rate',
                    'message': f'Transfer rate is {transfer_rate:.1f}% (threshold: {self.THRESHOLDS["high_transfer_rate"]}%)',
                    'value': round(transfer_rate, 1),
                    'threshold': self.THRESHOLDS['high_transfer_rate'],
                    'recommendation': 'Review task routing rules and department assignments.',
                })
        
        return alerts

    def _detect_anomalies(self, queryset, now):
        """Detect unusual patterns and anomalies."""
        alerts = []
        
        # Stale tickets (no activity for X days)
        stale_cutoff = now - timedelta(days=self.THRESHOLDS['stale_ticket_days'])
        stale_tasks = queryset.filter(
            status__in=['pending', 'in progress'],
            updated_at__lt=stale_cutoff
        ).count()
        
        if stale_tasks > 0:
            alerts.append({
                'type': 'anomaly',
                'category': 'Stale Tickets',
                'severity': 'warning',
                'title': f'{stale_tasks} stale task(s) detected',
                'message': f'{stale_tasks} tasks have had no activity for {self.THRESHOLDS["stale_ticket_days"]}+ days',
                'value': stale_tasks,
                'threshold': self.THRESHOLDS['stale_ticket_days'],
                'recommendation': 'Review these tasks and either close, escalate, or take action.',
            })
        
        # Aging tickets
        aging_cutoff = now - timedelta(days=self.THRESHOLDS['aging_ticket_days'])
        aging_tasks = queryset.filter(
            status__in=['pending', 'in progress'],
            created_at__lt=aging_cutoff
        ).count()
        
        if aging_tasks > 0:
            alerts.append({
                'type': 'anomaly',
                'category': 'Aging Tickets',
                'severity': 'warning' if aging_tasks < 10 else 'critical',
                'title': f'{aging_tasks} aging task(s) detected',
                'message': f'{aging_tasks} tasks are older than {self.THRESHOLDS["aging_ticket_days"]} days and still open',
                'value': aging_tasks,
                'threshold': self.THRESHOLDS['aging_ticket_days'],
                'recommendation': 'These long-running tasks may indicate systemic issues. Review and prioritize resolution.',
            })
        
        # Spike detection - compare today's volume to rolling average
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_created = Task.objects.filter(created_at__gte=today_start).count()
        
        # Last 7 days average
        week_ago = today_start - timedelta(days=7)
        week_tasks = Task.objects.filter(
            created_at__gte=week_ago,
            created_at__lt=today_start
        ).count()
        daily_avg = week_tasks / 7 if week_tasks > 0 else 0
        
        if daily_avg > 0 and today_created > daily_avg * 2:
            alerts.append({
                'type': 'anomaly',
                'category': 'Volume Spike',
                'severity': 'warning',
                'title': 'Unusual ticket volume spike',
                'message': f"Today's volume ({today_created}) is {(today_created/daily_avg*100):.0f}% of average ({daily_avg:.1f}/day)",
                'value': today_created,
                'threshold': daily_avg * 2,
                'recommendation': 'Monitor incoming volume and consider activating additional resources.',
            })
        
        return alerts

    def _analyze_queue_health(self, queryset, now):
        """Analyze queue backlogs and health."""
        alerts = []
        
        pending_count = queryset.filter(status='pending').count()
        
        if pending_count >= self.THRESHOLDS['queue_backlog_critical']:
            alerts.append({
                'type': 'queue',
                'category': 'Queue Backlog',
                'severity': 'critical',
                'title': 'Critical queue backlog',
                'message': f'{pending_count} tasks in pending state (threshold: {self.THRESHOLDS["queue_backlog_critical"]})',
                'value': pending_count,
                'threshold': self.THRESHOLDS['queue_backlog_critical'],
                'recommendation': 'Urgent: Allocate additional resources to clear the backlog.',
            })
        elif pending_count >= self.THRESHOLDS['queue_backlog_warning']:
            alerts.append({
                'type': 'queue',
                'category': 'Queue Backlog',
                'severity': 'warning',
                'title': 'Queue backlog growing',
                'message': f'{pending_count} tasks in pending state (threshold: {self.THRESHOLDS["queue_backlog_warning"]})',
                'value': pending_count,
                'threshold': self.THRESHOLDS['queue_backlog_warning'],
                'recommendation': 'Monitor queue and consider preventive measures.',
            })
        
        # Workflow-specific backlogs
        workflow_backlogs = queryset.filter(status='pending').values(
            'workflow_id__name'
        ).annotate(count=Count('task_id')).order_by('-count')[:5]
        
        for backlog in workflow_backlogs:
            if backlog['count'] >= 10:
                alerts.append({
                    'type': 'queue',
                    'category': 'Workflow Backlog',
                    'severity': 'info',
                    'title': f"Backlog in {backlog['workflow_id__name'] or 'Unknown workflow'}",
                    'message': f"{backlog['count']} pending tasks in this workflow",
                    'value': backlog['count'],
                    'threshold': 10,
                    'workflow_name': backlog['workflow_id__name'],
                    'recommendation': 'Review workflow capacity and assignment rules.',
                })
        
        return alerts

    def _calculate_health_score(self, summary, queryset):
        """Calculate overall system health score (0-100)."""
        base_score = 100
        
        # Deduct for critical alerts
        base_score -= summary['critical_count'] * 15
        
        # Deduct for warnings
        base_score -= summary['warning_count'] * 5
        
        # Deduct for info alerts
        base_score -= summary['info_count'] * 1
        
        # Ensure score is between 0 and 100
        return max(0, min(100, base_score))


class WorkloadAnalysisView(BaseReportingView):
    """Detailed workload analysis per agent and team."""

    def get(self, request):
        try:
            now = timezone.now()
            queryset = apply_date_filter(Task.objects.all(), request)
            
            # Per-user workload - include ALL task items (System, Transferred, Escalation)
            # to get full picture of agent workloads
            user_workloads = TaskItem.objects.filter(
                task__in=queryset,
                role_user__isnull=False  # Only count items with assigned users
            ).values(
                'role_user__user_id', 'role_user__user_full_name'
            ).annotate(
                total_assigned=Count('task_item_id', distinct=True),
                active_tasks=Count('task_item_id', distinct=True, filter=Q(task__status__in=['pending', 'in progress'])),
                completed_tasks=Count('task_item_id', distinct=True, filter=Q(task__status='completed')),
                system_assigned=Count('task_item_id', distinct=True, filter=Q(origin='System')),
                transferred=Count('task_item_id', distinct=True, filter=Q(origin='Transferred')),
                escalated=Count('task_item_id', distinct=True, filter=Q(origin='Escalation')),
            ).order_by('-active_tasks')
            
            workloads = [{
                'user_id': w['role_user__user_id'],
                'user_name': w['role_user__user_full_name'] or f"User {w['role_user__user_id']}",
                'total_assigned': w['total_assigned'],
                'active_tasks': w['active_tasks'],
                'completed_tasks': w['completed_tasks'],
                'system_assigned': w['system_assigned'],
                'transferred': w['transferred'],
                'escalated': w['escalated'],
                'utilization': round((w['active_tasks'] / 15) * 100, 1) if w['active_tasks'] else 0,  # Assuming 15 is full capacity
            } for w in user_workloads]
            
            # Summary stats
            total_users = len(workloads)
            total_active = sum(w['active_tasks'] for w in workloads)
            total_assigned = sum(w['total_assigned'] for w in workloads)
            avg_per_user = total_active / total_users if total_users > 0 else 0
            
            return Response({
                'generated_at': now.isoformat(),
                'summary': {
                    'total_agents': total_users,
                    'total_active_tasks': total_active,
                    'total_assigned_tasks': total_assigned,
                    'avg_tasks_per_agent': round(avg_per_user, 2),
                    'overloaded_agents': sum(1 for w in workloads if w['active_tasks'] >= 15),
                },
                'workloads': workloads,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class SLARiskReportView(BaseReportingView):
    """Detailed SLA risk analysis with at-risk tickets."""

    def get(self, request):
        try:
            now = timezone.now()
            queryset = apply_date_filter(Task.objects.all(), request)
            
            sla_tasks = queryset.filter(
                status__in=['pending', 'in progress'],
                target_resolution__isnull=False
            ).select_related('ticket_id', 'workflow_id', 'current_step')
            
            at_risk = []
            breached = []
            healthy = []
            
            for task in sla_tasks:
                hours_remaining = (task.target_resolution - now).total_seconds() / 3600
                
                task_data = {
                    'task_id': task.task_id,
                    'ticket_number': task.ticket_id.ticket_number if task.ticket_id else '',
                    'subject': task.ticket_id.ticket_data.get('subject', '') if task.ticket_id else '',
                    'priority': task.ticket_id.priority if task.ticket_id else None,
                    'workflow': task.workflow_id.name if task.workflow_id else None,
                    'current_step': task.current_step.name if task.current_step else None,
                    'status': task.status,
                    'target_resolution': task.target_resolution.isoformat(),
                    'hours_remaining': round(hours_remaining, 2),
                    'created_at': task.created_at.isoformat(),
                }
                
                if hours_remaining < 0:
                    task_data['overdue_hours'] = round(abs(hours_remaining), 2)
                    breached.append(task_data)
                elif hours_remaining <= 4:
                    at_risk.append(task_data)
                else:
                    healthy.append(task_data)
            
            # Sort by urgency
            breached.sort(key=lambda x: x.get('overdue_hours', 0), reverse=True)
            at_risk.sort(key=lambda x: x.get('hours_remaining', float('inf')))
            
            return Response({
                'generated_at': now.isoformat(),
                'summary': {
                    'total_with_sla': len(breached) + len(at_risk) + len(healthy),
                    'breached_count': len(breached),
                    'at_risk_count': len(at_risk),
                    'healthy_count': len(healthy),
                },
                'breached': breached[:20],  # Top 20
                'at_risk': at_risk[:20],
                'healthy_count': len(healthy),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class AnomalyDetectionView(BaseReportingView):
    """Detect anomalies in ticket patterns and agent behavior."""

    def get(self, request):
        try:
            now = timezone.now()
            days = int(request.query_params.get('days', 7))
            
            anomalies = []
            
            # Volume anomaly detection
            daily_volumes = []
            for i in range(days):
                day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                count = Task.objects.filter(created_at__gte=day_start, created_at__lt=day_end).count()
                daily_volumes.append({'date': day_start.date().isoformat(), 'count': count})
            
            if daily_volumes:
                avg_volume = sum(d['count'] for d in daily_volumes) / len(daily_volumes)
                std_dev = (sum((d['count'] - avg_volume) ** 2 for d in daily_volumes) / len(daily_volumes)) ** 0.5
                
                for day in daily_volumes:
                    if std_dev > 0 and abs(day['count'] - avg_volume) > 2 * std_dev:
                        anomalies.append({
                            'type': 'volume',
                            'date': day['date'],
                            'value': day['count'],
                            'expected': round(avg_volume, 1),
                            'deviation': round((day['count'] - avg_volume) / std_dev, 2),
                            'description': f"Unusual volume on {day['date']}: {day['count']} vs avg {avg_volume:.1f}",
                        })
            
            # Stale ticket anomaly
            stale_count = Task.objects.filter(
                status__in=['pending', 'in progress'],
                updated_at__lt=now - timedelta(days=7)
            ).count()
            
            if stale_count > 0:
                anomalies.append({
                    'type': 'stale',
                    'value': stale_count,
                    'description': f'{stale_count} tickets with no activity for 7+ days',
                })
            
            # Escalation spike detection
            recent_escalations = TaskItem.objects.filter(
                origin='Escalation',
                assigned_on__gte=now - timedelta(days=1)
            ).count()
            
            avg_daily_escalations = TaskItem.objects.filter(
                origin='Escalation',
                assigned_on__gte=now - timedelta(days=7)
            ).count() / 7
            
            if avg_daily_escalations > 0 and recent_escalations > avg_daily_escalations * 2:
                anomalies.append({
                    'type': 'escalation_spike',
                    'value': recent_escalations,
                    'expected': round(avg_daily_escalations, 1),
                    'description': f'Escalation spike: {recent_escalations} today vs avg {avg_daily_escalations:.1f}/day',
                })
            
            return Response({
                'generated_at': now.isoformat(),
                'analysis_period_days': days,
                'daily_volumes': daily_volumes,
                'anomalies': anomalies,
                'anomaly_count': len(anomalies),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class ServiceHealthSummaryView(BaseReportingView):
    """High-level service health dashboard."""

    def get(self, request):
        try:
            now = timezone.now()
            queryset = apply_date_filter(Task.objects.all(), request)
            
            total_tasks = queryset.count()
            
            # Status breakdown
            status_counts = dict(queryset.values_list('status').annotate(count=Count('task_id')))
            
            # Calculate metrics
            pending = status_counts.get('pending', 0)
            in_progress = status_counts.get('in progress', 0)
            completed = status_counts.get('completed', 0)
            
            # SLA metrics
            with_sla = queryset.filter(target_resolution__isnull=False)
            completed_on_time = with_sla.filter(
                status='completed',
                resolution_time__lte=F('target_resolution')
            ).count()
            sla_compliance = (completed_on_time / with_sla.count() * 100) if with_sla.count() > 0 else 100
            
            # Active SLA risks
            sla_at_risk = with_sla.filter(
                status__in=['pending', 'in progress'],
                target_resolution__lte=now + timedelta(hours=4)
            ).count()
            
            # Determine overall health status
            if sla_compliance >= 90 and pending < 20 and sla_at_risk < 5:
                health_status = 'healthy'
            elif sla_compliance >= 70 and pending < 50 and sla_at_risk < 15:
                health_status = 'warning'
            else:
                health_status = 'critical'
            
            return Response({
                'generated_at': now.isoformat(),
                'health_status': health_status,
                'metrics': {
                    'total_tasks': total_tasks,
                    'pending': pending,
                    'in_progress': in_progress,
                    'completed': completed,
                    'sla_compliance_rate': round(sla_compliance, 1),
                    'sla_at_risk': sla_at_risk,
                    'completion_rate': round((completed / total_tasks * 100) if total_tasks > 0 else 0, 1),
                },
                'thresholds': {
                    'sla_healthy': 90,
                    'sla_warning': 70,
                    'pending_healthy': 20,
                    'pending_warning': 50,
                },
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)