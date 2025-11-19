# A.3 Application Design and Development Documentation

## Table of Contents
1. [Development Overview](#development-overview)
2. [Software Design Patterns](#software-design-patterns)
3. [Backend Architecture](#backend-architecture)
4. [Key Algorithms](#key-algorithms)
5. [Code Structure](#code-structure)
6. [Libraries and Frameworks](#libraries-and-frameworks)

---

## Development Overview

### Development Principles

The Ticket Tracking System follows modern software development practices:

- **Clean Code**: Readable, maintainable, self-documenting code
- **DRY (Don't Repeat Yourself)**: Reusable components and utilities
- **SOLID Principles**: Object-oriented design principles
- **Separation of Concerns**: Clear boundaries between layers
- **API-First Design**: Well-defined interfaces between services
- **Test-Driven Development**: Comprehensive testing

### Architecture Patterns

1. **Microservices Architecture**: Independent, deployable services
2. **RESTful API Design**: Resource-based URL structure
3. **Event-Driven Architecture**: Asynchronous message processing
4. **MVC Pattern**: Model-View-Controller separation (Django)
5. **Repository Pattern**: Data access abstraction
6. **Service Layer Pattern**: Business logic encapsulation

---

## Software Design Patterns

### 1. Repository Pattern

**Purpose**: Abstract data access logic from business logic

**Implementation**: Django ORM Models act as repositories

**Example - Workflow Repository**:
```python
# workflow/models.py
class Workflows(models.Model):
    user_id = models.IntegerField(null=False)
    name = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="draft")
    
    @classmethod
    def get_deployed_workflows(cls):
        return cls.objects.filter(status='deployed')
    
    @classmethod
    def find_by_category(cls, category, sub_category):
        return cls.objects.filter(
            category=category,
            sub_category=sub_category,
            status='deployed'
        ).first()
    
    def deploy(self):
        self.status = 'deployed'
        self.is_published = True
        self.save()
```

---

### 2. Service Layer Pattern

**Purpose**: Encapsulate business logic separate from views

**Example - Notification Service**:
```python
# notifications/services.py
class NotificationService:
    @staticmethod
    def process_notification_request(notification_data):
        # Validate data
        # Get template
        # Render message
        # Send notification
        # Log result
        return success_status
```

---

### 3. Serializer Pattern

**Purpose**: Data validation and transformation between layers

**Example - Workflow Serializer**:
```python
# workflow/serializers.py
class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflows
        fields = ['workflow_id', 'name', 'description', ...]
    
    def validate(self, data):
        # Validate SLA ordering
        # urgent < high < medium < low
        return data
```

---

### 4. Observer Pattern (Event-Driven)

**Purpose**: Notify multiple subscribers of state changes

**Example - Comment Notification via WebSocket**:
```python
# messaging/comments/views.py
def perform_create(self, serializer):
    comment = serializer.save()
    
    # Notify all WebSocket subscribers
    channel_layer.group_send(
        f'comments_{comment.ticket_id}',
        {'type': 'comment_create', 'message': comment_data}
    )
```

---

### 5. Strategy Pattern

**Purpose**: Define family of algorithms, make them interchangeable

**Example - Task Assignment Strategies**:
```python
# workflow/assignment_strategies.py
class AssignmentStrategy(ABC):
    @abstractmethod
    def assign(self, task, role):
        pass

class RoundRobinStrategy(AssignmentStrategy):
    def assign(self, task, role):
        # Get users, order by last_assigned_at
        # Select first user (least recently assigned)
        return selected_user

class LoadBalancingStrategy(AssignmentStrategy):
    def assign(self, task, role):
        # Get users, order by active task count
        # Select user with least active tasks
        return selected_user
```

---

## Backend Architecture

### Django Application Structure

```
service_name/
├── service_name/          # Project settings
│   ├── settings.py        # Django configuration
│   ├── urls.py            # URL routing
│   ├── wsgi.py            # WSGI entry point
│   └── asgi.py            # ASGI entry point
├── app1/                  # Django app
│   ├── models.py          # Data models (Repository)
│   ├── views.py           # API views (Controller)
│   ├── serializers.py     # Data serializers
│   ├── urls.py            # App URLs
│   ├── services.py        # Business logic
│   ├── tasks.py           # Celery tasks
│   └── migrations/        # Database migrations
├── manage.py
├── requirements.txt
└── Dockerfile
```

---

### Layer Responsibilities

**Model Layer**: Database schema, ORM queries, model-level validation  
**Serializer Layer**: Request validation, response formatting, data type conversion  
**View Layer**: HTTP request handling, authentication, input validation  
**Service Layer**: Complex business rules, cross-model operations, external service calls  
**Task Layer**: Background jobs, scheduled tasks, long-running operations

---

### Django REST Framework Views

**ViewSet Pattern**:
```python
# workflow/views.py
class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflows.objects.all()
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def deploy(self, request, pk=None):
        workflow = self.get_object()
        workflow.deploy()
        return Response({'message': 'Deployed successfully'})
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        category = request.query_params.get('category')
        workflows = Workflows.objects.filter(category=category)
        return Response(self.get_serializer(workflows, many=True).data)
```

---

### Celery Task Patterns

**Shared Task Pattern**:
```python
# workflow/tasks.py
@shared_task(name="workflow.process_ticket", bind=True, max_retries=3)
def process_ticket(self, ticket_data):
    try:
        workflow = find_matching_workflow(ticket_data)
        task = create_task_from_ticket(workflow, ticket_data)
        assign_first_step(task, workflow)
        notify_assignment(task)
        return {'status': 'success', 'task_id': task.id}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

---

## Key Algorithms

### 1. Round-Robin Task Assignment

**Purpose**: Fairly distribute tasks among users in a role

**Algorithm**:
```python
def round_robin_assignment(role):
    """
    Time Complexity: O(n) where n = users in role
    Space Complexity: O(1)
    """
    users = UserRoleAssignment.objects.filter(
        role=role, active=True
    ).order_by('last_assigned_at')
    
    selected_user = users.first()
    selected_user.last_assigned_at = timezone.now()
    selected_user.save()
    
    return selected_user
```

**Pseudocode**:
```
ALGORITHM RoundRobinAssignment(role)
1. users ← GET_USERS_IN_ROLE(role) ORDER BY last_assigned_at ASC
2. IF users IS EMPTY THEN RAISE Error
3. selected_user ← users[0]
4. selected_user.last_assigned_at ← CURRENT_TIMESTAMP
5. SAVE(selected_user)
6. RETURN selected_user
```

---

### 2. SLA Calculation

**Purpose**: Calculate deadline based on workflow SLA and priority

**Algorithm**:
```python
def calculate_sla_deadline(workflow, priority):
    sla_map = {
        'urgent': workflow.urgent_sla,
        'high': workflow.high_sla,
        'medium': workflow.medium_sla,
        'low': workflow.low_sla,
    }
    
    sla_duration = sla_map.get(priority, timedelta(hours=24))
    deadline = timezone.now() + sla_duration
    return deadline
```

---

### 3. Workflow Matching Algorithm

**Purpose**: Find appropriate workflow for incoming ticket

**Flowchart**:
```
START
  ├─→ [Get ticket category, sub_category, department]
  ├─→ [Query: category + sub_category + department]
  ├─→ Found? YES → Return workflow → END
  │          NO  ↓
  ├─→ [Query: category + sub_category only]
  ├─→ Found? YES → Return workflow → END
  │          NO  ↓
  └─→ [Raise WorkflowNotFoundError] → END
```

---

### 4. Workflow State Machine

**State Diagram**:
```
       ┌──────────┐
  ┌────│  PENDING │
  │    └────┬─────┘
  │         │ assign()
  │         ▼
  │    ┌────────────┐
  │    │IN_PROGRESS │◄────┐
  │    └────┬───────┘     │ reopen()
  │         │ complete()  │
  │         ▼             │
  │    ┌──────────┐       │
  │    │COMPLETED │───────┘
  │    └────┬─────┘
  │         │ approve()
  │         ▼
  │    ┌─────────┐
  └───►│ CLOSED  │
       └─────────┘
```

**Implementation**:
```python
class TaskStateMachine:
    STATES = {
        'pending': ['in_progress'],
        'in_progress': ['completed', 'pending'],
        'completed': ['closed', 'in_progress'],
        'closed': []
    }
    
    @classmethod
    def can_transition(cls, from_state, to_state):
        return to_state in cls.STATES.get(from_state, [])
    
    @classmethod
    def transition(cls, task, to_state):
        if not cls.can_transition(task.status, to_state):
            raise InvalidTransitionError()
        
        task.status = to_state
        # Update timestamps
        task.save()
        # Log transition
        return task
```

---

## Code Structure

### File Organization Best Practices

1. **Single Responsibility**: Each file has one clear purpose
2. **Naming Conventions**:
   - Models: `models.py` - Singular names
   - Views: `views.py` - Descriptive ViewSet names
   - Serializers: `serializers.py` - Match model names
3. **Import Order**:
   - Standard library
   - Third-party
   - Django
   - Local application

**Example**:
```python
# Standard library
import logging
from datetime import timedelta

# Third-party
from celery import shared_task

# Django
from django.conf import settings
from django.utils import timezone

# Local
from .models import Workflow, Task
from .serializers import WorkflowSerializer
```

---

### Code Documentation Standards

**Docstring Format** (Google Style):
```python
def process_workflow_step(task, step):
    """
    Process a single workflow step.
    
    Args:
        task (Task): The task instance
        step (Step): The step to execute
    
    Returns:
        dict: Processing result
    
    Raises:
        ValidationError: If task data is invalid
        NoAvailableUsersError: If no users available
    
    Example:
        >>> result = process_workflow_step(task, step)
        >>> print(result['status'])
        'success'
    """
    pass
```

---

## Libraries and Frameworks

### Backend Libraries (Python)

| Library | Version | Purpose |
|---------|---------|---------|
| Django | 5.2.1 | Web framework |
| djangorestframework | 3.16.0 | REST API |
| djangorestframework-simplejwt | 5.5.0 | JWT authentication |
| Celery | 5.5.3 | Task queue |
| channels | Latest | WebSocket support |
| psycopg2-binary | 2.9+ | PostgreSQL adapter |
| python-decouple | Latest | Configuration |
| dj-database-url | Latest | Database URL parsing |
| django-cors-headers | 4.7.0 | CORS support |
| drf-spectacular | 0.28.0 | API documentation |
| gunicorn | 20.1.0 | WSGI server |
| whitenoise | Latest | Static file serving |
| Pillow | 11.2.1 | Image processing |
| requests | 2.32.4 | HTTP client |
| PyJWT | 2.9.0 | JWT library |

---

### Frontend Libraries (JavaScript)

| Library | Version | Purpose |
|---------|---------|---------|
| React | 18.x | UI library |
| Vite | Latest | Build tool |
| React Router | 6.x | Routing |
| Axios | Latest | HTTP client |
| TailwindCSS | 3.x | CSS framework |

---

### Infrastructure

| Component | Version | Purpose |
|-----------|---------|---------|
| RabbitMQ | 3-management | Message broker |
| PostgreSQL | 15 | Database |
| Docker | Latest | Containerization |
| NGINX | Latest | Reverse proxy |

---

## Critical Code Implementations

### 1. Ticket Processing Pipeline

**File**: `workflow_api/tickets/tasks.py`

```python
@shared_task(name="tickets.tasks.receive_ticket", bind=True, max_retries=3)
def receive_ticket(self, ticket_data):
    """Critical: Main entry point for ticket processing"""
    try:
        # Validate ticket data
        # Find matching workflow
        # Create task instance
        # Initialize workflow
        # Assign to first step
        # Notify assigned user
        return {'status': 'success', 'task_id': task.id}
    except WorkflowNotFoundError:
        notify_admin_no_workflow(ticket_data)
        return {'status': 'no_workflow'}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

---

### 2. WebSocket Comment Broadcasting

**File**: `messaging/comments/consumers.py`

```python
class CommentConsumer(AsyncWebsocketConsumer):
    """Critical: Real-time comment distribution"""
    
    async def connect(self):
        self.ticket_id = self.scope['url_route']['kwargs']['ticket_id']
        self.room_group_name = f'comments_{self.ticket_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def comment_create(self, event):
        """Broadcast comment creation to all clients"""
        await self.send(text_data=json.dumps({
            'type': 'comment_update',
            'action': 'create',
            'comment': event['message']
        }))
```

---

### 3. JWT Authentication

**File**: `auth/authentication.py`

```python
class JWTAuthentication(BaseAuthentication):
    """Custom JWT authentication"""
    
    def authenticate(self, request):
        token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            return (user, token)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise AuthenticationFailed('Invalid token')
```

---

## Development Workflow

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/Gknightt/Ticket-Tracking-System.git

# Setup environment
cd auth && cp .env.example .env

# Start services
cd Docker && docker-compose up -d

# Run migrations
docker exec -it auth-service python manage.py migrate

# Seed data
docker exec -it auth-service python manage.py seed_accounts
```

---

### Development Best Practices

1. **Code Style**: Follow PEP 8 for Python, ESLint for JavaScript
2. **Git Workflow**: Feature branches, conventional commits
3. **Code Review**: Required before merge
4. **Documentation**: Update docstrings and API docs

---

## Testing Strategy

### Test Pyramid

```
         ┌─────────────┐
         │  E2E Tests  │  (Few)
         └─────────────┘
       ┌─────────────────┐
       │ Integration Tests│  (Some)
       └─────────────────┘
     ┌───────────────────────┐
     │    Unit Tests         │  (Many)
     └───────────────────────┘
```

---

### Unit Testing Example

```python
# workflow/tests.py
class WorkflowModelTest(TestCase):
    def test_workflow_deploy(self):
        workflow = Workflows.objects.create(name="Test")
        workflow.deploy()
        self.assertEqual(workflow.status, "deployed")
```

---

### API Testing Example

```python
# workflow/tests_api.py
class WorkflowAPITest(APITestCase):
    def test_create_workflow(self):
        data = {'name': 'Test Workflow', 'category': 'IT'}
        response = self.client.post('/workflows/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Maintained By**: Development Team
