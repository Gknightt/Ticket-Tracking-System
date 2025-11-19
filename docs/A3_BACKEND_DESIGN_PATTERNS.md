# A.3 Application Design and Development (Backend Portions)

## Overview

This document focuses specifically on backend design patterns, algorithms, frameworks, and implementation details for the Django-based microservices in the Ticket Tracking System.

## Backend Architecture Principles

### 1. Separation of Concerns

Each Django service follows a layered architecture:

```
┌─────────────────────────────────────┐
│   Presentation Layer (Views/APIs)   │  ← HTTP Request/Response
├─────────────────────────────────────┤
│   Business Logic Layer (Services)   │  ← Core business rules
├─────────────────────────────────────┤
│   Data Access Layer (Models/ORM)    │  ← Database operations
├─────────────────────────────────────┤
│   Infrastructure Layer (Celery)     │  ← Async tasks, messaging
└─────────────────────────────────────┘
```

### 2. DRY (Don't Repeat Yourself)

- Shared utilities in `utils.py` modules
- Base classes for common view patterns
- Reusable serializers and mixins
- Shared Celery tasks

### 3. SOLID Principles

**Single Responsibility**: Each service handles one domain
**Open/Closed**: Extensible through inheritance and composition
**Liskov Substitution**: Proper use of Django's class-based views
**Interface Segregation**: Small, focused API endpoints
**Dependency Inversion**: Depend on abstractions (Django ORM, not raw SQL)

## Django Backend Design Patterns

### 1. Model-View-Serializer (MVS) Pattern

**Pattern**: Extension of MVC for REST APIs

**Implementation**:

```python
# models.py - Data layer
class Ticket(models.Model):
    """Domain model representing a support ticket"""
    ticket_id = models.CharField(max_length=50, unique=True)
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=50, 
                             choices=[('open', 'Open'), 
                                     ('closed', 'Closed')])
    priority = models.CharField(max_length=20)
    
    class Meta:
        db_table = 'tickets'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.ticket_id}: {self.subject}"

# serializers.py - Transformation layer
from rest_framework import serializers

class TicketSerializer(serializers.ModelSerializer):
    """Converts Ticket model to/from JSON"""
    
    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ('ticket_id', 'created_at', 'updated_at')
    
    def validate_priority(self, value):
        """Custom validation for priority field"""
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if value not in valid_priorities:
            raise serializers.ValidationError(
                f"Priority must be one of: {', '.join(valid_priorities)}"
            )
        return value
    
    def create(self, validated_data):
        """Custom creation logic"""
        # Generate ticket ID
        validated_data['ticket_id'] = generate_ticket_id()
        return super().create(validated_data)

# views.py - Presentation layer
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class TicketViewSet(viewsets.ModelViewSet):
    """
    API endpoint for ticket CRUD operations
    
    list: GET /tickets/
    create: POST /tickets/
    retrieve: GET /tickets/{id}/
    update: PUT /tickets/{id}/
    partial_update: PATCH /tickets/{id}/
    destroy: DELETE /tickets/{id}/
    """
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter tickets by user role"""
        user = self.request.user
        if user.is_staff:
            return Ticket.objects.all()
        return Ticket.objects.filter(assigned_to=user.email)
    
    def perform_create(self, serializer):
        """Add user context to ticket creation"""
        serializer.save(created_by=self.request.user.email)
```

### 2. Service Layer Pattern

**Purpose**: Encapsulate complex business logic outside views

**Implementation**:

