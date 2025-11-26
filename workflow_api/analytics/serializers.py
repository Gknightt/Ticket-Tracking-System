"""
Serializers for analytics endpoints.

Provides serialization for analytics metrics and summaries.
"""

from rest_framework import serializers
from django.db.models import Q, Count
from tickets.models import WorkflowTicket


class TicketStatusBreakdownSerializer(serializers.Serializer):
    """
    Serializer for ticket status breakdown metrics.
    """
    open = serializers.IntegerField(default=0)
    in_progress = serializers.IntegerField(default=0)
    on_hold = serializers.IntegerField(default=0)
    pending = serializers.IntegerField(default=0)
    resolved = serializers.IntegerField(default=0)
    rejected = serializers.IntegerField(default=0)
    withdrawn = serializers.IntegerField(default=0)
    closed = serializers.IntegerField(default=0)
    other = serializers.IntegerField(default=0)


class TicketAnalyticsSerializer(serializers.Serializer):
    """
    Main analytics serializer for ticket metrics.
    
    Derives all metrics from the ticket model without needing a dedicated analytics model.
    Includes:
    - Total tickets
    - Status breakdown with counts for all statuses
    - Applied filters summary
    """
    
    total_tickets = serializers.IntegerField()
    statuses = TicketStatusBreakdownSerializer()
    filters_applied = serializers.DictField(child=serializers.ListField(), required=False, allow_empty=True)
    time_range = serializers.DictField(required=False, allow_null=True)
    
    class Meta:
        fields = ['total_tickets', 'statuses', 'filters_applied', 'time_range']


class FilterSummarySerializer(serializers.Serializer):
    """
    Serializer for filter configuration summary.
    Shows what filters are currently active.
    """
    active_filters = serializers.IntegerField()
    time_range = serializers.DictField(required=False, allow_null=True)
    departments = serializers.ListField(child=serializers.CharField(), required=False)
    roles = serializers.ListField(child=serializers.CharField(), required=False)
    priorities = serializers.ListField(child=serializers.CharField(), required=False)
    statuses = serializers.ListField(child=serializers.CharField(), required=False)
    types = serializers.ListField(child=serializers.CharField(), required=False)


class TicketAnalyticsDetailedSerializer(serializers.Serializer):
    """
    Detailed analytics response including both metrics and filter information.
    """
    analytics = TicketAnalyticsSerializer()
    filters = FilterSummarySerializer()


class DimensionOptionsSerializer(serializers.Serializer):
    """
    Serializer for available filter dimension options.
    Useful for populating filter UI dropdowns.
    """
    departments = serializers.ListField(child=serializers.CharField())
    statuses = serializers.ListField(child=serializers.CharField())
    priorities = serializers.ListField(child=serializers.CharField())
    roles = serializers.ListField(child=serializers.CharField())
    types = serializers.ListField(child=serializers.CharField())
