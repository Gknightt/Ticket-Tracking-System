"""
URL configuration for analytics endpoints.
"""

from django.urls import path
from .views import (
    AnalyticsRootView,
    TicketAnalyticsView,
    TicketStatusSummaryView,
    FilterDimensionOptionsView,
)

app_name = 'analytics'

urlpatterns = [
    # Root analytics endpoint
    path('', AnalyticsRootView.as_view(), name='analytics-root'),
    
    # Ticket analytics with filtering
    path('tickets/', TicketAnalyticsView.as_view(), name='ticket-analytics'),
    
    # Status summary endpoint
    path('status-summary/', TicketStatusSummaryView.as_view(), name='status-summary'),
    
    # Filter dimension options (for populating UI dropdowns)
    path('filter-options/', FilterDimensionOptionsView.as_view(), name='filter-options'),
]