```python
# services.py - Business logic layer
from .models import Ticket, WorkflowTicket
from role.services import get_users_by_role
from notifications.tasks import send_notification
import logging

logger = logging.getLogger(__name__)

class TicketService:
    """Service class for ticket business logic"""
    
    @staticmethod
    def create_ticket_with_workflow(ticket_data, user):
        """
        Create ticket and trigger workflow processing
        
        Args:
            ticket_data: Dictionary with ticket information
            user: User creating the ticket
        
        Returns:
            Ticket instance
        
        Raises:
            ValidationError: If ticket data invalid
        """
        # 1. Validate data
        if not ticket_data.get('subject'):
            raise ValidationError("Subject is required")
        
        # 2. Create ticket
        ticket = Ticket.objects.create(
            **ticket_data,
            created_by=user.email
        )
        logger.info(f"Ticket {ticket.ticket_id} created by {user.email}")
        
        # 3. Trigger workflow (async)
        from .tasks import push_ticket_to_workflow
        push_ticket_to_workflow.delay({
            'ticket_id': ticket.ticket_id,
            'category': ticket.category,
            'priority': ticket.priority,
            # ... other fields
        })
        
        return ticket
    
    @staticmethod
    def assign_ticket(ticket, assignee_email):
        """
        Assign ticket to user
        
        Args:
            ticket: Ticket instance
            assignee_email: Email of user to assign to
        
        Returns:
            Updated ticket
        """
        ticket.assigned_to = assignee_email
        ticket.status = 'assigned'
        ticket.save()
        
        # Send notification
        send_notification.delay(
            recipient=assignee_email,
            subject=f"Ticket {ticket.ticket_id} assigned to you",
            message=f"You have been assigned: {ticket.subject}"
        )
        
        logger.info(f"Ticket {ticket.ticket_id} assigned to {assignee_email}")
        return ticket
    
    @staticmethod
    def bulk_update_status(ticket_ids, new_status):
        """
        Update status of multiple tickets
        
        Args:
            ticket_ids: List of ticket IDs
            new_status: New status value
        
        Returns:
            Number of tickets updated
        """
        updated = Ticket.objects.filter(
            ticket_id__in=ticket_ids
        ).update(status=new_status)
        
        logger.info(f"Updated {updated} tickets to status '{new_status}'")
        return updated

# views.py - View uses service
class TicketViewSet(viewsets.ModelViewSet):
    # ...
    
    def create(self, request):
        """Create ticket using service layer"""
        try:
            ticket = TicketService.create_ticket_with_workflow(
                ticket_data=request.data,
                user=request.user
            )
            serializer = TicketSerializer(ticket)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
```

### 3. Repository Pattern (Django ORM as Repository)

**Implementation using Django's Manager**:

```python
# models.py
from django.db import models

class TicketQuerySet(models.QuerySet):
    """Custom queryset with business logic"""
    
    def open_tickets(self):
        """Get all open tickets"""
        return self.filter(status='open')
    
    def high_priority(self):
        """Get high priority tickets"""
        return self.filter(priority__in=['high', 'urgent'])
    
    def assigned_to_user(self, user_email):
        """Get tickets assigned to specific user"""
        return self.filter(assigned_to=user_email)
    
    def overdue(self):
        """Get overdue tickets based on SLA"""
        from django.utils import timezone
        from datetime import timedelta
        
        deadline = timezone.now() - timedelta(days=7)
        return self.filter(
            created_at__lt=deadline,
            status='open'
        )

class TicketManager(models.Manager):
    """Custom manager for Ticket model"""
    
    def get_queryset(self):
        return TicketQuerySet(self.model, using=self._db)
    
    def open_tickets(self):
        return self.get_queryset().open_tickets()
    
    def high_priority(self):
        return self.get_queryset().high_priority()
    
    def create_with_id(self, **kwargs):
        """Create ticket with auto-generated ID"""
        kwargs['ticket_id'] = self._generate_id()
        return self.create(**kwargs)
    
    def _generate_id(self):
        """Generate unique ticket ID"""
        from datetime import datetime
        prefix = "TKT"
        timestamp = datetime.now().strftime("%Y%m%d")
        count = self.filter(ticket_id__startswith=f"{prefix}-{timestamp}").count()
        return f"{prefix}-{timestamp}-{count + 1:04d}"

class Ticket(models.Model):
    # ... fields ...
    
    objects = TicketManager()  # Custom manager
    
    # Usage:
    # Ticket.objects.open_tickets()
    # Ticket.objects.high_priority()
    # Ticket.objects.create_with_id(subject="New ticket")
```

### 4. Factory Pattern (Model Factories for Testing)

```python
# tests/factories.py
import factory
from factory.django import DjangoModelFactory
from tickets.models import Ticket
from django.utils import timezone

class TicketFactory(DjangoModelFactory):
    """Factory for creating test tickets"""
    
    class Meta:
        model = Ticket
    
    ticket_id = factory.Sequence(lambda n: f"TKT-TEST-{n:04d}")
    subject = factory.Faker('sentence', nb_words=6)
    description = factory.Faker('paragraph')
    category = factory.Iterator(['Technical Support', 'Billing', 'General Inquiry'])
    subcategory = factory.Iterator(['Hardware', 'Software', 'Network'])
    priority = factory.Iterator(['low', 'medium', 'high', 'urgent'])
    status = 'open'
    department = 'IT'
    created_at = factory.LazyFunction(timezone.now)
    
    # Related factory
    @factory.post_generation
    def with_attachments(self, create, extracted, **kwargs):
        if extracted:
            self.attachments = [
                {'filename': 'test.pdf', 'url': '/media/test.pdf'}
            ]
            self.save()

# Usage in tests:
# ticket = TicketFactory()
# high_priority_ticket = TicketFactory(priority='high')
# ticket_with_files = TicketFactory(with_attachments=True)
```

