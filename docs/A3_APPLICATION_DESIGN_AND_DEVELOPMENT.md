# A.3 Application Design and Development

## Overview

This document provides comprehensive details about the application's design, development patterns, algorithms, code structure, and implementation specifics across both frontend and backend components.

## Software Design Patterns

### 1. Microservices Architecture Pattern

**Pattern**: Distributed system architecture where application is composed of small, independent services

**Implementation**:
- 5 independent Django services (auth, ticket_service, workflow_api, messaging, notification_service)
- Each service has its own database schema
- Communication via REST APIs and message queues
- Independent deployment and scaling

**Benefits**:
- **Scalability**: Each service scales independently
- **Maintainability**: Smaller, focused codebases
- **Technology diversity**: Can use different tech stacks per service
- **Fault isolation**: One service failure doesn't crash entire system

**Code Example**:
```python
# Each service has independent settings.py
# ticket_service/ticket_service/settings.py
DATABASES = {
    'default': {
        'NAME': 'ticketmanagement'  # Separate database
    }
}

# workflow_api/workflow_api/settings.py
DATABASES = {
    'default': {
        'NAME': 'workflowmanagement'  # Different database
    }
}
```

### 2. Repository Pattern (Django ORM)

**Pattern**: Abstraction layer between business logic and data access

**Implementation**: Django ORM provides repository-like interface

**Example**:
```python
# models.py - Data model definition
class Ticket(models.Model):
    ticket_id = models.CharField(max_length=50, unique=True)
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'tickets'

# views.py - Business logic uses ORM as repository
class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()  # Repository-like access
    serializer_class = TicketSerializer
    
    def get_queryset(self):
        # Custom query logic
        return Ticket.objects.filter(status='open').order_by('-created_at')
```

### 3. Service Layer Pattern

**Pattern**: Business logic separated into service classes/functions

**Implementation**: Service modules handle complex business operations

**Example**:
```python
# workflow_api/workflow/services.py
def match_and_assign_workflow(workflow_ticket):
    """
    Service function to match ticket to workflow and assign
    """
    # 1. Find matching workflow
    workflow = Workflows.objects.filter(
        category=workflow_ticket.category,
        subcategory=workflow_ticket.subcategory,
        department=workflow_ticket.department,
        is_published=True
    ).first()
    
    if not workflow:
        return None
    
    # 2. Get initial step
    initial_step = workflow.steps.filter(order=1).first()
    
    # 3. Create task
    task = Task.objects.create(
        ticket=workflow_ticket,
        workflow=workflow
    )
    
    # 4. Assign to role (round-robin)
    assign_to_role(task, initial_step.role)
    
    return task

# views.py - View calls service
class TicketViewSet(viewsets.ModelViewSet):
    def create(self, request):
        # ... validation ...
        workflow_ticket = WorkflowTicket.objects.create(**validated_data)
        task = match_and_assign_workflow(workflow_ticket)  # Service call
        return Response({'task_id': task.task_id})
```

### 4. Observer Pattern (Django Signals)

**Pattern**: Event-driven notification when object state changes

**Implementation**: Django signals trigger actions on model events

**Example**:
```python
# ticket_service/tickets/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ticket
from .tasks import push_ticket_to_workflow

@receiver(post_save, sender=Ticket)
def trigger_workflow_on_ticket_creation(sender, instance, created, **kwargs):
    """
    Observer: When Ticket is created, trigger workflow
    """
    if created:
        ticket_data = serialize_ticket(instance)
        push_ticket_to_workflow.delay(ticket_data)  # Async notification

# models.py
# Signal automatically triggered when Ticket.save() called
ticket = Ticket.objects.create(subject="New ticket")  
# → post_save signal fires → push_ticket_to_workflow called
```

### 5. Factory Pattern (Serializer Creation)

**Pattern**: Object creation without specifying exact class

**Implementation**: Django REST Framework serializers

**Example**:
```python
# serializers.py
class TicketSerializer(serializers.ModelSerializer):
    """Factory for creating Ticket instances from data"""
    class Meta:
        model = Ticket
        fields = '__all__'

# views.py
class TicketViewSet(viewsets.ModelViewSet):
    def create(self, request):
        serializer = TicketSerializer(data=request.data)  # Factory
        if serializer.is_valid():
            serializer.save()  # Creates Ticket instance
            return Response(serializer.data, status=201)
```

