# A.1 System Architecture

## Overview

The Ticket Tracking System is a comprehensive enterprise platform built using a **microservices architecture** designed to manage and automate ticketing workflows for organizations. The system leverages modern technologies to provide scalability, maintainability, and high performance.

## Executive Summary

- **Architecture Pattern**: Microservices
- **Primary Technologies**: Django (Python), React (JavaScript), PostgreSQL, RabbitMQ, Celery
- **Deployment Strategy**: Docker containerization with Docker Compose orchestration
- **Communication Protocols**: REST HTTP/JSON (synchronous), AMQP via RabbitMQ (asynchronous)
- **Authentication**: JWT (JSON Web Tokens) with centralized auth service

## High-Level Architecture

The system consists of **5 Django backend microservices**, **1 React frontend application**, and **supporting infrastructure services** (database, message broker, task workers).

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │   React Application (Vite)                                     │  │
│  │   - Port: 1000                                                 │  │
│  │   - User Interface for Agents & Administrators                │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              ▼ HTTP/REST
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend Services Layer                          │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐                 │
│  │   Auth     │  │   Ticket    │  │  Workflow    │                 │
│  │  Service   │  │   Service   │  │     API      │                 │
│  │  (8000)    │  │   (8004)    │  │   (8002)     │                 │
│  └────────────┘  └─────────────┘  └──────────────┘                 │
│  ┌────────────┐  ┌─────────────┐                                   │
│  │ Messaging  │  │Notification │                                   │
│  │  Service   │  │   Service   │                                   │
│  │  (8005)    │  │   (8006)    │                                   │
│  └────────────┘  └─────────────┘                                   │
└─────────────────────────────────────────────────────────────────────┘
           ▼                           ▼
┌──────────────────────┐    ┌──────────────────────┐
│  PostgreSQL Database │    │   RabbitMQ Broker    │
│   (Multiple DBs)     │    │   AMQP: 5672         │
│   Port: 5432         │    │   Management: 15672  │
└──────────────────────┘    └──────────────────────┘
                                      ▼
                            ┌──────────────────────┐
                            │   Celery Workers     │
                            │  - workflow-worker   │
                            │  - notification-     │
                            │    worker            │
                            └──────────────────────┘
