# A.2 Information Systems Integration

## Overview

This document describes how different software systems, services, and components are integrated to work as a unified Ticket Tracking System. It covers integration architecture, data flow, API contracts, and data transformation between services.

## Integration Architecture

### Integration Pattern

The system uses a **Hybrid Integration Pattern** combining:

1. **Synchronous Integration** (REST HTTP/JSON)
   - Service-to-service HTTP API calls
   - Frontend-to-backend communication
   - Request-response pattern for immediate data needs

2. **Asynchronous Integration** (Message Queue/Event-Driven)
   - RabbitMQ message broker with Celery task queue
   - Decoupled service communication
   - Background job processing
   - Event-driven notifications

### Integration Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (React)                            │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │  Auth  │  │Tickets │  │Workflow│  │Messages│  │ Notif. │   │
│  │  API   │  │  API   │  │  API   │  │  API   │  │  API   │   │
│  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘   │
└──────┼───────────┼───────────┼───────────┼───────────┼─────────┘
       │           │           │           │           │
       │ JWT Token │           │           │           │
       │  in Auth  │           │           │           │
       │  Header   │           │           │           │
       ▼           ▼           ▼           ▼           ▼
┌──────────────────────────────────────────────────────────────────┐
│                   API Gateway Layer (implicit)                    │
│     Each Django service exposes REST endpoints independently      │
└──────────────────────────────────────────────────────────────────┘
       ▼           ▼           ▼           ▼           ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│   Auth   │◄─┤  Ticket  │◄─┤ Workflow │  │Messaging │  │  Notif.  │
│ Service  │  │ Service  │  │   API    │  │ Service  │  │ Service  │
│  :8000   │  │  :8004   │  │  :8002   │  │  :8005   │  │  :8006   │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┘  └────┬─────┘
     │             │              │                            │
     │             │              │      ┌─────────────────────┤
     │             │              │      │                     │
     ▼             ▼              ▼      ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                       RabbitMQ Message Broker                     │
│  Queues: TICKET_TASKS_PRODUCTION, notification-queue-default,    │
│          inapp-notification-queue, ticket_status-default, ...     │
└──────────────────────────────────────────────────────────────────┘
                          ▼                    ▼
                 ┌─────────────────┐   ┌─────────────────┐
                 │ Workflow Worker │   │ Notif. Worker   │
                 │  (Celery)       │   │  (Celery)       │
                 └─────────────────┘   └─────────────────┘
