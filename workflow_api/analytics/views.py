"""
Analytics views for ticket metrics and reporting.

Provides endpoints for analytics with support for stackable, aggregatable filters
across multiple dimensions: time, department, role, priority, status, type.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Case, When, Value, CharField
from tickets.models import WorkflowTicket
from authentication import JWTCookieAuthentication
from .serializers import (
    TicketAnalyticsSerializer,
    TicketStatusBreakdownSerializer,
    FilterSummarySerializer,
    TicketAnalyticsDetailedSerializer,
    DimensionOptionsSerializer,
)
from .filters import AnalyticsFilter


class TicketAnalyticsView(APIView):
    """
    Main ticket analytics endpoint.
    
    Returns:
    - Total ticket count
    - Status breakdown with counts
    - Current filter configuration
    
    Query Parameters:
    - start_date: ISO format date (YYYY-MM-DD)
    - end_date: ISO format date (YYYY-MM-DD)
    - departments: Comma-separated list of departments
    - roles: Comma-separated list of roles/assignees
    - priorities: Comma-separated list of priorities
    - statuses: Comma-separated list of statuses
    - types: Comma-separated list of ticket types/categories
    
    Example:
        GET /analytics/tickets/?start_date=2024-01-01&departments=IT,HR&priorities=High,Critical
    """
    
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Get ticket analytics with applied filters"""
        try:
            # Build filter from query parameters
            filter_obj = self._build_filter_from_request(request)
            
            # Get filtered queryset
            queryset = WorkflowTicket.objects.all()
            q_object = filter_obj.build_q_object()
            if q_object:
                queryset = queryset.filter(q_object)
            
            # Calculate metrics
            analytics_data = self._calculate_analytics(queryset)
            
            # Build response
            response_data = {
                'analytics': analytics_data,
                'filters': filter_obj.get_summary(),
            }
            
            serializer = TicketAnalyticsDetailedSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _build_filter_from_request(self, request) -> AnalyticsFilter:
        """Build AnalyticsFilter from query parameters"""
        filter_obj = AnalyticsFilter()
        
        # Time range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date or end_date:
            filter_obj.add_time_range(start_date, end_date)
        
        # Departments
        departments = request.query_params.get('departments', '').split(',')
        departments = [d.strip() for d in departments if d.strip()]
        if departments:
            filter_obj.add_departments(departments)
        
        # Roles/Assignees
        roles = request.query_params.get('roles', '').split(',')
        roles = [r.strip() for r in roles if r.strip()]
        if roles:
            filter_obj.add_roles(roles)
        
        # Priorities
        priorities = request.query_params.get('priorities', '').split(',')
        priorities = [p.strip() for p in priorities if p.strip()]
        if priorities:
            filter_obj.add_priorities(priorities)
        
        # Statuses
        statuses = request.query_params.get('statuses', '').split(',')
        statuses = [s.strip() for s in statuses if s.strip()]
        if statuses:
            filter_obj.add_statuses(statuses)
        
        # Types/Categories
        types = request.query_params.get('types', '').split(',')
        types = [t.strip() for t in types if t.strip()]
        if types:
            filter_obj.add_types(types)
        
        return filter_obj
    
    def _calculate_analytics(self, queryset) -> dict:
        """Calculate analytics metrics from queryset"""
        from django.db.models import Q
        total = queryset.count()
        
        # Use QuerySet aggregation for accurate status counts
        # Check both the model's status field and ticket_data JSON field
        status_counts = {
            'open': queryset.filter(status__icontains='open').count(),
            'in_progress': queryset.filter(Q(status__icontains='in progress') | Q(status__icontains='in_progress')).count(),
            'on_hold': queryset.filter(Q(status__icontains='on hold') | Q(status__icontains='on_hold')).count(),
            'pending': queryset.filter(status__icontains='pending').count(),
            'resolved': queryset.filter(status__icontains='resolved').count(),
            'rejected': queryset.filter(status__icontains='rejected').count(),
            'withdrawn': queryset.filter(status__icontains='withdrawn').count(),
            'closed': queryset.filter(status__icontains='closed').count(),
        }
        
        # Count tickets not matching any known status
        counted = sum(status_counts.values())
        status_counts['other'] = max(0, total - counted)
        
        return {
            'total_tickets': total,
            'statuses': status_counts,
        }