### 5. Strategy Pattern (Authentication Strategies)

```python
# authentication.py
from abc import ABC, abstractmethod
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

class AuthenticationStrategy(ABC):
    """Abstract authentication strategy"""
    
    @abstractmethod
    def authenticate(self, request):
        pass

class JWTAuthStrategy(AuthenticationStrategy):
    """JWT token authentication strategy"""
    
    def __init__(self):
        self.jwt_auth = JWTAuthentication()
    
    def authenticate(self, request):
        return self.jwt_auth.authenticate(request)

class SessionAuthStrategy(AuthenticationStrategy):
    """Session-based authentication strategy"""
    
    def __init__(self):
        self.session_auth = SessionAuthentication()
    
    def authenticate(self, request):
        return self.session_auth.authenticate(request)

class APIKeyAuthStrategy(AuthenticationStrategy):
    """API key authentication strategy"""
    
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_API_KEY')
        if not api_key:
            return None
        
        # Validate API key
        if self._is_valid_key(api_key):
            return (AnonymousUser(), None)
        return None
    
    def _is_valid_key(self, key):
        from django.conf import settings
        return key in settings.NOTIFICATION_API_KEYS

# Usage in views:
class MultiAuthView(APIView):
    """View supporting multiple auth strategies"""
    
    def get_authenticators(self):
        """Return list of authentication strategies"""
        return [
            JWTAuthStrategy(),
            SessionAuthStrategy(),
            APIKeyAuthStrategy()
        ]
```

## Backend-Specific Algorithms

### 1. Workflow Matching Algorithm with Priority

```python
# workflow_api/workflow/services.py
from .models import Workflows
import logging

logger = logging.getLogger(__name__)

def match_workflow_advanced(ticket):
    """
    Advanced workflow matching with priority and fallback
    
    Algorithm:
    1. Try exact match (category + subcategory + department + priority)
    2. Try match without priority (category + subcategory + department)
    3. Try match with just category and department
    4. Return default workflow if configured
    5. Return None if no match found
    
    Args:
        ticket: Ticket instance
    
    Returns:
        Workflows instance or None
    """
    
    # Level 1: Exact match
    workflow = Workflows.objects.filter(
        category=ticket.category,
        subcategory=ticket.subcategory,
        department=ticket.department,
        priority=ticket.priority,
        is_published=True
    ).order_by('-created_at').first()
    
    if workflow:
        logger.info(f"Exact match found: {workflow.workflow_id}")
        return workflow
    
    # Level 2: Match without priority
    workflow = Workflows.objects.filter(
        category=ticket.category,
        subcategory=ticket.subcategory,
        department=ticket.department,
        is_published=True
    ).order_by('-created_at').first()
    
    if workflow:
        logger.info(f"Match without priority: {workflow.workflow_id}")
        return workflow
    
    # Level 3: Broad match (category + department)
    workflow = Workflows.objects.filter(
        category=ticket.category,
        department=ticket.department,
        is_published=True
    ).order_by('-created_at').first()
    
    if workflow:
        logger.info(f"Broad match: {workflow.workflow_id}")
        return workflow
    
    # Level 4: Default workflow
    workflow = Workflows.objects.filter(
        name='Default Workflow',
        is_published=True
    ).first()
    
    if workflow:
        logger.info(f"Using default workflow: {workflow.workflow_id}")
        return workflow
    
    # Level 5: No match
    logger.warning(f"No workflow found for ticket {ticket.ticket_id}")
    return None
```

### 2. Round-Robin Assignment with Load Balancing