```

## Component Architecture

### 1. Frontend Service

**Technology Stack**: React 18.2, Vite 7.1, React Router 7.6

**Port**: 1000

**Responsibilities**:
- Single-page application (SPA) providing user interface
- Agent dashboard for ticket management
- Admin dashboard for system administration
- Real-time updates and notifications
- File upload and preview capabilities
- Workflow visualization and management

**Key Libraries**:
- `axios` (1.11.0) - HTTP client for REST API calls
- `react-router-dom` (7.6.2) - Client-side routing
- `reactflow` (11.11.4) - Workflow diagram visualization
- `chart.js` (4.5.0) - Dashboard charts and analytics
- `lucide-react` (0.523.0) - Icon library

**Build Configuration**:
- Build tool: Vite (ESBuild-based, optimized for speed)
- Development server: Hot module replacement (HMR)
- Production build: Optimized with tree-shaking and code splitting

### 2. Authentication Service (auth)

**Technology Stack**: Django 5.x, Django REST Framework, SimpleJWT

**Port**: 8000 (exposed as 8003 in Docker)

**Database**: PostgreSQL (`authservice` database)

**Responsibilities**:
- User authentication and authorization
- JWT token generation and validation
- Role-based access control (RBAC)
- System-specific role management (TTS, HDTS, AMS, BMS)
- User registration and invitation workflows
- Password management and OTP authentication
- Rate limiting and CAPTCHA for brute-force protection
- Session management

**Key Models**:
- `CustomUser` - Extended Django user model with profile data
- `UserSystemRole` - Links users to roles within specific systems
- `PendingRegistration` - Token-based invitation system
- `IPAddressRateLimit` - IP-based rate limiting
- `DeviceFingerprint` - Device-based rate limiting

**Authentication Flow**:
1. User submits credentials via `/api/v1/users/token/`
2. Rate limiting checks (IP and device fingerprint)
3. Credentials validated against database
4. JWT access and refresh tokens generated
5. Tokens returned to client with user metadata

**Security Features**:
- JWT token-based authentication
- Rate limiting (IP and device fingerprint)
- CAPTCHA integration after failed attempts
- OTP support for two-factor authentication
- Password complexity validation
- Session cookie security (configurable for HTTPS)

### 3. Ticket Service (ticket_service)

**Technology Stack**: Django 5.x, Django REST Framework, Celery

**Port**: 7000 (exposed as 8004 in Docker)

**Database**: PostgreSQL (`ticketmanagement` database)

**Responsibilities**:
- Ticket CRUD operations (Create, Read, Update, Delete)
- File attachment management
- Ticket metadata and categorization
- Archive management
- Asynchronous workflow triggering via Celery
- Media file storage and retrieval

**Key Models**:
- `Ticket` - Main ticket entity with comprehensive metadata
  - Fields: ticket_id, subject, description, category, subcategory, priority, status, department, assigned_to
  - JSON fields: employee data, attachments list
  - Timestamps: created_at, updated_at

**API Endpoints**:
- `GET/POST /tickets/` - List and create tickets
- `GET/PUT/DELETE /tickets/{id}/` - Retrieve, update, delete specific ticket
- `POST /send/` - Alternative ticket creation endpoint

**Integration Points**:
- **Signal-based**: After ticket creation, signals trigger Celery tasks to push ticket data to workflow service
- **Message Queue**: Publishes to `TICKET_TASKS_PRODUCTION` queue for workflow processing

### 4. Workflow API (workflow_api)

**Technology Stack**: Django 5.x, Django REST Framework, Celery

**Port**: 8000 (exposed as 8002 in Docker)

**Database**: PostgreSQL (`workflowmanagement` database)

**Responsibilities**:
- Workflow definition and management
- Workflow step orchestration
- Task allocation and assignment (round-robin)
- Step transition logic
- Action logging and audit trails
- Ticket status synchronization
- User assignment notifications

**Key Models**:
- `Workflows` - Workflow definitions with SLA configurations
- `Steps` - Individual workflow steps with role assignments
- `StepTransition` - Defines allowed transitions between steps
- `Task` - Represents a ticket in workflow processing
- `StepInstance` - Tracks user actions on workflow steps
- `ActionLog` - Audit trail of all workflow actions
- `WorkflowTicket` - Mirror of ticket data for workflow processing
- `Category` - Hierarchical category structure
- `RoleRoundRobinPointer` - Tracks round-robin assignment state

**Workflow Execution Flow**:
1. Ticket created in ticket service
2. Celery task enqueued to `TICKET_TASKS_PRODUCTION`
3. Workflow worker consumes task
4. Workflow matched based on category/subcategory/department/priority
5. Initial step assigned to role (round-robin algorithm)
6. Notification sent to assigned user
7. Step instances created for tracking
8. User actions logged to ActionLog

**Round-Robin Assignment Algorithm**:
- `RoleRoundRobinPointer` maintains a pointer for each role
- Fetches users with specific role from auth service
- Assigns to next user in rotation
- Updates pointer for next assignment
- Handles edge cases (no users, invalid pointer)

### 5. Messaging Service (messaging)

**Technology Stack**: Django 5.x, WebSockets (planned/partial), Django Channels (potential)

**Port**: 8001 (exposed as 8005 in Docker)

**Database**: PostgreSQL (`messagingservice` database)

**Responsibilities**:
- Real-time messaging between users
- Ticket comments and discussions
- WebSocket connections for live updates
- Media URL management for embedded content

**Key Features**:
- Comment threading on tickets
- Real-time message delivery
- File attachment support in messages
- CORS configured for WebSocket connections

### 6. Notification Service (notification_service)

**Technology Stack**: Django 5.x, Celery, Email backends

**Port**: 8001 (exposed as 8006 in Docker)

**Database**: PostgreSQL (`notificationservice` database) - optional, primarily uses Celery

**Responsibilities**:
- Asynchronous notification delivery
- Email notifications (SMTP)
- In-app notification creation
- Notification templates and formatting
- API-key based authentication for service-to-service calls

**Celery Queues**:
- `notification-queue-default` - General notifications
- `inapp-notification-queue` - In-app notifications

**Notification Types**:
- Assignment notifications (when ticket/task assigned)
- Status change notifications
- Escalation notifications
- System notifications

**Integration**:
- Auth service for user data lookup
- Email backend configurable (console for dev, SMTP for production)
- JWT shared secret for secure service-to-service communication

## Infrastructure Services

### PostgreSQL Database

**Image**: postgres:15

**Port**: 5432 (exposed as 5433 in Docker to avoid conflicts)

**Architecture**: Single PostgreSQL instance with **multiple logical databases**

**Databases**:
- `authservice` - Auth service data
- `ticketmanagement` - Ticket service data
- `workflowmanagement` - Workflow API data
- `messagingservice` - Messaging service data
- `notificationservice` - Notification service data (optional)

**Configuration**:
- Persistent volume: `postgres_data`
- Initialization scripts: `/docker-entrypoint-initdb.d` (in `Docker/db-init/`)
- Connection pooling: Managed by Django (600s max age, health checks enabled)

**Connection Strategy**:
- **Priority 1**: Use `DATABASE_URL` environment variable (Railway, managed services)
- **Priority 2**: Production with `DJANGO_ENV=production` uses individual PostgreSQL variables
- **Fallback**: Development uses SQLite (`db.sqlite3`)

### RabbitMQ Message Broker

**Image**: rabbitmq:3-management

**Ports**:
- 5672 - AMQP protocol
- 15672 - Management UI

**Credentials** (default):
- Username: `admin`
- Password: `admin`

**Purpose**:
- Message queuing for asynchronous task processing
- Decouples services for better scalability
- Ensures reliable task delivery with acknowledgments
- Supports multiple queues for different task types

**Queues Used**:
- `TICKET_TASKS_PRODUCTION` - Ticket processing tasks
- `notification-queue-default` - Email/general notifications
- `inapp-notification-queue` - In-app notifications
- `ticket_status-default` - Ticket status updates
- `role_send-default` - Role-related tasks
- `tts.role.sync` - TTS role synchronization
- `tts.user_system_role.sync` - User role synchronization
- `workflow_seed_queue` - Workflow seeding tasks

**Configuration**:
- Persistent volume: `rabbitmq_data`
- Management UI accessible at `http://localhost:15672`

