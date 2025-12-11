from django.urls import path
from .views import (
    # Trend Analytics endpoints (used by frontend)
    TicketTrendAnalyticsView,
    TaskItemTrendAnalyticsView,
    TicketCategoryAnalyticsView,
    # Aggregated endpoints (used by frontend)
    AggregatedTicketsReportView,
    AggregatedWorkflowsReportView,
    AggregatedTasksReportView,
    # Drilldown endpoints (used by frontend)
    DrilldownTicketsByStatusView,
    DrilldownTicketsByPriorityView,
    DrilldownTicketsByAgeView,
    DrilldownSLAComplianceView,
    DrilldownUserTasksView,
    DrilldownWorkflowTasksView,
    DrilldownStepTasksView,
    DrilldownDepartmentTasksView,
    DrilldownTransfersView,
    DrilldownTaskItemsByStatusView,
    DrilldownTaskItemsByOriginView,
)

app_name = 'reporting'

urlpatterns = [
    # Trend Analytics endpoints
    path('ticket-trends/', TicketTrendAnalyticsView.as_view(), name='ticket-trends'),
    path('task-item-trends/', TaskItemTrendAnalyticsView.as_view(), name='task-item-trends'),
    path('ticket-categories/', TicketCategoryAnalyticsView.as_view(), name='ticket-categories'),
    
    # Aggregated endpoints
    path('reports/tickets/', AggregatedTicketsReportView.as_view(), name='aggregated-tickets'),
    path('reports/workflows/', AggregatedWorkflowsReportView.as_view(), name='aggregated-workflows'),
    path('reports/tasks/', AggregatedTasksReportView.as_view(), name='aggregated-tasks'),
    
    # Drilldown endpoints - Tickets
    path('drilldown/tickets/status/', DrilldownTicketsByStatusView.as_view(), name='drilldown-tickets-status'),
    path('drilldown/tickets/priority/', DrilldownTicketsByPriorityView.as_view(), name='drilldown-tickets-priority'),
    path('drilldown/tickets/age/', DrilldownTicketsByAgeView.as_view(), name='drilldown-tickets-age'),
    path('drilldown/tickets/sla/', DrilldownSLAComplianceView.as_view(), name='drilldown-sla'),
    
    # Drilldown endpoints - Workflows
    path('drilldown/workflows/', DrilldownWorkflowTasksView.as_view(), name='drilldown-workflow-tasks'),
    path('drilldown/steps/', DrilldownStepTasksView.as_view(), name='drilldown-step-tasks'),
    path('drilldown/departments/', DrilldownDepartmentTasksView.as_view(), name='drilldown-department-tasks'),
    
    # Drilldown endpoints - Task Items
    path('drilldown/task-items/status/', DrilldownTaskItemsByStatusView.as_view(), name='drilldown-taskitems-status'),
    path('drilldown/task-items/origin/', DrilldownTaskItemsByOriginView.as_view(), name='drilldown-taskitems-origin'),
    path('drilldown/user-tasks/', DrilldownUserTasksView.as_view(), name='drilldown-user-tasks'),
    path('drilldown/transfers/', DrilldownTransfersView.as_view(), name='drilldown-transfers'),
]