```python
# workflow_api/role/services.py
from .models import RoleRoundRobinPointer
from collections import defaultdict
import requests
from django.conf import settings

def assign_task_with_load_balancing(role_id, task):
    """
    Round-robin assignment considering current user workload
    
    Algorithm:
    1. Fetch all users with role
    2. Get current task count per user
    3. Sort users by task count (ascending)
    4. Assign to user with least tasks
    5. Update round-robin pointer
    
    Args:
        role_id: Role UUID
        task: Task instance
    
    Returns:
        Dict with assigned user info
    """
    
    # Step 1: Get users from auth service
    users = _fetch_users_by_role(role_id)
    
    if not users:
        raise Exception(f"No users found for role {role_id}")
    
    # Step 2: Get current workload for each user
    from task.models import Task
    user_workload = defaultdict(int)
    
    for user in users:
        active_tasks = Task.objects.filter(
            stepinstance__user_id=user['id'],
            stepinstance__has_acted=False
        ).count()
        user_workload[user['id']] = active_tasks
    
    # Step 3: Sort by workload
    sorted_users = sorted(users, key=lambda u: user_workload[u['id']])
    
    # Step 4: Assign to user with least workload
    assigned_user = sorted_users[0]
    
    # Step 5: Create step instance
    from step_instance.models import StepInstance
    StepInstance.objects.create(
        task=task,
        user_id=assigned_user['id'],
        step_transition=task.workflow.get_initial_transition()
    )
    
    # Update pointer (for fallback to simple round-robin)
    pointer, _ = RoleRoundRobinPointer.objects.get_or_create(
        role_id=role_id,
        defaults={'pointer': 0}
    )
    
    # Find index of assigned user
    assigned_index = next(
        (i for i, u in enumerate(users) if u['id'] == assigned_user['id']),
        0
    )
    pointer.pointer = (assigned_index + 1) % len(users)
    pointer.save()
    
    logger.info(
        f"Task {task.task_id} assigned to {assigned_user['email']} "
        f"(workload: {user_workload[assigned_user['id']]})"
    )
    
    return assigned_user

def _fetch_users_by_role(role_id):
    """Fetch users from auth service"""
    auth_service_url = settings.DJANGO_AUTH_SERVICE
    url = f"{auth_service_url}/api/v1/tts/roles/{role_id}/users/"
    
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    
    return response.json().get('users', [])
```

### 3. SLA Calculation Algorithm

```python
# workflow_api/workflow/utils.py
from datetime import timedelta
from django.utils import timezone

class SLACalculator:
    """Calculate SLA deadlines and breaches"""
    
    # Business hours: Monday-Friday, 9 AM - 5 PM
    BUSINESS_HOURS_START = 9
    BUSINESS_HOURS_END = 17
    
    def __init__(self, workflow):
        self.workflow = workflow
    
    def calculate_deadline(self, ticket_created_at, priority):
        """
        Calculate SLA deadline based on priority
        
        Args:
            ticket_created_at: Ticket creation timestamp
            priority: Ticket priority (low, medium, high, urgent)
        
        Returns:
            datetime: SLA deadline
        """
        # Get SLA duration from workflow
        sla_map = {
            'low': self.workflow.low_sla,
            'medium': self.workflow.medium_sla,
            'high': self.workflow.high_sla,
            'urgent': self.workflow.urgent_sla
        }
        
        sla_duration = sla_map.get(priority, self.workflow.medium_sla)
        
        if not sla_duration:
            # Default: 2 business days
            sla_duration = timedelta(days=2)
        
        # Calculate deadline considering business hours
        deadline = self._add_business_time(ticket_created_at, sla_duration)
        
        return deadline
    
    def _add_business_time(self, start_time, duration):
        """
        Add business time duration to start time
        
        Args:
            start_time: Starting datetime
            duration: timedelta to add (in business hours)
        
        Returns:
            datetime: End time
        """
        current = start_time
        remaining_hours = duration.total_seconds() / 3600
        
        while remaining_hours > 0:
            # Skip weekends
            if current.weekday() >= 5:  # Saturday or Sunday
                current += timedelta(days=1)
                current = current.replace(hour=self.BUSINESS_HOURS_START, minute=0)
                continue
            
            # Check if within business hours
            if current.hour < self.BUSINESS_HOURS_START:
                current = current.replace(hour=self.BUSINESS_HOURS_START, minute=0)
            elif current.hour >= self.BUSINESS_HOURS_END:
                # Move to next business day
                current += timedelta(days=1)
                current = current.replace(hour=self.BUSINESS_HOURS_START, minute=0)
                continue
            
            # Calculate hours left in business day
            hours_left_today = self.BUSINESS_HOURS_END - current.hour - (current.minute / 60)
            
            if remaining_hours <= hours_left_today:
                # Can finish within today
                current += timedelta(hours=remaining_hours)
                remaining_hours = 0
            else:
                # Move to next business day
                remaining_hours -= hours_left_today
                current += timedelta(days=1)
                current = current.replace(hour=self.BUSINESS_HOURS_START, minute=0)
        
        return current
    
    def is_sla_breached(self, ticket):
        """
        Check if ticket has breached SLA
        
        Args:
            ticket: Ticket instance
        
        Returns:
            bool: True if SLA breached
        """
        deadline = self.calculate_deadline(ticket.created_at, ticket.priority)
        return timezone.now() > deadline
    
    def get_remaining_time(self, ticket):
        """
        Get remaining time before SLA breach
        
        Args:
            ticket: Ticket instance
        
        Returns:
            timedelta: Remaining time (negative if breached)
        """
        deadline = self.calculate_deadline(ticket.created_at, ticket.priority)
        return deadline - timezone.now()

# Usage:
# calculator = SLACalculator(workflow)
# deadline = calculator.calculate_deadline(ticket.created_at, 'high')
# is_breached = calculator.is_sla_breached(ticket)
```