### Celery Workers

**Type**: Distributed task queue system

**Workers**:

1. **workflow-worker**
   - Based on workflow_api service
   - Queues: `role_send-default`, `TICKET_TASKS_PRODUCTION`, `tts.role.sync`, `tts.user_system_role.sync`, `workflow_seed_queue`, `workflow_seed`
   - Pool: Solo (single-threaded for compatibility)
   - Startup delay: 20 seconds (waits for RabbitMQ and DB)

2. **notification-worker**
   - Based on notification_service
   - Queues: `notification-queue-default`, `inapp-notification-queue`
   - Pool: Default (prefork)
   - Startup delay: 5 seconds

**Task Serialization**: JSON

**Broker URL**: `amqp://admin:admin@rabbitmq:5672/`

**Execution Model**:
- Tasks published by services
- Workers poll queues
- Acknowledgment on successful completion
- Retry logic for failed tasks (configurable)

## Communication Protocols

### Synchronous Communication (REST HTTP/JSON)

**Protocol**: HTTP/1.1 over TCP

**Format**: JSON (application/json)

**Authentication**: JWT Bearer tokens in Authorization header

**Service Discovery**:
- Docker network DNS resolution
- Environment variables for service URLs
- Examples:
  - `DJANGO_AUTH_SERVICE=http://auth-service:8000`
  - `DJANGO_USER_SERVICE=http://auth-service:8000`

**Inter-Service REST Calls**:
- Workflow API → Auth Service: User and role lookups
- Services → Notification Service: Trigger notifications via API

**REST API Design**:
- RESTful resource-based URLs
- Standard HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Status codes: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 500 (Server Error)
- Pagination for list endpoints (page, perPage parameters)

### Asynchronous Communication (AMQP via RabbitMQ)

**Protocol**: AMQP 0-9-1

**Message Format**: JSON (Celery serialized)

**Reliability**:
- Message persistence
- Acknowledgments (acks-late strategy)
- Dead letter exchanges for failed tasks

**Task Routing**:
- Configured in Django settings: `CELERY_TASK_ROUTES`
- Tasks sent with `app.send_task(task_name, kwargs={...}, queue='queue_name')`

**Example Task Flow**:
```
ticket_service (create ticket) 
  → enqueue push_ticket_to_workflow.delay(data) 
  → RabbitMQ (TICKET_TASKS_PRODUCTION queue)
  → workflow-worker consumes 
  → workflow_api.process_ticket(data)
```

