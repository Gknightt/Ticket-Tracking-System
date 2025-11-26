# This file is deprecated. All views have been refactored into separate modules:
# - dashboard_views.py: AnalyticsRootView, DashboardSummaryView, StatusSummaryView
# - ticket_views.py: SLAComplianceView, PriorityDistributionView, TicketAgeAnalyticsView
# - workflow_views.py: WorkflowMetricsView, StepPerformanceView, DepartmentAnalyticsView
# - team_views.py: TeamPerformanceView, AssignmentAnalyticsView, AuditActivityView
# - task_item_views.py: Task Item analytics views
# - report_views.py: Aggregated reporting views
# - utils.py: Shared utility functions

# For backward compatibility, import all views from their new locations
from .dashboard_views import (
    AnalyticsRootView,
    DashboardSummaryView,
    StatusSummaryView,
)
from .ticket_views import (
    SLAComplianceView,
    PriorityDistributionView,
    TicketAgeAnalyticsView,
)
from .workflow_views import (
    WorkflowMetricsView,
    StepPerformanceView,
    DepartmentAnalyticsView,
)
from .team_views import (
    TeamPerformanceView,
    AssignmentAnalyticsView,
    AuditActivityView,
)
from .task_item_views import (
    TaskItemStatusAnalyticsView,
    TaskItemAssignmentOriginAnalyticsView,
    TaskItemPerformanceAnalyticsView,
    TaskItemUserPerformanceAnalyticsView,
    TaskItemHistoryTrendAnalyticsView,
    TaskItemTransferAnalyticsView,
)
from .report_views import (
    AggregatedTicketsReportView,
    AggregatedWorkflowsReportView,
    AggregatedTasksReportView,
)

__all__ = [
    'AnalyticsRootView',
    'DashboardSummaryView',
    'StatusSummaryView',
    'SLAComplianceView',
    'PriorityDistributionView',
    'TicketAgeAnalyticsView',
    'WorkflowMetricsView',
    'StepPerformanceView',
    'DepartmentAnalyticsView',
    'TeamPerformanceView',
    'AssignmentAnalyticsView',
    'AuditActivityView',
    'TaskItemStatusAnalyticsView',
    'TaskItemAssignmentOriginAnalyticsView',
    'TaskItemPerformanceAnalyticsView',
    'TaskItemUserPerformanceAnalyticsView',
    'TaskItemHistoryTrendAnalyticsView',
    'TaskItemTransferAnalyticsView',
    'AggregatedTicketsReportView',
    'AggregatedWorkflowsReportView',
    'AggregatedTasksReportView',
]