### 4. Audit Logging Algorithm

```python
# workflow_api/audit/services.py
import json
from django.utils import timezone
from .models import AuditLog

class AuditLogger:
    """Centralized audit logging service"""
    
    ACTIONS = {
        'CREATE': 'create',
        'UPDATE': 'update',
        'DELETE': 'delete',
        'VIEW': 'view',
        'ASSIGN': 'assign',
        'TRANSITION': 'transition',
        'APPROVE': 'approve',
        'REJECT': 'reject'
    }
    
    @classmethod
    def log(cls, action, user, resource_type, resource_id, 
            old_value=None, new_value=None, metadata=None):
        """
        Log an audit event
        
        Args:
            action: Action type (from ACTIONS)
            user: User performing action
            resource_type: Type of resource (ticket, task, workflow)
            resource_id: ID of resource
            old_value: Previous value (for updates)
            new_value: New value (for updates)
            metadata: Additional context
        """
        audit_entry = AuditLog.objects.create(
            action=action,
            user_id=user.id if user else None,
            user_email=user.email if user else 'system',
            resource_type=resource_type,
            resource_id=str(resource_id),
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            metadata=json.dumps(metadata) if metadata else None,
            timestamp=timezone.now(),
            ip_address=cls._get_ip_from_request()
        )
        
        return audit_entry
    
    @classmethod
    def log_workflow_transition(cls, task, user, from_step, to_step, action):
        """Log workflow transition"""
        return cls.log(
            action=cls.ACTIONS['TRANSITION'],
            user=user,
            resource_type='task',
            resource_id=task.task_id,
            old_value={'step': from_step.name},
            new_value={'step': to_step.name},
            metadata={
                'action': action.name,
                'workflow': task.workflow.workflow_id,
                'ticket': task.ticket.ticket_id
            }
        )
    
    @classmethod
    def log_ticket_update(cls, ticket, user, changed_fields):
        """Log ticket update"""
        old_values = {}
        new_values = {}
        
        for field in changed_fields:
            old_values[field] = getattr(ticket, f'_{field}_original', None)
            new_values[field] = getattr(ticket, field)
        
        return cls.log(
            action=cls.ACTIONS['UPDATE'],
            user=user,
            resource_type='ticket',
            resource_id=ticket.ticket_id,
            old_value=old_values,
            new_value=new_values
        )
    
    @classmethod
    def get_audit_trail(cls, resource_type, resource_id):
        """Get complete audit trail for a resource"""
        return AuditLog.objects.filter(
            resource_type=resource_type,
            resource_id=str(resource_id)
        ).order_by('-timestamp')
    
    @staticmethod
    def _get_ip_from_request():
        """Extract IP from current request context"""
        from middleware.current_request import get_current_request
        request = get_current_request()
        
        if not request:
            return None
        
        # Get IP from headers (for proxied requests)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        
        return request.META.get('REMOTE_ADDR')

# Usage:
# AuditLogger.log_workflow_transition(task, user, from_step, to_step, action)
# audit_trail = AuditLogger.get_audit_trail('ticket', 'TKT-001')
```

## Backend Framework Configuration

### Django Settings Structure