## Technology Stack Details

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Web Framework | Django | 5.x | Core framework for all services |
| API Framework | Django REST Framework | Latest | RESTful API development |
| Authentication | djangorestframework-simplejwt | Latest | JWT token handling |
| Task Queue | Celery | Latest | Asynchronous task processing |
| Message Broker | RabbitMQ | 3-management | Message queuing |
| Database ORM | Django ORM | 5.x | Object-relational mapping |
| Database Driver | psycopg2 | Latest | PostgreSQL adapter |
| CORS | django-cors-headers | Latest | Cross-origin resource sharing |
| Environment Config | python-decouple | Latest | Environment variable management |
| Database URL Parser | dj-database-url | Latest | Database URL parsing |
| API Documentation | drf-spectacular | Latest | OpenAPI/Swagger docs |
| Rate Limiting | django-ratelimit | Latest | Request rate limiting |
| CAPTCHA | django-simple-captcha | Latest | CAPTCHA for forms |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| UI Framework | React | 18.2.0 | Component-based UI |
| Build Tool | Vite | 7.1.3 | Fast dev server and bundler |
| Routing | react-router-dom | 7.6.2 | Client-side routing |
| HTTP Client | axios | 1.11.0 | API communication |
| State Management | React Context | Built-in | Global state |
| Charts | chart.js + react-chartjs-2 | 4.5.0 / 5.3.0 | Data visualization |
| Workflow Diagrams | reactflow | 11.11.4 | Workflow visualization |
| Icons | lucide-react | 0.523.0 | Icon library |
| Date Handling | dayjs / date-fns | Latest | Date utilities |
| UUID Generation | uuid | 11.1.0 | Unique identifiers |

### Infrastructure

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Database | PostgreSQL | 15 | Relational data storage |
| Containerization | Docker | Latest | Application containers |
| Orchestration | Docker Compose | Latest | Multi-container apps |
| Web Server (Production) | Gunicorn | Latest | WSGI HTTP server |
| Reverse Proxy (Optional) | Nginx | Latest | Load balancing, SSL |

## Deployment Architecture

### Docker Compose Structure

**File**: `Docker/docker-compose.yml`

**Services Defined**:
1. `rabbitmq` - Message broker
2. `db` (PostgreSQL) - Database server
3. `auth-service` - Authentication microservice
4. `ticket-service` - Ticket management microservice
5. `workflow-api` - Workflow orchestration microservice
6. `messaging-service` - Messaging microservice
7. `notification-service` - Notification API microservice
8. `workflow-worker` - Celery worker for workflows
9. `notification-worker` - Celery worker for notifications
10. `frontend` - React application (commented out, typically run separately)

**Network**:
- Default bridge network
- Service discovery via Docker DNS
- Services communicate using service names (e.g., `http://auth-service:8000`)

**Volumes**:
- `postgres_data` - Persistent database storage
- `rabbitmq_data` - Persistent message queue data
- `media_files` - Shared media files across services

**Startup Order**:
- RabbitMQ and PostgreSQL start first (no delay)
- Services start with delays (10-20 seconds) to ensure dependencies are ready
- Workers start last (15-20 seconds delay)

### Environment Configuration

**Pattern**: Each service has:
- `.env.example` - Template with all variables
- `.env` - Actual configuration (not committed to Git)

**Standardization**: All services use `DJANGO_` prefix for core settings

**Key Variables**:
- `DJANGO_ENV` - Environment (development/production)
- `DJANGO_DEBUG` - Debug mode
- `DJANGO_SECRET_KEY` - Django secret key
- `DJANGO_ALLOWED_HOSTS` - Allowed hostnames
- `DATABASE_URL` - PostgreSQL connection string
- `DJANGO_CELERY_BROKER_URL` - RabbitMQ connection
- `DJANGO_CORS_ALLOWED_ORIGINS` - CORS configuration

### Production Deployment

**Supported Platforms**:
- Railway (documented in `auth/RAILWAY_DEPLOYMENT.md`)
- Any Docker-compatible platform
- Kubernetes (requires manifest creation)

**Production Considerations**:
1. Set `DJANGO_ENV=production`
2. Use strong `DJANGO_SECRET_KEY`
3. Configure `DATABASE_URL` for managed databases
4. Set proper `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
5. Use SMTP for email (not console backend)
6. Enable HTTPS and secure cookies
7. Configure proper logging and monitoring
8. Use production-grade web servers (Gunicorn + Nginx)

## Data Flow Examples

### Example 1: User Login

```
1. Frontend → POST /api/v1/users/token/ (Auth Service)
2. Auth Service:
   a. Check rate limits (IP + device fingerprint)
   b. Validate credentials
   c. Generate JWT tokens
   d. Return tokens + user metadata
3. Frontend stores tokens in localStorage
4. Frontend redirects to dashboard
```

### Example 2: Ticket Creation and Workflow Processing

```
1. Frontend → POST /tickets/ (Ticket Service)
2. Ticket Service:
   a. Validate ticket data
   b. Save to database (ticketmanagement.Ticket)
   c. Post-save signal triggers Celery task
   d. Enqueue push_ticket_to_workflow.delay(ticket_data)
   e. Return 201 Created with ticket ID