class TicketStatusSummaryView(APIView):
    """
    Dedicated endpoint for ticket status breakdown.
    
    Returns only status counts without other analytics data.
    Supports the same filtering as TicketAnalyticsView.
    
    Example:
        GET /analytics/status-summary/?statuses=In Progress,On Hold
    """
    
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Get status breakdown"""
        try:
            # Build filter from query parameters
            filter_obj = AnalyticsFilter()
            
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            if start_date or end_date:
                filter_obj.add_time_range(start_date, end_date)
            
            departments = request.query_params.get('departments', '').split(',')
            departments = [d.strip() for d in departments if d.strip()]
            if departments:
                filter_obj.add_departments(departments)
            
            roles = request.query_params.get('roles', '').split(',')
            roles = [r.strip() for r in roles if r.strip()]
            if roles:
                filter_obj.add_roles(roles)
            
            priorities = request.query_params.get('priorities', '').split(',')
            priorities = [p.strip() for p in priorities if p.strip()]
            if priorities:
                filter_obj.add_priorities(priorities)
            
            statuses = request.query_params.get('statuses', '').split(',')
            statuses = [s.strip() for s in statuses if s.strip()]
            if statuses:
                filter_obj.add_statuses(statuses)
            
            types = request.query_params.get('types', '').split(',')
            types = [t.strip() for t in types if t.strip()]
            if types:
                filter_obj.add_types(types)
            
            # Get filtered queryset
            queryset = WorkflowTicket.objects.all()
            q_object = filter_obj.build_q_object()
            if q_object:
                queryset = queryset.filter(q_object)
            
            # Calculate status breakdown using QuerySet aggregation
            from django.db.models import Q
            total = queryset.count()
            status_counts = {
                'open': queryset.filter(status__icontains='open').count(),
                'in_progress': queryset.filter(Q(status__icontains='in progress') | Q(status__icontains='in_progress')).count(),
                'on_hold': queryset.filter(Q(status__icontains='on hold') | Q(status__icontains='on_hold')).count(),
                'pending': queryset.filter(status__icontains='pending').count(),
                'resolved': queryset.filter(status__icontains='resolved').count(),
                'rejected': queryset.filter(status__icontains='rejected').count(),
                'withdrawn': queryset.filter(status__icontains='withdrawn').count(),
                'closed': queryset.filter(status__icontains='closed').count(),
            }
            
            # Count tickets not matching any known status
            counted = sum(status_counts.values())
            status_counts['other'] = max(0, total - counted)
            
            serializer = TicketStatusBreakdownSerializer(status_counts)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class FilterDimensionOptionsView(APIView):
    """
    Get available options for each filter dimension.
    
    Useful for populating dropdown filters in UI.
    Returns distinct values from the database for each dimension.
    
    Example:
        GET /analytics/filter-options/
    """
    
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Get available filter dimension options"""
        try:
            queryset = WorkflowTicket.objects.all()
            
            # Extract unique values from ticket_data
            departments = set()
            statuses = set()
            priorities = set()
            roles = set()
            types = set()
            
            for ticket in queryset.values('ticket_data'):
                data = ticket.get('ticket_data', {})
                
                if data.get('department'):
                    departments.add(data['department'])
                if data.get('status'):
                    statuses.add(data['status'])
                if data.get('priority'):
                    priorities.add(data['priority'])
                if data.get('assigned_role'):
                    roles.add(data['assigned_role'])
                if data.get('assignee'):
                    roles.add(data['assignee'])
                if data.get('category'):
                    types.add(data['category'])
            
            # Sort for consistent output
            response_data = {
                'departments': sorted(list(departments)),
                'statuses': sorted(list(statuses)),
                'priorities': sorted(list(priorities)),
                'roles': sorted(list(roles)),
                'types': sorted(list(types)),
            }
            
            serializer = DimensionOptionsSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class AnalyticsRootView(APIView):
    """
    Root endpoint for analytics API.
    
    Provides navigation to analytics endpoints.
    """
    
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Get analytics root with available endpoints"""
        return Response({
            'message': 'Analytics API',
            'version': '1.0',
            'endpoints': {
                'tickets': request.build_absolute_uri('tickets/'),
                'status-summary': request.build_absolute_uri('status-summary/'),
                'filter-options': request.build_absolute_uri('filter-options/'),
            },
        }, status=status.HTTP_200_OK)