### 6. Strategy Pattern (Authentication Backends)

**Pattern**: Different algorithms/strategies for same operation

**Implementation**: JWT token authentication with multiple validation strategies

**Example**:
```python
# auth/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication

class CustomJWTAuthentication(JWTAuthentication):
    """Strategy for JWT token authentication"""
    def authenticate(self, request):
        # Strategy: Extract and validate JWT
        header = self.get_header(request)
        if header is None:
            return None
        
        raw_token = self.get_raw_token(header)
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token

# Alternative strategy could be SessionAuthentication
# from rest_framework.authentication import SessionAuthentication
```

### 7. Decorator Pattern (Permission Checks)

**Pattern**: Add behavior to objects without modifying structure

**Implementation**: Django REST Framework permission decorators

**Example**:
```python
# permissions.py
from rest_framework.permissions import BasePermission

class IsSystemAdminOrSuperUser(BasePermission):
    """Decorator-like permission class"""
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and
            (request.user.is_superuser or is_system_admin(request.user))
        )

# views.py
class RoleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSystemAdminOrSuperUser]  # Decorator pattern
    
    def list(self, request):
        # Only executed if permission check passes
        return Response(roles)
```

### 8. Template Method Pattern (Generic Views)

**Pattern**: Define skeleton of algorithm, let subclasses override steps

**Implementation**: Django generic views and DRF viewsets

**Example**:
```python
# views.py
from rest_framework import viewsets

class TicketViewSet(viewsets.ModelViewSet):
    """Template method pattern - ModelViewSet defines skeleton"""
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    
    # Override specific steps
    def get_queryset(self):
        """Customize query step"""
        user = self.request.user
        return Ticket.objects.filter(assigned_to=user.email)
    
    def perform_create(self, serializer):
        """Customize create step"""
        serializer.save(created_by=self.request.user)
```

### 9. Adapter Pattern (Database URL Parsing)

**Pattern**: Convert interface of class to another interface

**Implementation**: `dj-database-url` adapts URL to Django DATABASE dict

**Example**:
```python
# settings.py
import dj_database_url

# Adapter: Convert DATABASE_URL to Django DATABASES format
if config('DATABASE_URL', default=''):
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL'),  # Input: URL string
            # Output: Django database config dict
        )
    }
    # URL: "postgres://user:pass@host:5432/db"
    # → Dict: {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'db', ...}
```

### 10. Publish-Subscribe Pattern (Celery Tasks)

**Pattern**: Message broadcast to multiple subscribers

**Implementation**: RabbitMQ queues with Celery workers

**Example**:
```python
# Publisher: ticket_service
from celery import current_app as celery_app

def notify_ticket_created(ticket_data):
    # Publish to multiple queues
    celery_app.send_task(
        'workflow.tasks.process_ticket',
        args=[ticket_data],
        queue='TICKET_TASKS_PRODUCTION'
    )
    celery_app.send_task(
        'notifications.tasks.notify_admin',
        args=[ticket_data],
        queue='notification-queue-default'
    )

# Subscriber 1: workflow-worker
@shared_task
def process_ticket(ticket_data):
    # Process workflow
    pass

# Subscriber 2: notification-worker
@shared_task
def notify_admin(ticket_data):
    # Send notification
    pass
```

## Key Algorithms

### 1. Round-Robin User Assignment Algorithm

**Purpose**: Fairly distribute tasks among users with same role

**Algorithm**:
```
1. Get list of users with target role from Auth Service
2. Fetch current pointer position for this role (RoleRoundRobinPointer)
3. If pointer >= user count, reset to 0
4. Assign task to user at pointer index
5. Increment pointer and save
6. Return assigned user
```

**Implementation**:
```python
# workflow_api/role/services.py
def assign_task_round_robin(role_id, task):
    """
    Round-robin assignment algorithm
    """
    # Step 1: Get users with role
    users = get_users_from_auth_service(role_id)
    
    if not users:
        raise Exception("No users found for role")
    
    # Step 2: Get or create pointer
    pointer_obj, created = RoleRoundRobinPointer.objects.get_or_create(
        role_id=role_id,
        defaults={'pointer': 0}
    )
    
    # Step 3: Check bounds and reset if needed
    if pointer_obj.pointer >= len(users):
        pointer_obj.pointer = 0
    
    # Step 4: Get user at current pointer
    assigned_user = users[pointer_obj.pointer]
    
    # Step 5: Increment pointer for next assignment
    pointer_obj.pointer += 1
    pointer_obj.save()
    
    # Step 6: Create assignment
    assign_task_to_user(task, assigned_user['id'], assigned_user['email'])
    
    return assigned_user
```

