# Analytics System Documentation

## Overview

The analytics system provides a comprehensive API for ticket metrics and reporting with support for **stackable, aggregatable filters** across multiple dimensions.

## Architecture

### Components

1. **`filters.py`** - Centralized filtering system (`AnalyticsFilter` class)
   - Universal filter logic that can be reused across the application
   - Supports all dimensions: time, department, role, priority, status, type
   - Builds efficient Django Q objects for database queries

2. **`serializers.py`** - API response serialization
   - `TicketAnalyticsSerializer` - Main analytics metrics
   - `TicketStatusBreakdownSerializer` - Status count breakdown
   - `FilterSummarySerializer` - Current filter state
   - `DimensionOptionsSerializer` - Available filter options

3. **`views.py`** - REST API endpoints
   - `AnalyticsRootView` - Navigation endpoint
   - `TicketAnalyticsView` - Main analytics endpoint with filtering
   - `TicketStatusSummaryView` - Status breakdown endpoint
   - `FilterDimensionOptionsView` - Available filter options for UI

4. **`urls.py`** - URL routing
   - Routes all analytics endpoints

## API Endpoints

All endpoints are available at `/analytics-v2/` (to avoid conflict with existing reporting app).

### 1. Root Endpoint
```
GET /analytics-v2/
```
Returns navigation to all analytics endpoints.

### 2. Ticket Analytics
```
GET /analytics-v2/tickets/
```

Returns total ticket count and status breakdown with applied filters.

**Query Parameters:**
- `start_date` - ISO format date (YYYY-MM-DD), optional
- `end_date` - ISO format date (YYYY-MM-DD), optional
- `departments` - Comma-separated list of departments
- `roles` - Comma-separated list of roles/assignees
- `priorities` - Comma-separated list of priorities
- `statuses` - Comma-separated list of statuses
- `types` - Comma-separated list of ticket types/categories

**Example Request:**
```
GET /analytics-v2/tickets/?start_date=2024-01-01&end_date=2024-12-31&departments=IT,HR&priorities=High,Critical&statuses=In Progress,Pending
```

**Response:**
```json
{
  "analytics": {
    "total_tickets": 150,
    "statuses": {
      "in_progress": 45,
      "on_hold": 12,
      "pending": 38,
      "resolved": 42,
      "rejected": 8,
      "withdrawn": 3,
      "closed": 2,
      "other": 0
    }
  },
  "filters": {
    "active_filters": 3,
    "time_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    },
    "departments": ["IT", "HR"],
    "roles": [],
    "priorities": ["High", "Critical"],
    "statuses": ["In Progress", "Pending"],
    "types": []
  }
}
```

### 3. Status Summary
```
GET /analytics-v2/status-summary/
```

Returns only status counts. Supports same filtering as ticket analytics.

**Response:**
```json
{
  "in_progress": 45,
  "on_hold": 12,
  "pending": 38,
  "resolved": 42,
  "rejected": 8,
  "withdrawn": 3,
  "closed": 2,
  "other": 0
}
```

### 4. Filter Options
```
GET /analytics-v2/filter-options/
```

Returns available values for each filter dimension (useful for populating UI dropdowns).

**Response:**
```json
{
  "departments": ["IT", "HR", "Finance", "Operations"],
  "statuses": ["In Progress", "On Hold", "Pending", "Resolved", "Rejected", "Withdrawn", "Closed"],
  "priorities": ["Low", "Medium", "High", "Critical"],
  "roles": ["Manager", "Agent", "Support", "Lead"],
  "types": ["Bug", "Feature Request", "Support", "Enhancement"]
}
```

## Using AnalyticsFilter Programmatically

The `AnalyticsFilter` class can be used directly in code for complex analytics operations.

### Basic Usage

```python
from analytics.filters import AnalyticsFilter
from tickets.models import WorkflowTicket

# Create filter
filter_obj = AnalyticsFilter()

# Add filters (stackable)
filter_obj.add_departments(['IT', 'HR'])
filter_obj.add_priorities(['High', 'Critical'])
filter_obj.add_statuses(['In Progress', 'Pending'])
filter_obj.add_time_range('2024-01-01', '2024-12-31')

# Get filtered queryset
queryset = WorkflowTicket.objects.filter(filter_obj.build_q_object())

# Use the queryset
total = queryset.count()
for ticket in queryset:
    print(ticket.ticket_number)
```

