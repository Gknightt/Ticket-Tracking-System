# A.1 System Architecture Documentation

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Style](#architecture-style)
4. [Component Architecture](#component-architecture)
5. [Service Descriptions](#service-descriptions)
6. [Communication Protocols](#communication-protocols)
7. [Technology Stack](#technology-stack)
8. [Deployment Architecture](#deployment-architecture)
9. [Scalability and Performance](#scalability-and-performance)

---

## Executive Summary

The Ticket Tracking System is a distributed microservices-based application designed to manage and automate ticketing workflows. The system uses a message-driven architecture with RabbitMQ for asynchronous communication, enabling loose coupling between services and ensuring high availability and scalability.

**Key Architectural Principles:**
- Microservices architecture for independent service deployment
- Asynchronous message processing via RabbitMQ (NOT using Celery broker, but Celery workers consume from RabbitMQ)
- Event-driven architecture for real-time updates
- RESTful APIs for synchronous communication
- WebSocket support for real-time client updates
- Shared PostgreSQL database with logical separation

**Important Note**: The system uses RabbitMQ directly as the message broker. Celery is used only as worker processes that consume tasks from RabbitMQ queues, not as a separate broker layer.

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                              │
│                    (React + Vite + WebSocket)                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP/REST + WebSocket
                             │
┌────────────────────────────┴────────────────────────────────────────┐
│                         API Gateway Layer                           │
│              (NGINX/Load Balancer - Production)                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼─────────┐  ┌──────▼──────┐  ┌─────────▼──────────┐
│  Auth Service   │  │  Workflow   │  │    Messaging       │
│   (Port 8003)   │  │  API Service│  │    Service         │
│                 │  │ (Port 8002) │  │   (Port 8005)      │
│ - Authentication│  │             │  │                    │
│ - Authorization │  │ - Workflow  │  │ - WebSocket        │
│ - User Mgmt     │  │   Execution │  │ - Real-time        │
│ - Role Mgmt     │  │ - Task Mgmt │  │   Comments         │
│ - JWT Tokens    │  │ - Audit Log │  │ - Chat             │
└────────┬────────┘  └──────┬──────┘  └─────────┬──────────┘
         │                  │                    │
         │         ┌────────▼────────┐           │
         │         │  Notification   │           │
         │         │    Service      │           │
         │         │  (Port 8006)    │           │
         │         │                 │           │
         │         │ - Email Notif   │           │
         │         │ - In-App Notif  │           │
         │         │ - Task Queue    │           │
         │         └────────┬────────┘           │
         │                  │                    │
         └──────────────────┼────────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         │         Message Broker Layer        │
         │      RabbitMQ (Port 5672/15672)     │
         │                                     │
         │  Queues:                            │
         │  - TICKET_TASKS_PRODUCTION          │
         │  - notification-queue-default       │
         │  - inapp-notification-queue         │
         │  - role_send-default                │
         │  - tts.role.sync                    │
         │  - workflow_seed_queue              │
         └──────────────────┬──────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         │      Celery Worker Layer            │
         │                                     │
         │  - workflow-worker (consumes)       │
         │  - notification-worker (consumes)   │
         │  - Background job processing        │
         └──────────────────┬──────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         │         Data Layer                  │
         │   PostgreSQL Database (Port 5432)   │
         │                                     │
         │   Logical Databases:                │
         │   - authservice                     │
         │   - workflowmanagement              │
         │   - messagingservice                │
         │   - notificationservice             │
         │   - ticketmanagement (mock)         │
         └─────────────────────────────────────┘

External System (Mock):
┌────────────────────┐
│  Ticket Service    │  Simulates HDTS (Help Desk & Ticketing System)
│  (Port 8004)       │  Sends tickets via Celery to workflow_api
└────────────────────┘
```

---

## Architecture Style

### Microservices Architecture

The system follows a **microservices architecture** pattern with the following characteristics:

1. **Service Independence**: Each service can be developed, deployed, and scaled independently
2. **Database per Service**: Logical database separation (though sharing PostgreSQL instance)
3. **Decentralized Governance**: Each service owns its data and business logic
4. **Communication**: Mix of synchronous (REST) and asynchronous (RabbitMQ) communication

### Event-Driven Architecture

Services communicate through events using RabbitMQ:
- **Publish-Subscribe Pattern**: Services publish events to queues, workers subscribe
- **Asynchronous Processing**: Long-running tasks processed in background
- **Loose Coupling**: Services don't need to know about each other's implementation

### Layered Architecture

Each service follows a layered architecture:
```
┌────────────────────┐
│  Presentation      │ ← REST API endpoints, WebSocket handlers
├────────────────────┤
│  Business Logic    │ ← Services, Serializers, Validators
├────────────────────┤
│  Data Access       │ ← Django ORM Models
├────────────────────┤
│  Database          │ ← PostgreSQL
└────────────────────┘
```

---

## Component Architecture

### Core Services

#### 1. Authentication Service (auth)
**Port**: 8003  
**Database**: authservice  
**Responsibilities**:
- User authentication and authorization
- JWT token generation and validation
- Role-Based Access Control (RBAC)
- User management (CRUD operations)
- System role management (TTS, HDTS, AMS, BMS systems)
- OTP generation for login
- Email notifications for user events
- CAPTCHA validation

**Key Components**:
- `users/` - User model and CRUD operations
- `roles/` - Role definitions and permissions
- `system_roles/` - System-specific role mappings
- `tts/` - TTS (Ticket Tracking System) specific logic
- `hdts/` - HDTS (Help Desk & Ticketing System) integration
- `systems/` - Multi-system support

**API Endpoints**:
- `/api/v1/users/` - User management
- `/api/v1/roles/` - Role management
- `/token/` - JWT token generation
- `/logout/` - User logout
- `/login/` - User login with OTP support

**Technology**:
- Django 5.2.1
- Django REST Framework 3.16.0
- djangorestframework-simplejwt 5.5.0
- django-cors-headers 4.7.0

---

#### 2. Workflow API Service (workflow_api)
**Port**: 8002  
**Database**: workflowmanagement  
**Responsibilities**:
- Workflow creation, modification, and execution
- Task orchestration and routing
- Step execution and transitions
- Role-based task assignment
- SLA management per priority level
- Audit logging for all workflow actions
- Integration with external systems (AMS, BMS checkout)

**Key Components**:
- `workflow/` - Workflow models, CRUD, execution logic
- `step/` - Workflow step definitions
- `task/` - Task management and transitions
- `role/` - Workflow role definitions
- `tickets/` - Ticket processing from HDTS
- `audit/` - Audit trail for workflow actions
- `amscheckout/`, `bmscheckout/` - External system integrations
- `workflowmanager/` - Workflow orchestration

**Workflow Model Structure**:
```python
Workflow
├── name, description
├── category, sub_category, department
├── SLA per priority (low, medium, high, urgent)
├── status (draft, deployed, paused, initialized)
├── end_logic (asset, budget, notification)
└── Steps (many-to-many)
    ├── Step
    │   ├── role assignment
    │   ├── weight (priority)
    │   ├── approval/review logic
    │   └── Transitions
    └── Task (instance of workflow for a ticket)
```

**API Endpoints**:
- `/workflows/` - Workflow CRUD
- `/steps/` - Step management
- `/tasks/` - Task tracking
- `/transitions/` - State transitions
- `/roles/` - Workflow roles
- `/audit/` - Audit logs

**Technology**:
- Django 5.2.1
- Celery 5.5.3 (task execution)
- django-filters 25.1
- drf-spectacular 0.28.0 (API documentation)

---

#### 3. Messaging Service (messaging)
**Port**: 8005  
**Database**: messagingservice  
**Responsibilities**:
- Real-time messaging via WebSocket
- Comment management on tickets
- Comment ratings and replies
- Document attachments to comments
- Push notifications to connected clients

**Key Components**:
- `comments/` - Comment models and WebSocket consumers
- `tickets/` - Ticket-related messaging
- WebSocket routing and channel layers

**WebSocket Endpoints**:
- `ws/comments/<ticket_id>/` - Real-time comment updates
- `ws/tickets/<ticket_id>/` - Ticket update notifications

**Message Types**:
- `comment_create` - New comment posted
- `comment_update` - Comment edited
- `comment_delete` - Comment removed
- `comment_reply` - Reply to comment
- `comment_rate` - Comment rating
- `comment_attach_document` - Document attached
- `ping/pong` - Connection health check

**Technology**:
- Django 5.2.1
- Django Channels (WebSocket)
- asgiref 3.8.1

---

#### 4. Notification Service (notification_service)
**Port**: 8006  
**Database**: notificationservice  
**Responsibilities**:
- Email notification dispatch
- In-app notification management
- Notification templates
- Notification history and logging
- Task assignment notifications
- Bulk notification processing

**Key Components**:
- `notifications/` - Notification models and services
- `app/` - Celery tasks for async notification processing

**Celery Tasks**:
- `task.send_assignment_notification` - Task assignment alerts
- `notifications.create_inapp_notification` - In-app notifications
- `notifications.mark_notification_read` - Mark as read
- `notifications.bulk_create_notifications` - Bulk operations

**API Endpoints**:
- `/api/v1/notifications/send/` - Send notification
- `/api/v2/notifications/inapp/` - In-app notification CRUD
- `/api/v1/notifications/history/` - Notification history
- `/health/` - Service health check

**Notification Types**:
- Task assignment
- Password reset
- Login alerts
- Failed login attempts
- Profile changes
- System notifications

**Technology**:
- Django 5.2.1
- Celery 5.5.3
- Email backends (SMTP, Console)

---

#### 5. Ticket Service (ticket_service) - MOCK
**Port**: 8004  
**Database**: ticketmanagement  
**Responsibilities**:
- **Simulates external HDTS (Help Desk & Ticketing System)**
- Receives tickets from external systems
- Enqueues tickets to workflow_api via Celery/RabbitMQ
- File attachment handling
- NOT part of core system - for testing integration

**Key Components**:
- `tickets/` - Ticket model and API
- `tickets/tasks.py` - Celery task to push tickets

**Technology**:
- Django 5.2.1
- Celery 5.5.3

---

#### 6. Frontend Application
**Port**: 1000  
**Responsibilities**:
- User interface for agents and administrators
- Real-time updates via WebSocket
- Ticket management interface
- Workflow visualization
- Dashboard and analytics
- User profile management

**Key Components**:
- `src/pages/` - Page components
- `src/components/` - Reusable UI components
- `src/api/` - API client configuration
- `src/context/` - React context for state management
- `src/routes/` - Application routing

**Technology**:
- React 18
- Vite (build tool)
- Axios (HTTP client)
- WebSocket client

---

### Infrastructure Services

#### RabbitMQ Message Broker
**Ports**: 5672 (AMQP), 15672 (Management UI)  
**Credentials**: admin/admin (development)

**Queues**:
- `TICKET_TASKS_PRODUCTION` - Tickets from HDTS to workflow
- `notification-queue-default` - Email notifications
- `inapp-notification-queue` - In-app notifications
- `role_send-default` - Role synchronization
- `tts.role.sync` - TTS role sync
- `tts.user_system_role.sync` - User-role sync
- `workflow_seed_queue` - Workflow seeding
- `workflow_seed` - Workflow initialization

**Routing**:
```
HDTS → TICKET_TASKS_PRODUCTION → workflow-worker → workflow_api
workflow_api → notification-queue-default → notification-worker → Email
workflow_api → inapp-notification-queue → notification-worker → In-App DB
auth → tts.role.sync → workflow-worker → Role sync
```

---

#### PostgreSQL Database
**Port**: 5432 (mapped to 5433 on host)  
**Credentials**: postgres/postgrespass (development)

**Logical Databases**:
```
postgres (instance)
├── authservice
│   ├── users
│   ├── roles
│   ├── system_roles
│   ├── user_system_roles
│   └── systems
├── workflowmanagement
│   ├── workflows
│   ├── steps
│   ├── tasks
│   ├── transitions
│   ├── audit_logs
│   └── categories
├── messagingservice
│   ├── comments
│   ├── comment_ratings
│   └── comment_attachments
├── notificationservice
│   ├── notifications
│   ├── notification_templates
│   ├── notification_logs
│   └── inapp_notifications
└── ticketmanagement (mock)
    ├── tickets
    └── attachments
```

---

## Communication Protocols

### Synchronous Communication (REST)

**Protocol**: HTTP/1.1 with REST  
**Format**: JSON  
**Authentication**: JWT Bearer tokens

**Inter-Service Communication**:
```
Frontend → Auth Service
  POST /token/
  Headers: Content-Type: application/json
  Body: { "username": "user", "password": "pass" }
  Response: { "access": "token", "refresh": "token" }

Workflow API → Auth Service
  GET /api/v1/users/{user_id}/
  Headers: Authorization: Bearer <token>
  Response: { "id": 1, "username": "user", ... }

Workflow API → Notification Service
  POST /api/v1/notifications/send/
  Headers: X-API-Key: <api-key>
  Body: { "user_email": "...", "notification_type": "..." }
```

**Service Discovery**:
- Environment variables for service URLs
- Docker network DNS resolution (e.g., `http://auth-service:8000`)
- No service registry (simple architecture)

---

### Asynchronous Communication (Message Queue)

**Protocol**: AMQP (Advanced Message Queuing Protocol)  
**Broker**: RabbitMQ  
**Format**: JSON (serialized by Celery)

**Message Flow**:
```
Ticket Service:
  app.send_task(
    "tickets.tasks.receive_ticket",
    kwargs={"ticket_data": {...}},
    queue="TICKET_TASKS_PRODUCTION"
  )
  
Workflow Worker (consumes):
  @shared_task(name="tickets.tasks.receive_ticket")
  def receive_ticket(ticket_data):
      # Process ticket
      # Create workflow task
      # Assign to role
      pass

Workflow API → Notification:
  app.send_task(
    "task.send_assignment_notification",
    kwargs={"user_id": 1, "task_id": "T-123", ...},
    queue="notification-queue-default"
  )

Notification Worker (consumes):
  @shared_task(name="task.send_assignment_notification")
  def send_assignment_notification(user_id, task_id, ...):
      # Create notification
      # Send email
      pass
```

**Queue Routing**:
- Defined in `settings.py` via `CELERY_TASK_ROUTES`
- Tasks routed by name to specific queues
- Workers subscribe to specific queues

---

### Real-Time Communication (WebSocket)

**Protocol**: WebSocket (WS/WSS)  
**Framework**: Django Channels  
**Transport**: ASGI

**Connection Flow**:
```
Client → Messaging Service
  ws://messaging-service:8001/ws/comments/123/
  
  → connect()
  ← { "type": "connection_established", "ticket_id": 123 }
  
  → { "type": "ping", "timestamp": 1234567890 }
  ← { "type": "pong", "timestamp": 1234567890 }
  
  (Server broadcasts on comment create)
  ← { 
      "type": "comment_update", 
      "action": "create",
      "comment": { "id": 1, "text": "...", ... }
    }
```

**Channel Layers**:
- In-memory (development)
- Redis (production - future)
- Group-based broadcasting by ticket ID

---

## Technology Stack

### Backend Technologies

| Service | Framework | Version | Key Libraries |
|---------|-----------|---------|---------------|
| Auth | Django | 5.2.1 | DRF 3.16.0, SimpleJWT 5.5.0, django-cors-headers 4.7.0 |
| Workflow API | Django | 5.2.1 | Celery 5.5.3, django-filters 25.1, drf-spectacular 0.28.0 |
| Messaging | Django | 5.2.1 | Django Channels, asgiref 3.8.1 |
| Notification | Django | 5.2.1 | Celery 5.5.3, requests 2.32.4 |
| Ticket Service | Django | 5.2.1 | Celery 5.5.3 |

**Common Dependencies**:
- **python-decouple**: Environment variable management
- **dj-database-url**: Database URL parsing
- **psycopg2-binary**: PostgreSQL adapter
- **gunicorn**: WSGI HTTP Server
- **whitenoise**: Static file serving
- **Pillow**: Image processing
- **PyJWT**: JWT token handling
- **django-cors-headers**: CORS support

---

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.x | UI framework |
| Vite | Latest | Build tool and dev server |
| Axios | Latest | HTTP client |
| React Router | Latest | Client-side routing |
| WebSocket API | Native | Real-time communication |

---

### Infrastructure Technologies

| Component | Version | Purpose |
|-----------|---------|---------|
| RabbitMQ | 3-management | Message broker |
| PostgreSQL | 15 | Relational database |
| Docker | Latest | Containerization |
| Docker Compose | Latest | Multi-container orchestration |
| NGINX | Latest (prod) | Reverse proxy / Load balancer |

---

### Development Tools

- **drf-spectacular**: OpenAPI 3.0 schema generation
- **django-extensions**: Django shell enhancements
- **Faker**: Test data generation
- **pytest**: Testing framework (future)

---

## Deployment Architecture

### Docker Compose Deployment

**File**: `Docker/docker-compose.yml`

**Service Startup Order**:
```
1. rabbitmq (0s) - Message broker
2. db (0s) - PostgreSQL database
3. Auth Service (10s) - Authentication first
4. Workflow API (10s) - Core workflow engine
5. Messaging Service (10s) - Real-time messaging
6. Notification Service (10s) - Notification API
7. Ticket Service (10s) - Mock HDTS
8. Workflow Worker (20s) - Background job processing
9. Notification Worker (5s) - Notification processing
```

**Network Configuration**:
- Single Docker bridge network
- Service-to-service communication via service names
- Port exposure to host for external access

**Volume Mounts**:
- `rabbitmq_data` - RabbitMQ persistence
- `postgres_data` - PostgreSQL data
- `media_files` - Shared media files across services

---

### Production Deployment (Railway/Cloud)

**Environment Configuration**:
- `DJANGO_ENV=production`
- `DATABASE_URL` for managed PostgreSQL
- External RabbitMQ service (CloudAMQP)
- External Redis for channel layers
- CDN for static files

**Service Distribution**:
```
Load Balancer (NGINX/Cloud LB)
    ↓
  ┌─────┴──────┐
  │            │
Auth (×2)   Workflow API (×3)
  │            │
  └─────┬──────┘
        ↓
   Messaging (×2)
        ↓
   Notification (×2)
        ↓
   Workers (×N)
```

**Scaling Strategy**:
- Horizontal scaling for stateless services
- Database read replicas for heavy read loads
- Celery worker auto-scaling based on queue depth
- Redis cluster for WebSocket channel layer

---

## Scalability and Performance

### Performance Characteristics

**Expected Load**:
- 1000 concurrent users
- 10,000 tickets/day
- 100,000 API requests/day
- 50 concurrent WebSocket connections

**Response Times** (target):
- API endpoints: < 200ms (p95)
- WebSocket message delivery: < 100ms
- Background jobs: < 5s (p95)

---

### Scalability Strategies

1. **Stateless Services**: All API services are stateless, enabling horizontal scaling

2. **Message Queue**: RabbitMQ decouples services and enables async processing

3. **Database Optimization**:
   - Indexing on foreign keys and query fields
   - Connection pooling (600s max age)
   - Read replicas for reporting queries

4. **Caching** (Future):
   - Redis for session data
   - Redis for frequently accessed data (user profiles, roles)
   - CDN for static assets

5. **Load Balancing**:
   - Round-robin for HTTP requests
   - Sticky sessions for WebSocket connections

---

### Monitoring and Observability

**Logging**:
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Centralized logging with ELK stack (future)

**Metrics** (Future):
- Prometheus for metrics collection
- Grafana for visualization
- Key metrics: request rate, error rate, response time, queue depth

**Health Checks**:
- `/health/` endpoint on each service
- Database connectivity check
- RabbitMQ connectivity check

---

## Security Architecture

### Authentication & Authorization

1. **JWT Tokens**:
   - Access tokens: 15 minutes expiry
   - Refresh tokens: 1 day expiry
   - Token blacklisting on logout

2. **Role-Based Access Control (RBAC)**:
   - System-level roles (Admin, Agent, User)
   - Workflow-level roles (per workflow)
   - Permission checks at view level

3. **API Key Authentication**:
   - Notification service uses API keys
   - Key rotation supported

---

### Network Security

1. **CORS Configuration**:
   - Whitelist of allowed origins
   - Credentials support enabled
   - Pre-flight request handling

2. **HTTPS/TLS**:
   - Production uses HTTPS only
   - Secure cookies (HttpOnly, Secure flags)
   - CSRF protection enabled

3. **Rate Limiting**:
   - Per-IP rate limiting on auth endpoints
   - Per-user rate limiting on API endpoints

---

### Data Security

1. **Database Security**:
   - Password hashing (PBKDF2 with SHA256)
   - Database credentials in environment variables
   - Encrypted connections (SSL mode in production)

2. **Secret Management**:
   - Environment variables for secrets
   - No hardcoded credentials
   - Secret rotation procedures

3. **Input Validation**:
   - DRF serializers for validation
   - SQL injection prevention (ORM)
   - XSS prevention (template escaping)

---

## Disaster Recovery

### Backup Strategy

1. **Database Backups**:
   - Daily automated backups
   - Point-in-time recovery
   - 30-day retention

2. **Media File Backups**:
   - S3/object storage replication
   - Versioning enabled

3. **Configuration Backups**:
   - Infrastructure as Code (Docker Compose)
   - Environment variables documented

---

### High Availability

1. **Service Redundancy**:
   - Multiple instances per service
   - Health check-based failover
   - Auto-restart on failure

2. **Database**:
   - Master-replica setup
   - Automatic failover
   - Read replica for read-heavy loads

3. **Message Broker**:
   - RabbitMQ cluster (production)
   - Persistent messages
   - Queue mirroring

---

## Appendix

### Service URLs (Development)

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:1000 | User interface |
| Auth | http://localhost:8003 | Authentication API |
| Workflow API | http://localhost:8002 | Workflow management |
| Ticket Service | http://localhost:8004 | Mock HDTS |
| Messaging | http://localhost:8005 | WebSocket messaging |
| Notification | http://localhost:8006 | Notification API |
| RabbitMQ Mgmt | http://localhost:15672 | Queue management |
| PostgreSQL | localhost:5433 | Database |

---

### Service URLs (Production)

Defined via environment variables:
- `DJANGO_AUTH_SERVICE`
- `DJANGO_WORKFLOW_API`
- `DJANGO_NOTIFICATION_SERVICE`
- `DJANGO_MESSAGING_SERVICE`

---

### API Documentation

- Auth Service: http://localhost:8003/api/docs/
- Workflow API: http://localhost:8002/docs/
- Notification Service: http://localhost:8006/api/docs/

(Generated with drf-spectacular / Swagger UI)

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Maintained By**: System Architecture Team