**Time Complexity**: O(1) for pointer operations, O(n) for user fetch

**Space Complexity**: O(1) - only stores pointer position

### 2. Workflow Matching Algorithm

**Purpose**: Find appropriate workflow for a ticket based on attributes

**Algorithm**:
```
1. Extract ticket attributes (category, subcategory, department, priority)
2. Query workflows with exact match on all attributes
3. Filter by is_published=True
4. Order by priority (urgent > high > medium > low)
5. Return first match
6. If no match, try partial match (category + department only)
7. Return None if no workflow found
```

**Implementation**:
```python
# workflow_api/workflow/services.py
def match_workflow(ticket):
    """
    Workflow matching algorithm with fallback
    """
    # Step 1-5: Exact match
    workflow = Workflows.objects.filter(
        category=ticket.category,
        subcategory=ticket.subcategory,
        department=ticket.department,
        priority=ticket.priority,
        is_published=True
    ).order_by('-priority').first()
    
    if workflow:
        return workflow
    
    # Step 6-7: Fallback to partial match
    workflow = Workflows.objects.filter(
        category=ticket.category,
        department=ticket.department,
        is_published=True
    ).order_by('-priority').first()
    
    return workflow
```

**Time Complexity**: O(log n) with database indexes

**Space Complexity**: O(1)

### 3. JWT Token Validation Algorithm

**Purpose**: Verify JWT token authenticity and extract user info

**Algorithm**:
```
1. Extract token from Authorization header
2. Decode JWT header to get algorithm
3. Verify signature using secret key and algorithm
4. Check token expiration (exp claim)
5. Extract user_id from payload
6. Return user_id if valid, raise exception if invalid
```

**Implementation**:
```python
# Handled by djangorestframework-simplejwt library
# Simplified conceptual implementation:

import jwt
from django.conf import settings
from datetime import datetime

def validate_jwt_token(token_string):
    """
    JWT validation algorithm
    """
    try:
        # Step 2-3: Decode and verify signature
        payload = jwt.decode(
            token_string,
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        
        # Step 4: Check expiration
        exp_timestamp = payload.get('exp')
        if datetime.now().timestamp() > exp_timestamp:
            raise Exception("Token expired")
        
        # Step 5: Extract user_id
        user_id = payload.get('user_id')
        
        return user_id
    except jwt.InvalidSignatureError:
        raise Exception("Invalid token signature")
    except jwt.DecodeError:
        raise Exception("Invalid token format")
```

**Time Complexity**: O(1) - constant time signature verification

**Space Complexity**: O(1)

### 4. Rate Limiting Algorithm (Token Bucket)

**Purpose**: Prevent abuse by limiting request rate per IP/device

**Algorithm**:
```
1. Get IP address and device fingerprint from request
2. Check IPAddressRateLimit table for IP
3. If failed_attempts >= threshold:
   - Check if block expired
   - If not expired, reject request
4. Check DeviceFingerprint table for device
5. If failed_attempts >= captcha_threshold, require CAPTCHA
6. If failed_attempts >= block_threshold, block device
7. Allow request if all checks pass
```