### Chaining Operations

```python
filter_obj = (AnalyticsFilter()
    .add_departments(['IT'])
    .add_priorities(['High'])
    .add_time_range('2024-01-01', '2024-12-31')
)

queryset = WorkflowTicket.objects.filter(filter_obj.build_q_object())
```

### Getting Filter Summary

```python
filter_obj = AnalyticsFilter()
filter_obj.add_departments(['IT', 'HR'])
filter_obj.add_priorities(['High'])

summary = filter_obj.get_summary()
# {
#   'time_range': {'start': None, 'end': None},
#   'departments': ['IT', 'HR'],
#   'roles': [],
#   'priorities': ['High'],
#   'statuses': [],
#   'types': [],
#   'active_filters': 2
# }
```

### Clearing Filters

```python
# Clear all filters
filter_obj.clear()

# Clear specific dimension
filter_obj.clear_dimension('departments')
filter_obj.clear_dimension('time_range')
```

### Serializing/Deserializing

```python
# Convert to dictionary for caching/storage
filter_dict = filter_obj.to_dict()

# Restore from dictionary
restored = AnalyticsFilter.from_dict(filter_dict)
```

## Filter Dimensions

### Time Range
- **Field**: `created_at` (ticket creation date)
- **Format**: ISO date (YYYY-MM-DD)
- **Example**: `start_date=2024-01-01&end_date=2024-12-31`

### Department / Team
- **Field**: `ticket_data.department`
- **Type**: String (case-insensitive substring match)
- **Example**: `departments=IT,HR,Finance`

### Role / Assignee
- **Fields**: `ticket_data.assigned_role` or `ticket_data.assignee`
- **Type**: String (case-insensitive substring match)
- **Example**: `roles=Manager,Agent,Support`

### Priority
- **Field**: `ticket_data.priority`
- **Type**: String (case-insensitive substring match)
- **Values**: Low, Medium, High, Critical
- **Example**: `priorities=High,Critical`

### Status
- **Field**: `ticket_data.status`
- **Type**: String (case-insensitive substring match)
- **Values**: In Progress, On Hold, Pending, Resolved, Rejected, Withdrawn, Closed, Other
- **Example**: `statuses=In Progress,Pending`

### Ticket Type / Category
- **Field**: `ticket_data.category`
- **Type**: String (case-insensitive substring match)
- **Example**: `types=Bug,Feature Request,Enhancement`

## Filter Logic

### Within a Dimension (OR)
Multiple values in the same dimension are combined with **OR**:
```
departments=IT OR departments=HR
```

### Across Dimensions (AND)
Different dimensions are combined with **AND**:
```
(departments=IT OR departments=HR) AND (priorities=High OR priorities=Critical)
```

### Matching Behavior
- Substring matching is case-insensitive
- Searches for any occurrence of the filter value within the field
- Example: `status_filter="In"` would match "In Progress", "In Review", etc.

## Integration Points

The `AnalyticsFilter` class is designed to be used universally across the application:

1. **Analytics Views** - Already integrated in `/analytics-v2/` endpoints
2. **Custom Reports** - Can be used in reporting views
3. **Admin Dashboard** - For filtered dashboard data
4. **Data Exports** - For exporting filtered datasets
5. **Background Tasks** - For scheduled analytics generation

## Performance Considerations

- Filters are applied at the database level using Django ORM
- Efficiently builds Q objects to minimize database queries
- For large datasets, consider adding database indexes on frequently filtered fields:
  - `ticket_data__department`
  - `ticket_data__status`
  - `ticket_data__priority`
  - `created_at`

## Authentication

All analytics endpoints require **JWT authentication**:
```
Authorization: Bearer <your_jwt_token>
```

## Error Handling

- Invalid date formats return 400 Bad Request
- Invalid filter dimensions are silently ignored
- Missing parameters are treated as "no filter" for that dimension
- Empty results return count of 0 instead of error

## Future Enhancements

1. Add database aggregation for large datasets (vs. in-memory iteration)
2. Support for date granularity (daily, weekly, monthly summaries)
3. Caching layer for frequently requested filters
4. Export formats (CSV, Excel, PDF)
5. Scheduled report generation and delivery
6. Advanced metrics (SLA compliance, cycle time, resolution time)
7. Trend analysis and forecasting