3. RabbitMQ receives task in TICKET_TASKS_PRODUCTION queue
4. workflow-worker consumes task
5. Workflow API:
   a. Receive ticket data
   b. Save to WorkflowTicket model
   c. Match workflow (category/subcategory/department/priority)
   d. Identify initial step and role
   e. Query Auth Service for users with role (round-robin)
   f. Assign task to user
   g. Create Task and StepInstance records
   h. Enqueue notification task
6. notification-worker consumes notification task
7. Notification Service:
   a. Generate notification message
   b. Send email via SMTP
   c. Create in-app notification
8. Frontend polls/receives notification
```

### Example 3: Workflow Step Transition

```
1. Frontend → POST /tasks/{task_id}/action/ (Workflow API)
   Body: { action_id: "approve", comment: "Looks good" }
2. Workflow API:
   a. Validate user has active StepInstance for task
   b. Lookup StepTransition for current step + action
   c. Mark current StepInstance as has_acted=True
   d. Create ActionLog entry
   e. If transition exists:
      - Move to next step
      - Assign to next role (round-robin)
      - Create new StepInstance
      - Enqueue assignment notification
   f. If no transition (end logic):
      - Mark task as completed
      - Update ticket status
   g. Return 200 OK with transition result
3. Notification flow (same as Example 2, step 6-8)
```

## Scalability Considerations

### Horizontal Scaling

**Services**: Each Django service can be scaled independently
- Deploy multiple instances behind a load balancer
- Stateless design (no in-memory session state)
- JWT tokens enable distributed authentication

**Workers**: Celery workers can be scaled horizontally
- Add more worker containers/processes
- Queues distribute tasks automatically
- No code changes required

**Database**: PostgreSQL can be scaled with:
- Read replicas for read-heavy operations
- Connection pooling (PgBouncer)
- Partitioning for large tables

### Vertical Scaling

- Increase CPU/RAM for compute-intensive services (Workflow API)
- Optimize database with indexes and query tuning
- Use caching (Redis) for frequently accessed data

## Security Architecture

### Authentication & Authorization

- JWT-based authentication (stateless)
- Role-based access control (RBAC)
- System-specific role assignments
- Token expiration and refresh mechanisms

### Network Security

- Services isolated in Docker network
- CORS restrictions on frontend-backend communication
- Rate limiting to prevent abuse
- CAPTCHA for brute-force protection
- IP and device fingerprinting

### Data Security

- Database credentials via environment variables (never hardcoded)
- Secrets managed outside codebase
- HTTPS enforcement in production
- Secure cookie flags (SECURE, HTTPONLY, SAMESITE)
- SQL injection protection (Django ORM)

### API Security

- JWT token validation on all protected endpoints
- Permission classes (IsAuthenticated, custom permissions)
- API key authentication for service-to-service calls (Notification Service)
- Input validation and sanitization

## Monitoring & Observability

### Logging

- Django logging framework
- Celery task logging
- Database query logging (development)
- Application logs to stdout (Docker best practice)

### Health Checks

- Django health check endpoints (can be added)
- Database connection health checks
- Celery worker monitoring via Flower (can be added)

### Metrics (Future Enhancement)

- Prometheus for metrics collection
- Grafana for visualization
- APM tools (New Relic, DataDog)

## Architecture Diagrams

### Component Diagram

See `architecture/component_diagram.puml` for detailed component relationships.

### Sequence Diagrams

- `architecture/sequence_ticket_creation.puml` - Ticket creation flow
- `architecture/sequence_notification.puml` - Notification delivery flow

### Class Diagrams

- `architecture/class_diagram_backend.puml` - Django models
- `architecture/class_diagram_models.puml` - Model relationships

### Use Case Diagram

See `architecture/use_cases.puml` for user interactions.

## Future Enhancements

### Short Term
- Add Redis for caching
- Implement WebSocket support in messaging service
- Add comprehensive logging and monitoring
- Implement API versioning
- Add rate limiting middleware

### Long Term
- Migrate to Kubernetes for orchestration
- Implement event sourcing for audit trails
- Add GraphQL API layer
- Implement CQRS pattern for read/write separation
- Add machine learning for ticket categorization
- Implement full-text search (Elasticsearch)

## References

- **Main README**: `/ReadMe.md`
- **Environment Standardization**: `/ENVIRONMENT_STANDARDIZATION_REPORT.md`
- **Rate Limiting Implementation**: `/RATE_LIMITING_IMPLEMENTATION.md`
- **System URL Configuration**: `/auth/SYSTEM_URL_CONFIG.md`
- **Railway Deployment Guide**: `/auth/RAILWAY_DEPLOYMENT.md`
- **Docker Compose**: `/Docker/docker-compose.yml`
- **Architecture Diagrams**: `/architecture/*.puml`

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Authors**: System Architecture Team