**Implementation**:
```python
# auth/rate_limiting.py
from datetime import datetime, timedelta

def check_login_rate_limits(request):
    """
    Rate limiting algorithm
    """
    ip_address = get_client_ip(request)
    device_fingerprint = generate_device_fingerprint(request)
    
    # Check IP rate limit
    ip_limit, _ = IPAddressRateLimit.objects.get_or_create(
        ip_address=ip_address
    )
    
    # IP blocking logic
    if ip_limit.blocked_until and ip_limit.blocked_until > datetime.now():
        return {
            'login_allowed': False,
            'reason': 'IP blocked',
            'blocked_until': ip_limit.blocked_until
        }
    
    if ip_limit.failed_attempts >= settings.IP_ATTEMPT_THRESHOLD:
        ip_limit.blocked_until = datetime.now() + timedelta(minutes=30)
        ip_limit.save()
        return {
            'login_allowed': False,
            'reason': 'Too many attempts from IP'
        }
    
    # Check device fingerprint
    device_limit, _ = DeviceFingerprint.objects.get_or_create(
        fingerprint_hash=device_fingerprint
    )
    
    captcha_required = device_limit.failed_attempts >= 5
    
    if device_limit.failed_attempts >= 8:
        device_limit.blocked_until = datetime.now() + timedelta(minutes=20)
        device_limit.save()
        return {
            'login_allowed': False,
            'captcha_required': True,
            'reason': 'Device blocked'
        }
    
    return {
        'login_allowed': True,
        'captcha_required': captcha_required
    }
```

**Time Complexity**: O(1) - database lookups with indexed fields

**Space Complexity**: O(n) where n = unique IPs/devices

### 5. Workflow Step Transition Algorithm

**Purpose**: Determine next step in workflow based on action

**Algorithm**:
```
1. Get current StepInstance for task
2. Validate user has permission to act on this step
3. Look up StepTransition for (current_step, action)
4. If transition exists:
   a. Mark current StepInstance as has_acted=True
   b. Create ActionLog entry
   c. Get next step from transition
   d. Assign next step to role (round-robin)
   e. Create new StepInstance
5. If no transition (end of workflow):
   a. Mark task as completed
   b. Update ticket status
6. Send notification to newly assigned user
```

**Implementation**:
```python
# workflow_api/task/services.py
def process_workflow_action(task, user, action_id, comment):
    """
    Workflow transition algorithm
    """
    # Step 1-2: Get and validate current step
    current_step_instance = StepInstance.objects.get(
        task=task,
        user_id=user.id,
        has_acted=False
    )
    
    # Step 3: Find transition
    transition = StepTransition.objects.filter(
        from_step=current_step_instance.step,
        action_id=action_id
    ).first()
    
    # Step 4: Process transition
    if transition:
        # 4a: Mark current step as acted
        current_step_instance.has_acted = True
        current_step_instance.save()
        
        # 4b: Log action
        ActionLog.objects.create(
            step_instance=current_step_instance,
            task=task,
            user=user.username,
            action_id=action_id,
            comment=comment
        )
        
        # 4c-e: Move to next step
        next_step = transition.to_step
        assign_task_round_robin(next_step.role_id, task)
        
        return {'status': 'transitioned', 'next_step': next_step.name}
    
    # Step 5: End of workflow
    else:
        task.mark_as_completed()
        task.ticket.status = 'completed'
        task.ticket.save()
        
        return {'status': 'completed'}
```

**Time Complexity**: O(1) for database operations with indexes

**Space Complexity**: O(1)

## Code Structure & Organization

### Backend (Django Services)

**Directory Structure** (per service):
```
service_name/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container definition
├── start.sh                     # Startup script
├── .env.example                 # Environment template
├── service_name/                # Project settings
│   ├── __init__.py
│   ├── settings.py              # Django configuration
│   ├── urls.py                  # URL routing
│   ├── wsgi.py                  # WSGI application
│   └── celery.py                # Celery configuration (if applicable)
├── app_name/                    # Django app (e.g., tickets, workflow)
│   ├── __init__.py
│   ├── models.py                # Database models
│   ├── views.py                 # API views/endpoints
│   ├── serializers.py           # DRF serializers
│   ├── urls.py                  # App-specific URLs
│   ├── tasks.py                 # Celery tasks
│   ├── services.py              # Business logic
│   ├── signals.py               # Django signals
│   ├── permissions.py           # Custom permissions
│   ├── admin.py                 # Django admin configuration
│   ├── tests.py                 # Unit tests
│   └── migrations/              # Database migrations
│       └── 0001_initial.py
└── media/                       # User-uploaded files
```

**Example: ticket_service structure**:
```
ticket_service/
├── manage.py
├── requirements.txt
├── ticket_service/
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
└── tickets/
    ├── models.py          # Ticket model
    ├── views.py           # TicketViewSet
    ├── serializers.py     # TicketSerializer
    ├── urls.py            # /tickets/ routes
    ├── tasks.py           # push_ticket_to_workflow
    └── signals.py         # post_save handler
```