```

## Integration Points

### 1. Frontend ↔ Backend Services (Synchronous HTTP)

**Protocol**: HTTP/1.1 REST with JSON payloads

**Authentication**: JWT Bearer token in `Authorization` header

**Integration Points**:

| Frontend Component | Backend Service | Endpoint Examples | Purpose |
|-------------------|-----------------|-------------------|---------|
| Login Component | Auth Service | `POST /api/v1/users/token/` | Obtain JWT tokens |
| User Profile | Auth Service | `GET /api/v1/users/profile/` | Fetch user details |
| Ticket Dashboard | Ticket Service | `GET /tickets/` | List tickets |
| Ticket Form | Ticket Service | `POST /tickets/` | Create ticket |
| Workflow Manager | Workflow API | `GET /workflows/` | List workflows |
| Task List | Workflow API | `GET /tasks/` | List user tasks |
| Task Actions | Workflow API | `POST /tasks/{id}/action/` | Perform action |
| Notifications | Notification Service | `GET /notifications/` | Fetch notifications |
| Comments | Messaging Service | `GET/POST /comments/` | Ticket comments |

**Request Flow Example - Ticket Creation**:

```javascript
// Frontend (React)
const createTicket = async (ticketData) => {
  const token = localStorage.getItem('access_token');
  
  const response = await axios.post(
    'http://ticket-service:8004/tickets/',
    ticketData,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  return response.data;
};
```

**Response Format (Standard)**:
```json
{
  "id": 123,
  "ticket_id": "TKT-2025-001",
  "subject": "Login issue",
  "status": "open",
  "created_at": "2025-11-19T10:00:00Z",
  "assigned_to": "user@example.com"
}
```

**Error Response Format**:
```json
{
  "error": "Validation failed",
  "details": {
    "subject": ["This field is required"],
    "category": ["Invalid category"]
  }
}
```

### 2. Workflow API ↔ Auth Service (Synchronous HTTP)

**Purpose**: User and role lookups for task assignment

**Integration Pattern**: Direct REST API calls

**Key Integration Points**:

| Use Case | Auth Service Endpoint | Workflow API Caller | Data Flow |
|----------|----------------------|---------------------|-----------|
| Round-robin assignment | `GET /api/v1/tts/roles/{role_id}/users/` | `role/tasks.py` | Workflow fetches users by role |
| User validation | `GET /api/v1/users/{user_id}/` | Multiple views | Validate user exists |
| System role check | `GET /api/v1/tts/systems/{system}/users/` | Authorization middleware | Check system access |

**Example Integration Code**:

```python
# workflow_api/role/tasks.py
import requests
from django.conf import settings

def get_users_by_role(role_id):
    """
    Fetch users from Auth Service by role ID
    """
    auth_service_url = settings.DJANGO_AUTH_SERVICE  # http://auth-service:8000
    url = f"{auth_service_url}/api/v1/tts/roles/{role_id}/users/"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()  # Returns list of user objects
    else:
        raise Exception(f"Failed to fetch users: {response.status_code}")
```

**Data Transformation**:

Auth Service Response:
```json
{
  "users": [
    {
      "id": 5,
      "username": "agent1",
      "email": "agent1@example.com",
      "role": {
        "role_id": "uuid-role-123",
        "name": "L1 Support"
      }
    }
  ]
}
```

Workflow API Internal Representation:
```python
# Extracted and used for assignment
assigned_user_id = users[pointer_index]['id']  # 5
assigned_user_email = users[pointer_index]['email']  # "agent1@example.com"
```

### 3. Ticket Service → Workflow API (Asynchronous Message Queue)

**Purpose**: Trigger workflow processing when ticket created

**Integration Pattern**: Event-driven via RabbitMQ

**Message Flow**:

```
Ticket Service (Django Signal) 
  → Celery Task (push_ticket_to_workflow) 
  → RabbitMQ (TICKET_TASKS_PRODUCTION queue)
  → Workflow Worker (Celery Consumer)
  → Workflow API (process_ticket function)
```

**Implementation Details**:

**Ticket Service - Signal Handler** (`ticket_service/tickets/signals.py`):
```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ticket
from .tasks import push_ticket_to_workflow

@receiver(post_save, sender=Ticket)
def trigger_workflow_on_ticket_creation(sender, instance, created, **kwargs):
    """
    After ticket is saved, push to workflow service asynchronously
    """
    if created:
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
```

**Ticket Service - Celery Task** (`ticket_service/tickets/tasks.py`):
```python
from celery import shared_task

@shared_task(name='tickets.tasks.push_ticket_to_workflow')
def push_ticket_to_workflow(ticket_data):
    """
    Publish ticket data to workflow service via message queue
    """
    # This task is consumed by workflow-worker
    # The actual processing happens in workflow_api
    return ticket_data
```

**Workflow API - Task Consumer** (`workflow_api/tickets/tasks.py`):
```python
from celery import shared_task
from .models import WorkflowTicket
from workflow.services import match_and_assign_workflow

@shared_task(name='tickets.tasks.push_ticket_to_workflow', bind=True)
def process_ticket(self, ticket_data):
    """
    Process incoming ticket and assign to workflow
    """
    # Create WorkflowTicket mirror
    workflow_ticket = WorkflowTicket.objects.create(**ticket_data)
    
    # Match workflow and assign
    match_and_assign_workflow(workflow_ticket)
    
    return {'status': 'processed', 'ticket_id': ticket_data['ticket_id']}
```

**Message Format** (JSON over AMQP):
```json
{
  "task": "tickets.tasks.push_ticket_to_workflow",
  "args": [],
  "kwargs": {
    "ticket_data": {
      "ticket_id": "TKT-2025-001",
      "subject": "Login issue",
      "category": "Technical Support",
      "subcategory": "Authentication",
      "department": "IT",
      "priority": "high",
      "description": "Cannot login to the system",
      "employee": {
        "id": 123,
        "name": "John Doe",
        "email": "john@example.com"
      },
      "attachments": []
    }
  }
}
```

### 4. Workflow API → Notification Service (Asynchronous)

**Purpose**: Send notifications for task assignments, status changes

**Integration Pattern**: Celery task via message queue

**Message Flow**:

```
Workflow API (assignment logic)
  → Celery Task (create_assignment_notification)
  → RabbitMQ (notification-queue-default)
  → Notification Worker
  → Notification Service (send email/in-app notification)
```

**Implementation**:

**Workflow API - Enqueue Notification** (`workflow_api/workflow/services.py`):
```python
from celery import current_app as celery_app

def assign_task_to_user(task, user_id, user_email):
    """
    Assign task to user and send notification
    """
    # Create StepInstance
    step_instance = StepInstance.objects.create(
        task=task,
        user_id=user_id,
        step_transition=current_transition
    )
    
    # Enqueue notification task
    celery_app.send_task(
        'notifications.tasks.create_assignment_notification',
        kwargs={
            'user_id': user_id,
            'user_email': user_email,
            'task_id': str(task.task_id),
            'ticket_subject': task.ticket.subject
        },
        queue='notification-queue-default'
    )
```

**Notification Service - Task Handler** (`notification_service/app/tasks.py`):
```python
from celery import shared_task
from django.core.mail import send_mail

@shared_task(name='notifications.tasks.create_assignment_notification')
def create_assignment_notification(user_id, user_email, task_id, ticket_subject):
    """
    Send assignment notification to user
    """
    # Send email
    send_mail(
        subject=f'New Task Assigned: {ticket_subject}',
        message=f'You have been assigned task {task_id}',
        from_email='noreply@ticketsystem.com',
        recipient_list=[user_email]
    )
    
    # Create in-app notification (call to auth service if needed)
    # ...
    
    return {'status': 'sent', 'user_email': user_email}
```

### 5. Services ↔ PostgreSQL (Data Layer)

**Integration Pattern**: Django ORM with logical database separation

**Database Mapping**:

| Service | Database Name | Connection String |
|---------|--------------|-------------------|
| Auth Service | `authservice` | `postgres://postgres:pass@db:5432/authservice` |
| Ticket Service | `ticketmanagement` | `postgres://postgres:pass@db:5432/ticketmanagement` |
| Workflow API | `workflowmanagement` | `postgres://postgres:pass@db:5432/workflowmanagement` |
| Messaging Service | `messagingservice` | `postgres://postgres:pass@db:5432/messagingservice` |
| Notification Service | `notificationservice` | `postgres://postgres:pass@db:5432/notificationservice` |

**Data Isolation**:
- Each service has its own logical database
- No direct cross-database queries
- Integration via APIs or message queues only

**Connection Configuration** (Django settings):
```python
import dj_database_url
from decouple import config

# Priority 1: Use DATABASE_URL (Railway, managed services)
if config('DATABASE_URL', default=''):
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
# Priority 2: Production PostgreSQL with individual vars
elif config('DJANGO_ENV', default='development') == 'production':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('POSTGRES_DB', default='servicedb'),
            'USER': config('POSTGRES_USER', default='postgres'),
            'PASSWORD': config('POSTGRES_PASSWORD', default=''),
            'HOST': config('PGHOST', default='localhost'),
            'PORT': config('PGPORT', default='5432'),
        }
    }
# Fallback: Development SQLite
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

## Data Flow Diagrams

### Data Flow 1: Complete Ticket Lifecycle

```
┌──────────┐      1. Create Ticket (POST /tickets/)
│ Frontend │──────────────────────────────────────────────────┐
└──────────┘                                                   │
                                                               ▼
                                                   ┌───────────────────┐
                                                   │  Ticket Service   │
                                                   │  - Save to DB     │
                                                   │  - Trigger signal │
                                                   └────────┬──────────┘
                                                            │
                                        2. Enqueue Celery Task
                                                            │
                                                            ▼
                                                   ┌────────────────┐
                                                   │   RabbitMQ     │
                                                   │  (Queue:       │
                                                   │   TICKET_      │
                                                   │   TASKS_PROD)  │
                                                   └────────┬───────┘
                                                            │
                                        3. Worker Consumes Task
                                                            │
                                                            ▼
                                                   ┌────────────────┐
                                                   │ Workflow-Worker│
                                                   │ (Celery)       │
                                                   └────────┬───────┘
                                                            │
                                        4. Process Workflow
                                                            │
                                                            ▼
                                                   ┌────────────────────┐
                                                   │   Workflow API     │
                                                   │ - Match workflow   │
                                                   │ - Assign to role   │
                                                   └────────┬───────────┘
                                                            │
                            5. Query Users by Role          │
                ┌───────────────────────────────────────────┘
                │
                ▼
     ┌─────────────────┐
     │  Auth Service   │
     │ - Return users  │
     │   with role     │
     └─────────┬───────┘
               │
               │ 6. User List
               ▼
     ┌─────────────────────┐
     │   Workflow API      │
     │ - Round-robin pick  │
     │ - Assign user       │
     │ - Create Task       │
     └─────────┬───────────┘
               │
               │ 7. Enqueue Notification
               ▼
     ┌────────────────┐
     │   RabbitMQ     │
     │ (Queue: notif.)│
     └────────┬───────┘
               │
               │ 8. Worker Consumes
               ▼
     ┌──────────────────┐
     │ Notif. Worker    │
     └────────┬─────────┘
               │
               │ 9. Send Notification
               ▼
     ┌──────────────────────┐
     │ Notification Service │
     │ - Send Email         │
     │ - Create In-app      │
     └──────────────────────┘
```

### Data Flow 2: User Authentication & Authorization

```
┌──────────┐
│ Frontend │
└────┬─────┘
     │
     │ 1. Login Request (username, password)
     │    POST /api/v1/users/token/
     ▼
┌─────────────────────┐
│   Auth Service      │
│                     │
│ 1. Rate limit check │
│ 2. Validate creds   │
│ 3. Generate JWT     │
└────┬────────────────┘
     │
     │ 2. JWT Tokens (access, refresh)
     │    { "access": "eyJ...", "refresh": "eyJ..." }
     ▼
┌──────────┐
│ Frontend │
│ - Store  │
│   tokens │
└────┬─────┘
     │
     │ 3. API Request with JWT
     │    Authorization: Bearer eyJ...
     │    GET /tickets/
     ▼
┌─────────────────────┐
│  Ticket Service     │
│                     │
│ 1. Extract JWT      │
│ 2. Validate JWT     │
│    (verify signature│
│     with secret key)│
│ 3. Extract user_id  │
│ 4. Check permissions│
│ 5. Return data      │
└─────────────────────┘
```

## Data Transformation & Mapping

### Ticket Data: Service → Workflow Transformation

**Ticket Service Model** (`ticket_service/tickets/models.py`):
```python
class Ticket(models.Model):
    id = models.AutoField(primary_key=True)
    ticket_id = models.CharField(max_length=50, unique=True)
    original_ticket_id = models.CharField(max_length=50, null=True)
    source_service = models.CharField(max_length=50)
    employee = models.JSONField()
    subject = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    subcategory = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    priority = models.CharField(max_length=20)
    status = models.CharField(max_length=50)
    assigned_to = models.CharField(max_length=255, null=True)
    attachments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Workflow API Model** (`workflow_api/tickets/models.py`):
```python
class WorkflowTicket(models.Model):
    # Same fields as Ticket, PLUS:
    is_task_allocated = models.BooleanField(default=False)
    
    # Additional workflow-specific logic in save() method
```

**Data Mapping**:

| Ticket Service Field | Workflow API Field | Transformation |
|---------------------|-------------------|----------------|
| `ticket_id` | `ticket_id` | Direct copy |
| `subject` | `subject` | Direct copy |
| `category` | `category` | Direct copy (used for workflow matching) |
| `subcategory` | `subcategory` | Direct copy (used for workflow matching) |
| `department` | `department` | Direct copy (used for workflow matching) |
| `priority` | `priority` | Direct copy (used for workflow matching) |
| `employee` (JSON) | `employee` (JSON) | Direct copy |
| `attachments` (JSON) | `attachments` (JSON) | Direct copy |
| N/A | `is_task_allocated` | Set to `False` initially, `True` after assignment |

### User Data: Auth Service → Workflow API

**Auth Service Response**:
```json
{
  "users": [
    {
      "id": 5,
      "username": "agent1",
      "email": "agent1@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "phone_number": "+1234567890",
      "role": {
        "role_id": "uuid-123",
        "name": "L1 Support"
      }
    }
  ]
}
```

**Workflow API Usage**:
```python
# Extract minimal required data
user_id = user_data['id']  # 5
user_email = user_data['email']  # "agent1@example.com"

# Store in StepInstance
step_instance = StepInstance.objects.create(
    user_id=user_id,  # Store just the ID
    task=task,
    step_transition=transition
)

# Use email for notifications
send_notification(user_email, task_details)
```

## API Contracts & Specifications

### Authentication Endpoints (Auth Service)

**Base URL**: `http://auth-service:8000/api/v1/`

| Method | Endpoint | Request Body | Response | Description |
|--------|----------|--------------|----------|-------------|
| POST | `/users/token/` | `{"username": "user", "password": "pass"}` | `{"access": "jwt...", "refresh": "jwt..."}` | Obtain JWT tokens |
| POST | `/users/token/refresh/` | `{"refresh": "jwt..."}` | `{"access": "jwt..."}` | Refresh access token |
| GET | `/users/profile/` | - | User object | Get authenticated user profile |
| GET | `/tts/roles/{role_id}/users/` | - | List of users | Get users by role |

### Ticket Endpoints (Ticket Service)

**Base URL**: `http://ticket-service:8004/`

| Method | Endpoint | Request Body | Response | Description |
|--------|----------|--------------|----------|-------------|
| GET | `/tickets/` | - | Paginated list | List all tickets |
| POST | `/tickets/` | Ticket object | Created ticket | Create new ticket |
| GET | `/tickets/{id}/` | - | Ticket object | Get specific ticket |
| PUT | `/tickets/{id}/` | Ticket object | Updated ticket | Update ticket |
| DELETE | `/tickets/{id}/` | - | 204 No Content | Delete ticket |

**Ticket Object Schema**:
```json
{
  "ticket_id": "TKT-2025-001",
  "subject": "Login issue",
  "description": "Cannot access the system",
  "category": "Technical Support",
  "subcategory": "Authentication",
  "department": "IT",
  "priority": "high",
  "status": "open",
  "employee": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "attachments": [
    {
      "filename": "screenshot.png",
      "url": "/media/attachments/screenshot.png"
    }
  ]
}
```

### Workflow Endpoints (Workflow API)

**Base URL**: `http://workflow-api:8002/`

| Method | Endpoint | Request Body | Response | Description |
|--------|----------|--------------|----------|-------------|
| GET | `/workflows/` | - | List of workflows | List all workflows |
| POST | `/workflows/` | Workflow object | Created workflow | Create workflow |
| GET | `/tasks/` | - | List of tasks | List user tasks |
| POST | `/tasks/{id}/action/` | `{"action_id": "uuid", "comment": "text"}` | Transition result | Perform action |
| GET | `/transitions/` | - | List of transitions | Get available transitions |

## Error Handling & Retry Logic

### HTTP Error Responses

**Standard Error Format**:
```json
{
  "error": "Error type",
  "message": "Human-readable message",
  "details": {
    "field1": ["Validation error"],
    "field2": ["Another error"]
  },
  "code": "ERROR_CODE"
}
```

**HTTP Status Codes**:
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Celery Task Retry Logic

**Configuration** (Django settings):
```python
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # 1 minute
CELERY_TASK_MAX_RETRIES = 3
```

**Example Retry Implementation**:
```python
@shared_task(bind=True, max_retries=3)
def push_ticket_to_workflow(self, ticket_data):
    try:
        # Process ticket
        process_ticket(ticket_data)
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

## Service Discovery & Configuration

### Environment-Based Service URLs

**Auth Service**:
- `DJANGO_AUTH_SERVICE=http://auth-service:8000`
- `DJANGO_USER_SERVICE=http://auth-service:8000`

**Notification Service**:
- `DJANGO_NOTIFICATION_SERVICE_URL=http://notification-service:8001`

**Docker Network DNS**:
- Services resolve each other by container name
- Example: `http://auth-service:8000` resolves to auth service container IP

## Security Integration

### JWT Token Flow

1. **Token Generation** (Auth Service):
   - User authenticates
   - Service generates JWT with secret key
   - Token contains: user_id, username, exp (expiration), role

2. **Token Validation** (All Services):
   - Extract token from `Authorization: Bearer <token>` header
   - Verify signature with shared secret key
   - Extract user information from payload
   - Check expiration

3. **Token Refresh**:
   - Client sends refresh token
   - Auth service generates new access token
   - Client updates stored token

### API Key Authentication (Notification Service)

**Configuration**:
```python
DJANGO_NOTIFICATION_API_KEYS=demo-api-key-123,test-api-key-456
```

**Usage**:
```python
# In request header
headers = {
    'X-API-Key': 'demo-api-key-123'
}
```

## Integration Testing Considerations

### End-to-End Test Flow

1. **Authenticate** (Auth Service)
   - POST `/api/v1/users/token/` → Get JWT

2. **Create Ticket** (Ticket Service)
   - POST `/tickets/` with JWT → Ticket created

3. **Verify Workflow Processing** (Workflow API)
   - GET `/tasks/` with JWT → Task appears in list

4. **Perform Action** (Workflow API)
   - POST `/tasks/{id}/action/` with JWT → Action processed

5. **Verify Notification** (Notification Service)
   - Check email sent (mocked in tests)
   - Check in-app notification created

### Integration Testing Tools

- **pytest-django** for Django service tests
- **requests** library for HTTP API calls
- **celery-mock** for Celery task testing
- **Docker Compose** for integration environment

## References

- **System Architecture**: `/docs/A1_SYSTEM_ARCHITECTURE.md`
- **API Documentation**: Generated via drf-spectacular at `/api/docs/`
- **Environment Configuration**: `/ENVIRONMENT_STANDARDIZATION_REPORT.md`
- **Sequence Diagrams**: `/architecture/*.puml`

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Authors**: Integration Architecture Team
