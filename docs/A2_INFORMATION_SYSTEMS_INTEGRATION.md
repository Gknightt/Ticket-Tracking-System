# A.2 Information Systems Integration Documentation

## Table of Contents
1. [Integration Overview](#integration-overview)
2. [Integration Architecture](#integration-architecture)
3. [Integration Points](#integration-points)
4. [Data Flow Diagrams](#data-flow-diagrams)
5. [Inter-Service Communication](#inter-service-communication)
6. [External System Integration](#external-system-integration)
7. [Data Transformation and Mapping](#data-transformation-and-mapping)
8. [Integration Patterns](#integration-patterns)
9. [Error Handling and Resilience](#error-handling-and-resilience)
10. [Integration Security](#integration-security)

---

## Integration Overview

The Ticket Tracking System integrates multiple internal microservices and external systems to provide a unified ticketing and workflow management solution. The integration architecture is based on:

- **Asynchronous messaging** via RabbitMQ for loose coupling
- **RESTful APIs** for synchronous inter-service communication
- **WebSocket** for real-time client updates
- **Event-driven architecture** for workflow orchestration

**Key Integration Principles:**
- Service autonomy and independence
- Message-based communication for resilience
- Standardized API contracts
- Centralized authentication
- Distributed data management

---

## Integration Architecture

### High-Level Integration Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         External Systems                          │
│                                                                   │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │    HDTS     │     │     AMS     │     │     BMS     │       │
│  │  (Help Desk)│     │   (Asset    │     │  (Budget    │       │
│  │             │     │  Management)│     │ Management) │       │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘       │
│         │                   │                     │              │
└─────────┼───────────────────┼─────────────────────┼──────────────┘
          │                   │                     │
          │ Celery/AMQP       │ REST API            │ REST API
          │                   │                     │
┌─────────▼───────────────────┴─────────────────────┴──────────────┐
│                      Internal Services                            │
│                                                                   │
│  ┌─────────────────────────────────────────────────────┐         │
│  │              RabbitMQ Message Broker                │         │
│  │  (Central Integration Hub)                          │         │
│  │                                                      │         │
│  │  Queues:                                             │         │
│  │  - TICKET_TASKS_PRODUCTION (HDTS → Workflow)        │         │
│  │  - notification-queue-default (Workflow → Notif)    │         │
│  │  - inapp-notification-queue (Workflow → Notif)      │         │
│  │  - role_send-default (Auth → Workflow)              │         │
│  │  - tts.role.sync (Auth → Workflow)                  │         │
│  └─────────────────────────────────────────────────────┘         │
│                             │                                     │
│         ┌──────────┬────────┼────────┬──────────┐               │
│         │          │        │        │          │               │
│    ┌────▼───┐  ┌──▼───┐ ┌──▼───┐ ┌──▼────┐ ┌──▼──────┐        │
│    │  Auth  │  │ Work-│ │Messag│ │ Notif │ │ Ticket  │        │
│    │ Service│  │ flow │ │ ing  │ │Service│ │ Service │        │
│    │        │  │ API  │ │      │ │       │ │ (Mock)  │        │
│    └────┬───┘  └──┬───┘ └──┬───┘ └───┬───┘ └─────────┘        │
│         │         │        │         │                          │
│         │  REST   │  REST  │ WebSock │ REST                     │
│         │         │        │         │                          │
│    ┌────▼─────────▼────────▼─────────▼───┐                     │
│    │      PostgreSQL Database             │                     │
│    │  (Logical Separation per Service)    │                     │
│    └──────────────────────────────────────┘                     │
│                                                                  │
└────────────────────────────┬─────────────────────────────────────┘
                             │ REST API + WebSocket
                             │
                   ┌─────────▼─────────┐
                   │   Frontend (React) │
                   └───────────────────┘
```

---

## Integration Points

### 1. Frontend ↔ Backend Services

**Integration Type**: RESTful API + WebSocket  
**Protocol**: HTTP/HTTPS, WebSocket (WS/WSS)  
**Authentication**: JWT Bearer tokens  
**Data Format**: JSON

**Endpoints**:

| Frontend → Service | Method | Endpoint | Purpose |
|-------------------|--------|----------|---------|
| Frontend → Auth | POST | `/token/` | Obtain JWT tokens |
| Frontend → Auth | POST | `/api/v1/users/` | User management |
| Frontend → Auth | GET | `/api/v1/roles/` | Fetch roles |
| Frontend → Workflow API | GET | `/workflows/` | List workflows |
| Frontend → Workflow API | POST | `/tasks/` | Create tasks |
| Frontend → Workflow API | GET | `/audit/` | Audit logs |
| Frontend → Notification | GET | `/api/v2/notifications/inapp/` | In-app notifications |
| Frontend → Messaging | WS | `ws://messaging:8001/ws/comments/{ticket_id}/` | Real-time comments |

**Integration Flow - User Login**:
```
1. User enters credentials
2. Frontend → POST /token/ (Auth Service)
3. Auth validates credentials
4. Auth returns { access_token, refresh_token }
5. Frontend stores tokens (localStorage/sessionStorage)
6. Frontend includes token in all subsequent requests:
   Authorization: Bearer <access_token>
```

**Integration Flow - Real-Time Comments**:
```
1. Frontend establishes WebSocket connection
   ws://messaging-service:8001/ws/comments/123/
2. Messaging Service authenticates via JWT
3. User joined to channel group 'comments_123'
4. User posts comment via REST API
5. Messaging Service broadcasts to all WebSocket clients in group
6. Frontend receives update and displays new comment
```

---

### 2. Auth Service ↔ Other Services

**Integration Type**: RESTful API (Synchronous)  
**Protocol**: HTTP  
**Authentication**: JWT Shared Secret / Service-to-Service tokens  
**Data Format**: JSON

**Key Integrations**:

#### Auth → Workflow API (User Verification)
```python
# Workflow API calls Auth Service to verify user
import requests

def verify_user(user_id, token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f'{DJANGO_AUTH_SERVICE}/api/v1/users/{user_id}/',
        headers=headers
    )
    return response.json()
```

#### Auth → Workflow API (Role Synchronization)
```python
# Auth Service sends role updates via RabbitMQ
from celery import current_app as app

def sync_role_to_workflow(role_data):
    app.send_task(
        'workflow.role.sync',
        kwargs={'role_data': role_data},
        queue='tts.role.sync'
    )
```

**Data Mapping**:
```json
{
  "user_id": 123,
  "username": "john.doe",
  "email": "john@example.com",
  "roles": [
    {
      "system": "TTS",
      "role_name": "Agent",
      "permissions": ["view_ticket", "update_ticket"]
    }
  ]
}
```

---

### 3. Workflow API ↔ Notification Service

**Integration Type**: Message Queue (Asynchronous)  
**Protocol**: AMQP (via RabbitMQ)  
**Queue**: `notification-queue-default`, `inapp-notification-queue`  
**Data Format**: JSON

**Integration Flow - Task Assignment Notification**:
```
1. Workflow API assigns task to user
2. Workflow API enqueues notification task:
   
   app.send_task(
       'task.send_assignment_notification',
       kwargs={
           'user_id': 123,
           'task_id': 'T-456',
           'task_title': 'Approve Budget Request',
           'role_name': 'Budget Approver'
       },
       queue='notification-queue-default'
   )

3. RabbitMQ routes message to notification-queue-default
4. Notification Worker consumes message
5. Notification Worker creates in-app notification in DB
6. Notification Worker sends email via SMTP
7. Worker acknowledges message to RabbitMQ
```

**Message Schema**:
```json
{
  "task": "task.send_assignment_notification",
  "id": "uuid-generated-by-celery",
  "kwargs": {
    "user_id": 123,
    "task_id": "T-456",
    "task_title": "Approve Budget Request",
    "role_name": "Budget Approver"
  },
  "retries": 0,
  "eta": null
}
```

---

### 4. HDTS (External) → Workflow API

**Integration Type**: Message Queue (Asynchronous)  
**Protocol**: AMQP (via RabbitMQ)  
**Queue**: `TICKET_TASKS_PRODUCTION`  
**Data Format**: JSON

**Purpose**: HDTS (Help Desk & Ticketing System) sends tickets to the workflow engine for processing.

**Integration Flow**:
```
1. HDTS creates ticket in external system
2. HDTS sends ticket to Ticket Service (mock) via API or direct queue
3. Ticket Service enqueues to RabbitMQ:
   
   app.send_task(
       'tickets.tasks.receive_ticket',
       kwargs={'ticket_data': {
           'ticket_id': 'HDTS-12345',
           'title': 'Network Issue',
           'description': 'Cannot access internal servers',
           'priority': 'high',
           'category': 'IT Support',
           'sub_category': 'Network',
           'requester': 'john.doe@company.com'
       }},
       queue='TICKET_TASKS_PRODUCTION'
   )

4. Workflow Worker consumes from TICKET_TASKS_PRODUCTION
5. Workflow API processes ticket:
   a. Find matching workflow by category/sub_category
   b. Create Task instance
   c. Initialize first step
   d. Assign to role (round-robin)
   e. Send notification to assigned user
6. Worker acknowledges message
```

**Ticket Schema from HDTS**:
```json
{
  "ticket_id": "HDTS-12345",
  "title": "Network connectivity issue",
  "description": "User cannot connect to internal network",
  "priority": "high",
  "category": "IT Support",
  "sub_category": "Network",
  "department": "Operations",
  "requester_email": "user@company.com",
  "requester_name": "John Doe",
  "created_at": "2025-11-19T10:30:00Z",
  "attachments": [
    {
      "filename": "screenshot.png",
      "url": "https://hdts.company.com/files/12345/screenshot.png"
    }
  ]
}
```

**Response (Acknowledgment)**:
- Message acknowledgment to RabbitMQ after successful processing
- Failure → message re-queued for retry

---

### 5. Workflow API ↔ AMS/BMS (External Systems)

**Integration Type**: RESTful API (Synchronous)  
**Protocol**: HTTP/HTTPS  
**Authentication**: API Key or OAuth  
**Data Format**: JSON

**Purpose**: Workflow steps may require external approvals from Asset Management System (AMS) or Budget Management System (BMS).

**Integration Flow - AMS Checkout**:
```
1. Workflow reaches "Asset Assignment" step
2. Workflow API calls AMS:
   
   POST /api/assets/reserve/
   Headers:
     X-API-Key: <ams-api-key>
     Content-Type: application/json
   Body:
     {
       "asset_id": "ASSET-789",
       "requester_id": 123,
       "task_id": "T-456",
       "duration_days": 30
     }

3. AMS validates availability
4. AMS reserves asset
5. AMS returns reservation confirmation:
   {
     "reservation_id": "RES-999",
     "status": "confirmed",
     "asset_id": "ASSET-789",
     "valid_until": "2025-12-19T10:30:00Z"
   }

6. Workflow API stores reservation_id in task metadata
7. Workflow transitions to next step
```

**Integration Flow - BMS Budget Check**:
```
1. Workflow reaches "Budget Approval" step
2. Workflow API calls BMS:
   
   POST /api/budget/check/
   Headers:
     Authorization: Bearer <bms-token>
   Body:
     {
       "department": "Operations",
       "amount": 5000.00,
       "currency": "USD",
       "category": "Equipment",
       "requester_id": 123
     }

3. BMS checks budget availability
4. BMS returns approval decision:
   {
     "approved": true,
     "budget_line_id": "BL-2025-OPS-001",
     "remaining_balance": 15000.00,
     "approval_id": "APPR-555"
   }

5. Workflow stores approval_id
6. If approved: transition to next step
   If rejected: send rejection notification
```

---

### 6. Messaging Service ↔ Other Services

**Integration Type**: Mixed (REST + WebSocket)  
**Protocol**: HTTP for data, WebSocket for real-time

**Comment Creation Flow**:
```
1. User posts comment via REST API:
   POST /api/comments/
   Body: { "ticket_id": 123, "text": "Issue resolved", "user_id": 456 }

2. Messaging Service saves comment to DB

3. Messaging Service broadcasts to WebSocket channel:
   channel_layer.group_send(
       'comments_123',
       {
           'type': 'comment_create',
           'message': comment_serialized_data,
           'action': 'create',
           'timestamp': datetime.now()
       }
   )

4. All connected WebSocket clients receive update

5. Optional: Messaging Service calls Notification Service
   (future enhancement for @mentions)
```

---

## Data Flow Diagrams

### DFD Level 0 - Context Diagram

```
┌────────────┐
│   HDTS     │────────────┐
│ (External) │            │
└────────────┘            │
                          │ Tickets
                          ▼
┌────────────┐       ┌────────────────────┐        ┌──────────┐
│   Agent    │◄─────►│  Ticket Tracking   │◄──────►│  Admin   │
│  (User)    │       │      System        │        │  (User)  │
└────────────┘       └────────────────────┘        └──────────┘
                          ▲         ▲
                          │         │
┌────────────┐            │         │          ┌──────────────┐
│    AMS     │────────────┘         └──────────│     BMS      │
│ (External) │                                 │  (External)  │
└────────────┘                                 └──────────────┘
```

### DFD Level 1 - System Decomposition

```
┌─────────────────────────────────────────────────────────────┐
│                    Ticket Tracking System                    │
│                                                              │
│  ┌──────────────┐                      ┌────────────────┐  │
│  │ 1.0          │   User Data          │ 2.0            │  │
│  │ Authenticate │◄────────────────────►│ Manage Users   │  │
│  │ User         │                      │ and Roles      │  │
│  └──────┬───────┘                      └────────────────┘  │
│         │ JWT Token                                         │
│         │                                                   │
│  ┌──────▼───────────────────────────────────────────────┐  │
│  │ 3.0                                                   │  │
│  │ Process Tickets and Execute Workflows                │  │
│  │                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │  │
│  │  │3.1 Create│  │3.2 Assign│  │3.3 Track Progress │  │  │
│  │  │Task      │→ │to Role   │→ │and Transitions    │  │  │
│  │  └──────────┘  └──────────┘  └───────────────────┘  │  │
│  └───────────────────┬──────────────────────────────────┘  │
│                      │ Assignment Event                    │
│  ┌───────────────────▼───────────────┐                     │
│  │ 4.0                                │                     │
│  │ Send Notifications                │                     │
│  │  (Email + In-App)                 │                     │
│  └───────────────────────────────────┘                     │
│                                                             │
│  ┌──────────────────────────────────┐                      │
│  │ 5.0                               │                      │
│  │ Real-Time Messaging               │                      │
│  │  (Comments, Updates)              │                      │
│  └──────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### DFD Level 2 - Workflow Processing

```
                 ┌─────────────────────┐
                 │  Ticket from HDTS   │
                 └──────────┬──────────┘
                            │
                            ▼
         ┌──────────────────────────────────────┐
         │ 3.1 Receive and Validate Ticket      │
         │  - Parse ticket data                 │
         │  - Validate required fields          │
         └──────────────────┬───────────────────┘
                            │ Validated Ticket
                            ▼
         ┌──────────────────────────────────────┐
         │ 3.2 Match Workflow                   │
         │  - Find by category/sub_category     │
         │  - Check workflow is deployed        │
         └──────────────────┬───────────────────┘
                            │ Matched Workflow
                            ▼
         ┌──────────────────────────────────────┐
         │ 3.3 Create Task Instance             │
         │  - Initialize task state             │
         │  - Set SLA based on priority         │
         │  - Create first step instance        │
         └──────────────────┬───────────────────┘
                            │ Task ID
                            ▼
         ┌──────────────────────────────────────┐
         │ 3.4 Assign to Role                   │
         │  - Get users in role                 │
         │  - Apply round-robin algorithm       │
         │  - Create assignment record          │
         └──────────────────┬───────────────────┘
                            │ Assignment
                            ▼
         ┌──────────────────────────────────────┐
         │ 3.5 Send Notification                │
         │  - Enqueue to notification queue     │
         │  - Task assignment details           │
         └──────────────────────────────────────┘
```

---

## Inter-Service Communication

### Service Communication Matrix

| From Service | To Service | Communication Type | Protocol | Purpose |
|--------------|------------|-------------------|----------|---------|
| Frontend | Auth | Synchronous | REST/HTTPS | Authentication, User CRUD |
| Frontend | Workflow API | Synchronous | REST/HTTPS | Workflow/Task management |
| Frontend | Messaging | Asynchronous | WebSocket | Real-time comments |
| Frontend | Notification | Synchronous | REST/HTTPS | In-app notifications |
| Workflow API | Auth | Synchronous | REST/HTTP | User verification |
| Workflow API | Notification | Asynchronous | AMQP | Send notifications |
| Workflow API | AMS (External) | Synchronous | REST/HTTPS | Asset checkout |
| Workflow API | BMS (External) | Synchronous | REST/HTTPS | Budget approval |
| Auth | Workflow API | Asynchronous | AMQP | Role synchronization |
| Ticket Service | Workflow API | Asynchronous | AMQP | Ticket ingestion |
| Messaging | Auth | Synchronous | REST/HTTP | WebSocket authentication |

---

### Service Dependency Graph

```
                  ┌───────────────┐
                  │     Auth      │ (Core Dependency)
                  │   Service     │
                  └───────┬───────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
            │             │             │
    ┌───────▼─────┐  ┌───▼────────┐  ┌▼────────────┐
    │  Workflow   │  │  Messaging │  │ Notification│
    │    API      │  │  Service   │  │   Service   │
    └───────┬─────┘  └────────────┘  └─────────────┘
            │
            │ (Depends on)
            │
    ┌───────▼────────────┐
    │  External Systems  │
    │   (AMS, BMS)       │
    └────────────────────┘
```

**Critical Paths**:
1. **Auth Service**: Single point of authentication; all services depend on it
2. **RabbitMQ**: Message broker; failure impacts async processing
3. **PostgreSQL**: Database; failure impacts all services

---

## External System Integration

### HDTS (Help Desk & Ticketing System) - Inbound Integration

**Integration Pattern**: Producer-Consumer (Asynchronous)

**Data Contract**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "HDTS Ticket",
  "type": "object",
  "required": ["ticket_id", "title", "category", "sub_category", "priority"],
  "properties": {
    "ticket_id": {
      "type": "string",
      "description": "Unique ticket ID from HDTS"
    },
    "title": {
      "type": "string",
      "maxLength": 200
    },
    "description": {
      "type": "string"
    },
    "priority": {
      "type": "string",
      "enum": ["low", "medium", "high", "urgent"]
    },
    "category": {
      "type": "string"
    },
    "sub_category": {
      "type": "string"
    },
    "department": {
      "type": "string"
    },
    "requester_email": {
      "type": "string",
      "format": "email"
    },
    "attachments": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "filename": {"type": "string"},
          "url": {"type": "string", "format": "uri"}
        }
      }
    }
  }
}
```

**Error Handling**:
- Invalid ticket → Message rejected, logged, sent to dead-letter queue
- Missing workflow → Ticket queued, notification to admin
- Processing failure → Retry 3 times with exponential backoff

---

### AMS (Asset Management System) - Outbound Integration

**Integration Pattern**: Request-Reply (Synchronous)

**API Specification**:

**Endpoint**: `POST /api/assets/reserve/`  
**Authentication**: API Key in header `X-API-Key`  
**Request**:
```json
{
  "asset_id": "string",
  "requester_id": "integer",
  "task_id": "string",
  "duration_days": "integer",
  "notes": "string"
}
```
**Response (Success - 200)**:
```json
{
  "reservation_id": "string",
  "status": "confirmed",
  "asset_id": "string",
  "valid_until": "datetime",
  "asset_details": {
    "name": "string",
    "model": "string",
    "serial": "string"
  }
}
```
**Response (Error - 400)**:
```json
{
  "error": "Asset not available",
  "available_alternatives": ["ASSET-790", "ASSET-791"]
}
```

**Timeout**: 30 seconds  
**Retry Strategy**: None (synchronous, user-facing)  
**Fallback**: Display error, allow manual asset selection

---

### BMS (Budget Management System) - Outbound Integration

**Integration Pattern**: Request-Reply (Synchronous)

**API Specification**:

**Endpoint**: `POST /api/budget/check/`  
**Authentication**: OAuth 2.0 Bearer token  
**Request**:
```json
{
  "department": "string",
  "amount": "decimal",
  "currency": "string",
  "category": "string",
  "requester_id": "integer",
  "justification": "string"
}
```
**Response (Approved - 200)**:
```json
{
  "approved": true,
  "budget_line_id": "string",
  "remaining_balance": "decimal",
  "approval_id": "string",
  "approved_by": "string",
  "approved_at": "datetime"
}
```
**Response (Rejected - 200)**:
```json
{
  "approved": false,
  "reason": "Insufficient budget",
  "available_amount": "decimal",
  "rejection_code": "INSUFFICIENT_FUNDS"
}
```

**Timeout**: 30 seconds  
**Retry Strategy**: 1 retry after 5 seconds  
**Fallback**: Queue for manual approval

---

## Data Transformation and Mapping

### Ticket Data Transformation (HDTS → Workflow API)

**Source (HDTS)**:
```json
{
  "ticket_id": "HDTS-12345",
  "title": "Network Issue",
  "description": "Cannot access servers",
  "priority": "high",
  "category": "IT Support",
  "sub_category": "Network",
  "requester_email": "user@company.com",
  "created_at": "2025-11-19T10:30:00Z"
}
```

**Transformation Logic**:
```python
def transform_hdts_ticket(hdts_ticket):
    # Map HDTS priority to internal priority
    priority_map = {
        'high': 'urgent',
        'medium': 'high',
        'low': 'medium'
    }
    
    # Find matching workflow
    workflow = Workflows.objects.filter(
        category=hdts_ticket['category'],
        sub_category=hdts_ticket['sub_category'],
        status='deployed'
    ).first()
    
    if not workflow:
        raise WorkflowNotFoundError(
            f"No workflow for {hdts_ticket['category']}/{hdts_ticket['sub_category']}"
        )
    
    # Create task
    task = Task.objects.create(
        workflow=workflow,
        external_ticket_id=hdts_ticket['ticket_id'],
        title=hdts_ticket['title'],
        description=hdts_ticket['description'],
        priority=priority_map.get(hdts_ticket['priority'], 'medium'),
        requester_email=hdts_ticket['requester_email'],
        sla_deadline=calculate_sla_deadline(
            workflow, 
            priority_map.get(hdts_ticket['priority'], 'medium')
        )
    )
    
    return task
```

**Target (Workflow API Task)**:
```json
{
  "task_id": "T-456",
  "workflow_id": 10,
  "external_ticket_id": "HDTS-12345",
  "title": "Network Issue",
  "description": "Cannot access servers",
  "priority": "urgent",
  "status": "pending",
  "current_step": 1,
  "assigned_user": 123,
  "sla_deadline": "2025-11-19T14:30:00Z",
  "created_at": "2025-11-19T10:35:00Z"
}
```

---

### User Data Synchronization (Auth → Workflow API)

**When**: Role changes, user profile updates

**Source (Auth Service)**:
```json
{
  "user_id": 123,
  "username": "john.doe",
  "email": "john.doe@company.com",
  "system_roles": [
    {
      "system": "TTS",
      "role_id": 5,
      "role_name": "Budget Approver",
      "assigned_at": "2025-11-01T00:00:00Z"
    }
  ]
}
```

**Transformation**:
```python
@shared_task(name='workflow.role.sync')
def sync_user_role(user_data):
    for system_role in user_data['system_roles']:
        if system_role['system'] == 'TTS':
            # Map to workflow role
            workflow_role, created = WorkflowRole.objects.get_or_create(
                name=system_role['role_name']
            )
            
            # Create/update user-role assignment
            UserRoleAssignment.objects.update_or_create(
                user_id=user_data['user_id'],
                role=workflow_role,
                defaults={
                    'email': user_data['email'],
                    'username': user_data['username'],
                    'assigned_at': system_role['assigned_at']
                }
            )
```

**Target (Workflow API)**:
```json
{
  "assignment_id": 789,
  "user_id": 123,
  "username": "john.doe",
  "email": "john.doe@company.com",
  "workflow_role_id": 10,
  "workflow_role_name": "Budget Approver",
  "active": true
}
```

---

## Integration Patterns

### 1. Request-Reply Pattern

**Used For**: Synchronous operations requiring immediate response

**Example**: Workflow API → Auth Service (User verification)

```python
def get_user_details(user_id, token):
    response = requests.get(
        f'{AUTH_SERVICE_URL}/api/v1/users/{user_id}/',
        headers={'Authorization': f'Bearer {token}'},
        timeout=10
    )
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        raise UserNotFoundError(f'User {user_id} not found')
    else:
        raise ServiceError(f'Auth service error: {response.status_code}')
```

---

### 2. Publish-Subscribe Pattern

**Used For**: Broadcasting events to multiple consumers

**Example**: Comment created → Notify all WebSocket clients

```python
# Publisher (Messaging Service)
async def broadcast_comment(ticket_id, comment_data):
    await channel_layer.group_send(
        f'comments_{ticket_id}',
        {
            'type': 'comment_create',
            'message': comment_data,
            'timestamp': datetime.now().isoformat()
        }
    )

# Subscribers (All WebSocket clients in room)
async def comment_create(self, event):
    await self.send(text_data=json.dumps({
        'type': 'comment_update',
        'action': 'create',
        'comment': event['message']
    }))
```

---

### 3. Message Queue Pattern

**Used For**: Asynchronous, reliable task execution

**Example**: Ticket Service → Workflow API

```python
# Producer (Ticket Service)
from celery import current_app as app

def send_ticket_to_workflow(ticket_data):
    app.send_task(
        'tickets.tasks.receive_ticket',
        kwargs={'ticket_data': ticket_data},
        queue='TICKET_TASKS_PRODUCTION'
    )

# Consumer (Workflow Worker)
@shared_task(name='tickets.tasks.receive_ticket')
def receive_ticket(ticket_data):
    task = transform_and_create_task(ticket_data)
    assign_to_role(task)
    send_assignment_notification(task)
    return {'status': 'success', 'task_id': task.id}
```

---

### 4. Circuit Breaker Pattern

**Used For**: Preventing cascading failures in external integrations

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def call_ams_api(asset_id):
    response = requests.post(
        f'{AMS_URL}/api/assets/reserve/',
        json={'asset_id': asset_id},
        headers={'X-API-Key': AMS_API_KEY},
        timeout=30
    )
    response.raise_for_status()
    return response.json()

# Usage
try:
    result = call_ams_api('ASSET-123')
except CircuitBreakerError:
    # Circuit open, use fallback
    return fallback_manual_asset_selection()
```

---

## Error Handling and Resilience

### Retry Strategies

| Integration Type | Retry Count | Backoff | Timeout |
|-----------------|-------------|---------|---------|
| REST (Auth verification) | 2 | Linear 5s | 10s |
| REST (External AMS/BMS) | 1 | None | 30s |
| Message Queue (HDTS) | 3 | Exponential 2^n s | N/A |
| Message Queue (Notifications) | 5 | Exponential 2^n s | N/A |
| WebSocket | Infinite | Reconnect 3s | N/A |

### Dead Letter Queues

**Queue**: `TICKET_TASKS_PRODUCTION_DLQ`  
**Purpose**: Store failed ticket processing attempts

**Trigger Conditions**:
- 3 consecutive processing failures
- Invalid ticket schema
- Workflow not found

**Monitoring**:
- Admin notification on DLQ message
- Dashboard showing DLQ depth
- Manual reprocessing interface

---

### Fallback Mechanisms

1. **Auth Service Unavailable**:
   - Cache user data for 5 minutes
   - Allow operations with cached data
   - Display warning banner to users

2. **AMS/BMS Unavailable**:
   - Queue step for manual processing
   - Notify admin
   - Allow workflow to proceed with "pending external approval" status

3. **Notification Service Failure**:
   - Log notification to database
   - Retry asynchronously
   - Ensure in-app notification created (higher priority)

4. **Database Connection Lost**:
   - Retry connection 3 times
   - Return 503 Service Unavailable
   - Health check endpoint reflects status

---

## Integration Security

### Authentication Methods

| Integration | Method | Details |
|-------------|--------|---------|
| Frontend → Services | JWT Bearer | Access token in Authorization header |
| Service → Service (Auth) | JWT Bearer | Shared secret for token validation |
| Service → Service (Notification) | API Key | X-API-Key header |
| External → System (HDTS) | Message Signature | HMAC SHA256 signature |
| System → External (AMS/BMS) | OAuth 2.0 | Bearer token with refresh |

---

### Data Encryption

1. **In Transit**:
   - HTTPS/TLS 1.2+ for all REST APIs
   - WSS (WebSocket Secure) for real-time connections
   - AMQPS for RabbitMQ in production

2. **At Rest**:
   - PostgreSQL encryption at rest
   - Encrypted backups
   - Environment variables for secrets

---

### Access Control

1. **API Endpoints**:
   - JWT token validation on every request
   - Role-based permissions check
   - Rate limiting per IP/user

2. **Message Queues**:
   - RabbitMQ user authentication
   - Virtual host isolation
   - Queue-level permissions

3. **Database**:
   - Service-specific database users
   - Least privilege principle
   - Audit logging for sensitive operations

---

## Monitoring and Observability

### Integration Metrics

**Tracked Metrics**:
- Request rate (requests/second)
- Error rate (errors/total requests)
- Response time (p50, p95, p99)
- Queue depth (messages in queue)
- Consumer lag (time in queue)
- Circuit breaker state (open/closed/half-open)

**Alerting Thresholds**:
- Error rate > 5%
- Response time p95 > 2s
- Queue depth > 1000 messages
- Circuit breaker open > 5 minutes

---

### Integration Logging

**Log Format** (JSON):
```json
{
  "timestamp": "2025-11-19T10:35:00Z",
  "level": "INFO",
  "service": "workflow_api",
  "integration": "auth_service",
  "operation": "verify_user",
  "user_id": 123,
  "duration_ms": 45,
  "status": "success"
}
```

**Error Log**:
```json
{
  "timestamp": "2025-11-19T10:35:00Z",
  "level": "ERROR",
  "service": "workflow_api",
  "integration": "ams",
  "operation": "reserve_asset",
  "asset_id": "ASSET-123",
  "error_code": "TIMEOUT",
  "error_message": "Connection timeout after 30s",
  "stack_trace": "..."
}
```

---

## Appendix

### Integration Testing

**Test Scenarios**:
1. Ticket ingestion from HDTS (happy path)
2. Ticket ingestion with missing workflow
3. User role synchronization
4. Notification delivery (email + in-app)
5. WebSocket reconnection
6. AMS API timeout and fallback
7. Database connection failure and recovery

**Test Data**:
- Sample HDTS tickets: `/test-data/hdts-tickets.json`
- Sample AMS responses: `/test-data/ams-responses.json`
- Sample BMS responses: `/test-data/bms-responses.json`

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Maintained By**: Integration Architecture Team