### Frontend (React)

**Directory Structure**:
```
frontend/
├── package.json                 # Dependencies and scripts
├── vite.config.js               # Vite configuration
├── index.html                   # Entry HTML
├── public/                      # Static assets
├── src/
│   ├── main.jsx                 # Application entry point
│   ├── App.jsx                  # Root component
│   ├── index.css                # Global styles
│   ├── api/                     # API integration layer
│   │   ├── axios.jsx            # Axios instance
│   │   ├── useLogin.jsx         # Login hook
│   │   ├── useTicketsFetcher.jsx
│   │   └── useWorkflowAPI.jsx
│   ├── components/              # Reusable components
│   │   ├── common/
│   │   │   ├── Button.jsx
│   │   │   ├── Modal.jsx
│   │   │   └── Table.jsx
│   │   └── ticket/
│   │       ├── TicketForm.jsx
│   │       ├── TicketList.jsx
│   │       └── TicketDetail.jsx
│   ├── pages/                   # Page components
│   │   ├── agent/
│   │   │   ├── Dashboard.jsx
│   │   │   └── TicketPage.jsx
│   │   └── admin/
│   │       ├── AdminDashboard.jsx
│   │       └── WorkflowManager.jsx
│   ├── routes/                  # Routing configuration
│   │   └── AppRoutes.jsx
│   ├── context/                 # React Context providers
│   │   ├── AuthContext.jsx
│   │   └── TicketsContext.jsx
│   ├── hooks/                   # Custom React hooks
│   │   ├── useAuth.jsx
│   │   └── useTickets.jsx
│   ├── utils/                   # Utility functions
│   │   ├── formatters.js
│   │   └── validators.js
│   └── types/                   # TypeScript types (if using TS)
│       └── ticket.types.js
└── .env                         # Environment variables
```

### Shared Files

**Root Directory**:
```
Ticket-Tracking-System/
├── Docker/                      # Docker configuration
│   ├── docker-compose.yml       # Multi-container setup
│   └── db-init/                 # Database init scripts
├── Scripts/                     # Automation scripts
│   ├── docker.sh                # Docker startup
│   └── init.sh                  # Initialize services
├── architecture/                # Architecture diagrams
│   ├── component_diagram.puml
│   ├── sequence_ticket_creation.puml
│   └── class_diagram_backend.puml
├── docs/                        # Documentation
│   ├── A1_SYSTEM_ARCHITECTURE.md
│   ├── A2_INFORMATION_SYSTEMS_INTEGRATION.md
│   └── A3_APPLICATION_DESIGN_AND_DEVELOPMENT.md
├── .gitignore                   # Git ignore rules
├── ReadMe.md                    # Main README
├── ENVIRONMENT_STANDARDIZATION_REPORT.md
└── requirements.txt             # Shared Python dependencies
```

## Critical Code Snippets

### 1. JWT Authentication Middleware

```python
# auth/middleware.py
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

class JWTAuthenticationMiddleware:
    """
    Middleware to extract user from JWT token
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        token = self.get_token_from_request(request)
        
        if token:
            try:
                access_token = AccessToken(token)
                user_id = access_token['user_id']
                request.user = User.objects.get(id=user_id)
            except Exception:
                request.user = AnonymousUser()
        else:
            request.user = AnonymousUser()
        
        response = self.get_response(request)
        return response
    
    def get_token_from_request(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None
```

### 2. Celery Task with Retry Logic

```python
# workflow_api/tickets/tasks.py
from celery import shared_task
from celery.exceptions import Retry

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def push_ticket_to_workflow(self, ticket_data):
    """
    Process ticket with automatic retry on failure
    """
    try:
        # Create workflow ticket
        workflow_ticket = WorkflowTicket.objects.create(**ticket_data)
        
        # Match and assign workflow
        task = match_and_assign_workflow(workflow_ticket)
        
        if not task:
            raise Exception("No workflow matched")
        
        return {'status': 'success', 'task_id': str(task.task_id)}
        
    except Exception as exc:
        # Exponential backoff: 60s, 120s, 240s
        retry_countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=retry_countdown)
```

### 3. Custom Permission Class

