"""
Utility functions for reporting analytics
"""
from django.db.models import F, Case, When, DurationField, Avg
from datetime import timedelta


def convert_timedelta_to_hours(td):
    """Convert timedelta to hours as float"""
    if td is None:
        return None
    return round(td.total_seconds() / 3600, 2)


def get_average_duration(queryset, duration_field_expression):
    """
    Get average duration from a queryset with duration field expression
    
    Args:
        queryset: Django queryset
        duration_field_expression: F() expression representing duration
    
    Returns:
        Average hours as float or None
    """
    result = queryset.aggregate(
        avg_duration=Avg(
            Case(
                When(**{str(duration_field_expression): True}, then=duration_field_expression),
                default=None,
                output_field=DurationField(),
            )
        )
    )
    return convert_timedelta_to_hours(result['avg_duration'])


def build_date_range_filters(start_date_str, end_date_str):
    """
    Build Q objects for date range filtering
    
    Args:
        start_date_str: ISO format date string or None
        end_date_str: ISO format date string or None
    
    Returns:
        Tuple of (start_date_display, end_date_display, filters_dict)
    """
    from datetime import datetime
    from django.db.models import Q
    
    filters = {}
    start_display = start_date_str or 'all time'
    end_display = end_date_str or 'all time'
    
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str).date()
            filters['created_at__gte'] = start_date
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str).date()
            # Add 1 day to include all of the end date
            filters['created_at__lte'] = end_date + timedelta(days=1)
        except ValueError:
            pass
    
    return start_display, end_display, filters
