"""
Centralized filtering system for analytics across all dimensions.

Supports stackable filters across:
- Time (date range)
- Department / Team
- Role / Assignee
- Priority
- Status
- Ticket Type / Category

Filters can be aggregated, allowing multiple values per dimension
(e.g., multiple departments, multiple statuses, etc.)
"""

from django.db.models import Q
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any


class AnalyticsFilter:
    """
    Centralized filtering system for analytics queries.
    
    Supports stackable, aggregatable filters across multiple dimensions.
    Builds efficient Django Q objects for database queries.
    
    Usage:
        filter = AnalyticsFilter()
        filter.add_time_range('2024-01-01', '2024-12-31')
        filter.add_departments(['IT', 'HR'])
        filter.add_priorities(['High', 'Critical'])
        filter.add_statuses(['In Progress', 'Pending'])
        
        queryset = Ticket.objects.filter(filter.build_q_object())
    """
    
    def __init__(self):
        """Initialize empty filter dimensions"""
        self.dimensions = {
            'time_range': {
                'start_date': None,
                'end_date': None,
            },
            'departments': [],
            'roles': [],
            'priorities': [],
            'statuses': [],
            'types': [],  # ticket types/categories
        }
        self.field_mappings = {
            'created_at': 'created_at',
            'fetched_at': 'fetched_at',
            'department': 'ticket_data__department',
            'status': 'ticket_data__status',
            'priority': 'ticket_data__priority',
            'category': 'ticket_data__category',
            'type': 'ticket_data__category',
            'assignee': 'ticket_data__assignee',
            'assigned_role': 'ticket_data__assigned_role',
        }
    
    # ========== Time Range Filters ==========
    
    def add_time_range(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> 'AnalyticsFilter':
        """
        Add time range filter.
        
        Args:
            start_date: ISO format date string (YYYY-MM-DD) or None
            end_date: ISO format date string (YYYY-MM-DD) or None
        
        Returns:
            Self for chaining
        """
        if start_date:
            try:
                self.dimensions['time_range']['start_date'] = self._parse_date(start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                self.dimensions['time_range']['end_date'] = self._parse_date(end_date)
            except ValueError:
                pass
        
        return self
    
    def set_time_range(self, start_date: Optional[str], end_date: Optional[str]) -> 'AnalyticsFilter':
        """
        Set (replace) time range filter. Alias for add_time_range with clearer semantics.
        """
        return self.add_time_range(start_date, end_date)
    
    # ========== Department / Team Filters ==========
    
    def add_departments(self, departments: List[str]) -> 'AnalyticsFilter':
        """
        Add department(s) to filter. Stackable - adds to existing departments.
        
        Args:
            departments: List of department names
        
        Returns:
            Self for chaining
        """
        if isinstance(departments, str):
            departments = [departments]
        
        self.dimensions['departments'].extend([d for d in departments if d and d not in self.dimensions['departments']])
        return self
    
    def set_departments(self, departments: List[str]) -> 'AnalyticsFilter':
        """
        Set (replace) departments. Clears previous departments.
        """
        self.dimensions['departments'] = list(set([d for d in departments if d]))
        return self
    
    def get_departments(self) -> List[str]:
        """Get current department filters"""
        return self.dimensions['departments'].copy()
    
    # ========== Role / Assignee Filters ==========
    
    def add_roles(self, roles: List[str]) -> 'AnalyticsFilter':
        """
        Add role(s) to filter. Stackable.
        
        Args:
            roles: List of role names
        
        Returns:
            Self for chaining
        """
        if isinstance(roles, str):
            roles = [roles]
        
        self.dimensions['roles'].extend([r for r in roles if r and r not in self.dimensions['roles']])
        return self
    
    def add_assignees(self, assignees: List[str]) -> 'AnalyticsFilter':
        """
        Alias for add_roles for assignee context.
        """
        return self.add_roles(assignees)
    
    def set_roles(self, roles: List[str]) -> 'AnalyticsFilter':
        """
        Set (replace) roles.
        """
        self.dimensions['roles'] = list(set([r for r in roles if r]))
        return self
    
    def get_roles(self) -> List[str]:
        """Get current role filters"""
        return self.dimensions['roles'].copy()
    
    # ========== Priority Filters ==========
    
    def add_priorities(self, priorities: List[str]) -> 'AnalyticsFilter':
        """
        Add priority level(s) to filter. Stackable.
        
        Args:
            priorities: List of priority levels (e.g., 'Low', 'Medium', 'High', 'Critical')
        
        Returns:
            Self for chaining
        """
        if isinstance(priorities, str):
            priorities = [priorities]
        
        self.dimensions['priorities'].extend([p for p in priorities if p and p not in self.dimensions['priorities']])
        return self
    
    def set_priorities(self, priorities: List[str]) -> 'AnalyticsFilter':
        """
        Set (replace) priorities.
        """
        self.dimensions['priorities'] = list(set([p for p in priorities if p]))
        return self
    
    def get_priorities(self) -> List[str]:
        """Get current priority filters"""
        return self.dimensions['priorities'].copy()
    
    # ========== Status Filters ==========
    
    def add_statuses(self, statuses: List[str]) -> 'AnalyticsFilter':
        """
        Add status(es) to filter. Stackable.
        
        Args:
            statuses: List of statuses (e.g., 'In Progress', 'On Hold', 'Pending', 
                      'Resolved', 'Rejected', 'Withdrawn', 'Closed')
        
        Returns:
            Self for chaining
        """
        if isinstance(statuses, str):
            statuses = [statuses]
        
        self.dimensions['statuses'].extend([s for s in statuses if s and s not in self.dimensions['statuses']])
        return self
    
    def set_statuses(self, statuses: List[str]) -> 'AnalyticsFilter':
        """
        Set (replace) statuses.
        """
        self.dimensions['statuses'] = list(set([s for s in statuses if s]))
        return self
    
    def get_statuses(self) -> List[str]:
        """Get current status filters"""
        return self.dimensions['statuses'].copy()
    
    # ========== Type / Category Filters ==========
    
    def add_types(self, types: List[str]) -> 'AnalyticsFilter':
        """
        Add ticket type/category to filter. Stackable.
        
        Args:
            types: List of ticket types/categories
        
        Returns:
            Self for chaining
        """
        if isinstance(types, str):
            types = [types]
        
        self.dimensions['types'].extend([t for t in types if t and t not in self.dimensions['types']])
        return self
    
    def add_categories(self, categories: List[str]) -> 'AnalyticsFilter':
        """
        Alias for add_types for category context.
        """
        return self.add_types(categories)
    
    def set_types(self, types: List[str]) -> 'AnalyticsFilter':
        """
        Set (replace) types.
        """
        self.dimensions['types'] = list(set([t for t in types if t]))
        return self
    
    def get_types(self) -> List[str]:
        """Get current type filters"""
        return self.dimensions['types'].copy()
    
    # ========== Query Building ==========
    
    def build_q_object(self) -> Q:
        """
        Build a Django Q object representing all active filters.
        
        Filters within a dimension are OR'd (union).
        Filters across dimensions are AND'd (intersection).
        
        Returns:
            Q object ready for queryset.filter()
        """
        q_object = Q()
        
        # Time range filters (AND with other dimensions)
        if self.dimensions['time_range']['start_date']:
            q_object &= Q(created_at__gte=self.dimensions['time_range']['start_date'])
        
        if self.dimensions['time_range']['end_date']:
            # Include entire end date (up to end of day)
            from datetime import timedelta
            end_date = self.dimensions['time_range']['end_date']
            q_object &= Q(created_at__lte=end_date + timedelta(days=1))
        
        # Department filter (OR within dimension, AND across dimensions)
        if self.dimensions['departments']:
            dept_q = Q()
            for dept in self.dimensions['departments']:
                dept_q |= Q(**{f"{self.field_mappings['department']}__icontains": dept})
            q_object &= dept_q
        
        # Role/Assignee filter
        if self.dimensions['roles']:
            role_q = Q()
            for role in self.dimensions['roles']:
                # Check both assigned_role and assignee fields
                role_q |= Q(**{f"{self.field_mappings['assigned_role']}__icontains": role})
                role_q |= Q(**{f"{self.field_mappings['assignee']}__icontains": role})
            q_object &= role_q
        
        # Priority filter
        if self.dimensions['priorities']:
            priority_q = Q()
            for priority in self.dimensions['priorities']:
                priority_q |= Q(**{f"{self.field_mappings['priority']}__icontains": priority})
            q_object &= priority_q
        
        # Status filter
        if self.dimensions['statuses']:
            status_q = Q()
            for status in self.dimensions['statuses']:
                status_q |= Q(**{f"{self.field_mappings['status']}__icontains": status})
            q_object &= status_q
        
        # Type/Category filter
        if self.dimensions['types']:
            type_q = Q()
            for ticket_type in self.dimensions['types']:
                type_q |= Q(**{f"{self.field_mappings['type']}__icontains": ticket_type})
            q_object &= type_q
        
        return q_object
    
    def build_filters_dict(self) -> Dict[str, Any]:
        """
        Build a dictionary of filter kwargs for use with queryset.filter().
        
        This is an alternative to build_q_object() for simpler use cases.
        Note: This approach is less flexible for OR operations within dimensions.
        
        Returns:
            Dictionary of filter kwargs
        """
        filters = {}
        
        # Time range
        if self.dimensions['time_range']['start_date']:
            filters['created_at__gte'] = self.dimensions['time_range']['start_date']
        
        if self.dimensions['time_range']['end_date']:
            from datetime import timedelta
            filters['created_at__lte'] = self.dimensions['time_range']['end_date'] + timedelta(days=1)
        
        return filters
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of active filters for display/logging.
        
        Returns:
            Dictionary with filter summary
        """
        return {
            'time_range': {
                'start': self.dimensions['time_range']['start_date'],
                'end': self.dimensions['time_range']['end_date'],
            },
            'departments': self.dimensions['departments'],
            'roles': self.dimensions['roles'],
            'priorities': self.dimensions['priorities'],
            'statuses': self.dimensions['statuses'],
            'types': self.dimensions['types'],
            'active_filters': self._count_active_filters(),
        }
    
    def clear(self) -> 'AnalyticsFilter':
        """
        Clear all filters. Returns self for chaining.
        """
        self.__init__()
        return self
    
    def clear_dimension(self, dimension: str) -> 'AnalyticsFilter':
        """
        Clear a specific filter dimension.
        
        Args:
            dimension: One of 'time_range', 'departments', 'roles', 'priorities', 'statuses', 'types'
        
        Returns:
            Self for chaining
        """
        if dimension == 'time_range':
            self.dimensions['time_range'] = {'start_date': None, 'end_date': None}
        elif dimension in self.dimensions:
            self.dimensions[dimension] = []
        
        return self
    
    # ========== Helper Methods ==========
    
    @staticmethod
    def _parse_date(date_str: str) -> date:
        """
        Parse ISO format date string.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
        
        Returns:
            date object
        
        Raises:
            ValueError: If date format is invalid
        """
        if isinstance(date_str, date):
            return date_str
        
        try:
            return datetime.fromisoformat(date_str).date()
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")
    
    def _count_active_filters(self) -> int:
        """Count number of active filter dimensions"""
        count = 0
        if self.dimensions['time_range']['start_date'] or self.dimensions['time_range']['end_date']:
            count += 1
        if self.dimensions['departments']:
            count += 1
        if self.dimensions['roles']:
            count += 1
        if self.dimensions['priorities']:
            count += 1
        if self.dimensions['statuses']:
            count += 1
        if self.dimensions['types']:
            count += 1
        return count
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize filter state to dictionary (for caching/storage).
        """
        return {
            'dimensions': {
                'time_range': {
                    'start_date': str(self.dimensions['time_range']['start_date']) if self.dimensions['time_range']['start_date'] else None,
                    'end_date': str(self.dimensions['time_range']['end_date']) if self.dimensions['time_range']['end_date'] else None,
                },
                'departments': self.dimensions['departments'].copy(),
                'roles': self.dimensions['roles'].copy(),
                'priorities': self.dimensions['priorities'].copy(),
                'statuses': self.dimensions['statuses'].copy(),
                'types': self.dimensions['types'].copy(),
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyticsFilter':
        """
        Restore filter state from dictionary (for loading from cache/storage).
        """
        filter_obj = cls()
        
        if 'dimensions' in data:
            dims = data['dimensions']
            
            # Restore time range
            if dims.get('time_range'):
                filter_obj.add_time_range(
                    dims['time_range'].get('start_date'),
                    dims['time_range'].get('end_date')
                )
            
            # Restore other dimensions
            if dims.get('departments'):
                filter_obj.add_departments(dims['departments'])
            if dims.get('roles'):
                filter_obj.add_roles(dims['roles'])
            if dims.get('priorities'):
                filter_obj.add_priorities(dims['priorities'])
            if dims.get('statuses'):
                filter_obj.add_statuses(dims['statuses'])
            if dims.get('types'):
                filter_obj.add_types(dims['types'])
        
        return filter_obj