```python
# auth/permissions.py
from rest_framework.permissions import BasePermission

class IsSystemAdminOrSuperUser(BasePermission):
    """
    Custom permission: Only system admins or superusers
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Check if user has Admin role in any system
        return UserSystemRole.objects.filter(
            user=request.user,
            role__name='Admin'
        ).exists()
    
    def has_object_permission(self, request, view, obj):
        # Object-level permission check
        if request.user.is_superuser:
            return True
        
        # Allow if user is admin in the object's system
        if hasattr(obj, 'system'):
            return UserSystemRole.objects.filter(
                user=request.user,
                system=obj.system,
                role__name='Admin'
            ).exists()
        
        return False
```

### 4. Django Signal for Ticket Processing

```python
# ticket_service/tickets/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Ticket
from .tasks import push_ticket_to_workflow
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Ticket)
def trigger_workflow_on_ticket_creation(sender, instance, created, **kwargs):
    """
    Signal: Automatically trigger workflow when ticket created
    """
    if created:
        logger.info(f"New ticket created: {instance.ticket_id}")
        
        # Serialize ticket data
        ticket_data = {
            'ticket_id': instance.ticket_id,
            'subject': instance.subject,
            'category': instance.category,
            'subcategory': instance.subcategory,
            'department': instance.department,
            'priority': instance.priority,
            'description': instance.description,
            'employee': instance.employee,
            'attachments': instance.attachments
        }
        
        # Enqueue async task
        push_ticket_to_workflow.delay(ticket_data)
        logger.info(f"Ticket {instance.ticket_id} queued for workflow processing")

@receiver(pre_delete, sender=Ticket)
def log_ticket_deletion(sender, instance, **kwargs):
    """
    Signal: Log when ticket is deleted
    """
    logger.warning(f"Ticket {instance.ticket_id} is being deleted")
```

### 5. React Custom Hook for API Integration

```javascript
// frontend/src/api/useTicketsFetcher.jsx
import { useState, useEffect } from 'react';
import axios from './axios';

export const useTicketsFetcher = (filters = {}) => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const fetchTickets = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('access_token');
      
      const response = await axios.get('/tickets/', {
        params: filters,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      setTickets(response.data.results || response.data);
    } catch (err) {
      setError(err.message);
      console.error('Failed to fetch tickets:', err);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchTickets();
  }, [JSON.stringify(filters)]);
  
  return { tickets, loading, error, refetch: fetchTickets };
};

// Usage in component:
// const { tickets, loading, error } = useTicketsFetcher({ status: 'open' });
```

### 6. Workflow Matching Service Function

```python
# workflow_api/workflow/services.py
from .models import Workflows, Steps, Task, StepInstance
from role.services import assign_task_round_robin

def match_and_assign_workflow(workflow_ticket):
    """
    Core business logic: Match ticket to workflow and assign
    """
    # 1. Find matching workflow
    workflow = Workflows.objects.filter(
        category=workflow_ticket.category,
        subcategory=workflow_ticket.subcategory,
        department=workflow_ticket.department,
        priority=workflow_ticket.priority,
        is_published=True
    ).first()
    
    if not workflow:
        # Fallback: Match by category and department only
        workflow = Workflows.objects.filter(
            category=workflow_ticket.category,
            department=workflow_ticket.department,
            is_published=True
        ).first()
    
    if not workflow:
        logger.warning(f"No workflow found for ticket {workflow_ticket.ticket_id}")
        return None
    
    # 2. Get initial step (order=1)
    initial_step = Steps.objects.filter(
        workflow=workflow,
        order=1
    ).first()
    
    if not initial_step:
        logger.error(f"Workflow {workflow.workflow_id} has no initial step")
        return None
    
    # 3. Create task
    task = Task.objects.create(
        ticket=workflow_ticket,
        workflow=workflow
    )
    
    # 4. Assign to role using round-robin
    assigned_user = assign_task_round_robin(initial_step.role_id, task)
    
    # 5. Mark ticket as allocated
    workflow_ticket.is_task_allocated = True
    workflow_ticket.assigned_to = assigned_user['email']
    workflow_ticket.save()
    
    logger.info(f"Task {task.task_id} assigned to {assigned_user['email']}")
    
    return task
```

## Major Libraries and Frameworks

### Backend Libraries