```python
# settings.py - Comprehensive configuration
import os
from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Environment
DJANGO_ENV = config('DJANGO_ENV', default='development')
IS_PRODUCTION = DJANGO_ENV.lower() == 'production'

# Security
SECRET_KEY = config(
    'DJANGO_SECRET_KEY',
    default='insecure-dev-key' if not IS_PRODUCTION else None
)

if IS_PRODUCTION and not SECRET_KEY:
    raise ValueError('DJANGO_SECRET_KEY must be set in production')

DEBUG = config('DJANGO_DEBUG', default=not IS_PRODUCTION, cast=bool)

ALLOWED_HOSTS = config(
    'DJANGO_ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    
    # Local apps
    'tickets',
    'workflow',
    'tasks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Database
if config('DATABASE_URL', default=''):
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif IS_PRODUCTION:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('POSTGRES_DB'),
            'USER': config('POSTGRES_USER'),
            'PASSWORD': config('POSTGRES_PASSWORD'),
            'HOST': config('PGHOST', default='localhost'),
            'PORT': config('PGPORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Celery Configuration
CELERY_BROKER_URL = config(
    'DJANGO_CELERY_BROKER_URL',
    default='amqp://admin:admin@localhost:5672/'
)
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Task routing
CELERY_TASK_ROUTES = {
    'tickets.tasks.push_ticket_to_workflow': {
        'queue': 'TICKET_TASKS_PRODUCTION'
    },
    'notifications.tasks.*': {
        'queue': 'notification-queue-default'
    },
}

# CORS
CORS_ALLOWED_ORIGINS = config(
    'DJANGO_CORS_ALLOWED_ORIGINS',
    default='http://localhost:1000,http://localhost:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)
CORS_ALLOW_CREDENTIALS = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'app.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Celery Configuration

```python
# celery.py - Celery application setup
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workflow_api.settings')

app = Celery('workflow_api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

## Performance Optimization Techniques

### 1. Database Query Optimization

```python
# Optimize with select_related (for ForeignKey)
tickets = Ticket.objects.select_related('workflow', 'assigned_user').all()

# Optimize with prefetch_related (for ManyToMany/reverse FK)
workflows = Workflow.objects.prefetch_related('steps', 'transitions').all()

# Use only() to fetch specific fields
tickets = Ticket.objects.only('id', 'ticket_id', 'subject', 'status').all()

# Use defer() to exclude heavy fields
tickets = Ticket.objects.defer('description', 'attachments').all()

# Aggregate queries
from django.db.models import Count, Avg
stats = Ticket.objects.aggregate(
    total=Count('id'),
    avg_priority=Avg('priority')
)

# Bulk operations
tickets_to_update = [...]
Ticket.objects.bulk_update(tickets_to_update, ['status'], batch_size=100)
```

### 2. Caching Strategy

```python
# Using Django's cache framework
from django.core.cache import cache

def get_user_tickets(user_id):
    """Get user tickets with caching"""
    cache_key = f'user_tickets_{user_id}'
    tickets = cache.get(cache_key)
    
    if tickets is None:
        tickets = list(Ticket.objects.filter(assigned_to=user_id))
        cache.set(cache_key, tickets, timeout=300)  # 5 minutes
    
    return tickets

# Invalidate cache on update
from django.db.models.signals import post_save

@receiver(post_save, sender=Ticket)
def invalidate_ticket_cache(sender, instance, **kwargs):
    cache_key = f'user_tickets_{instance.assigned_to}'
    cache.delete(cache_key)
```

### 3. Async Task Optimization

```python
# Batch processing with Celery
from celery import group

@shared_task
def process_single_ticket(ticket_id):
    """Process one ticket"""
    ticket = Ticket.objects.get(id=ticket_id)
    # ... processing logic

@shared_task
def process_tickets_batch(ticket_ids):
    """Process multiple tickets in parallel"""
    job = group(process_single_ticket.s(tid) for tid in ticket_ids)
    result = job.apply_async()
    return result.get()
```

## References

- **Main Architecture Document**: `/docs/A1_SYSTEM_ARCHITECTURE.md`
- **Integration Details**: `/docs/A2_INFORMATION_SYSTEMS_INTEGRATION.md`
- **General Application Design**: `/docs/A3_APPLICATION_DESIGN_AND_DEVELOPMENT.md`
- **Django Best Practices**: https://docs.djangoproject.com/en/stable/topics/db/optimization/
- **Celery Documentation**: https://docs.celeryq.dev/en/stable/

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Authors**: Backend Development Team