| Library | Version | Purpose | Used In |
|---------|---------|---------|---------|
| Django | 5.x | Web framework | All services |
| djangorestframework | 3.x | REST API framework | All services |
| djangorestframework-simplejwt | 5.x | JWT authentication | Auth service |
| Celery | 5.x | Task queue | ticket_service, workflow_api, notification_service |
| psycopg2-binary | 2.9.x | PostgreSQL adapter | All services |
| python-decouple | 3.x | Environment config | All services |
| dj-database-url | 2.x | Database URL parser | All services |
| django-cors-headers | 4.x | CORS handling | All services |
| drf-spectacular | 0.26.x | API documentation | Auth, workflow_api |
| django-ratelimit | 4.x | Rate limiting | Auth service |
| django-simple-captcha | 0.6.x | CAPTCHA | Auth service |
| gunicorn | 21.x | WSGI server | Production deployment |
| redis | 4.x | Caching (optional) | Future enhancement |

### Frontend Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| react | 18.2.0 | UI framework |
| react-dom | 18.2.0 | React DOM rendering |
| vite | 7.1.3 | Build tool |
| react-router-dom | 7.6.2 | Routing |
| axios | 1.11.0 | HTTP client |
| reactflow | 11.11.4 | Workflow diagrams |
| chart.js | 4.5.0 | Charts |
| react-chartjs-2 | 5.3.0 | React Chart.js wrapper |
| lucide-react | 0.523.0 | Icons |
| dayjs | 1.11.18 | Date formatting |
| dompurify | 3.3.0 | XSS sanitization |
| uuid | 11.1.0 | UUID generation |

## Development Best Practices

### Code Style & Standards

**Python (PEP 8)**:
- 4 spaces for indentation
- Max line length: 79 characters (docstrings/comments), 120 (code)
- Naming: `snake_case` for functions/variables, `PascalCase` for classes
- Docstrings: Google or NumPy style

**JavaScript (ESLint)**:
- 2 spaces for indentation
- Semicolons optional (consistent usage)
- Arrow functions for anonymous functions
- Destructuring for object/array access

### Testing Strategy

**Backend Tests** (pytest):
```python
# ticket_service/tickets/tests.py
import pytest
from django.test import TestCase
from .models import Ticket

class TicketModelTest(TestCase):
    def setUp(self):
        self.ticket = Ticket.objects.create(
            ticket_id="TEST-001",
            subject="Test ticket",
            category="Support",
            priority="high"
        )
    
    def test_ticket_creation(self):
        self.assertEqual(self.ticket.ticket_id, "TEST-001")
        self.assertEqual(self.ticket.priority, "high")
    
    def test_ticket_string_representation(self):
        self.assertEqual(str(self.ticket), "TEST-001: Test ticket")
```

**Frontend Tests** (React Testing Library):
```javascript
// frontend/src/components/TicketForm.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import TicketForm from './TicketForm';

describe('TicketForm', () => {
  test('renders form fields', () => {
    render(<TicketForm />);
    expect(screen.getByLabelText(/subject/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
  });
  
  test('submits form with valid data', async () => {
    const onSubmit = jest.fn();
    render(<TicketForm onSubmit={onSubmit} />);
    
    fireEvent.change(screen.getByLabelText(/subject/i), {
      target: { value: 'Test ticket' }
    });
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ subject: 'Test ticket' })
    );
  });
});
```

### Database Migrations

**Creating Migrations**:
```bash
# After model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Rollback migration
python manage.py migrate app_name 0001_previous_migration
```

**Example Migration**:
```python
# tickets/migrations/0002_add_priority_field.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('tickets', '0001_initial'),
    ]
    
    operations = [
        migrations.AddField(
            model_name='ticket',
            name='priority',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('low', 'Low'),
                    ('medium', 'Medium'),
                    ('high', 'High'),
                    ('urgent', 'Urgent')
                ],
                default='medium'
            ),
        ),
    ]
```

## References

- **System Architecture**: `/docs/A1_SYSTEM_ARCHITECTURE.md`
- **Integration Details**: `/docs/A2_INFORMATION_SYSTEMS_INTEGRATION.md`
- **Django Documentation**: https://docs.djangoproject.com/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **React Documentation**: https://react.dev/
- **Celery Documentation**: https://docs.celeryq.dev/

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Authors**: Development Team
