# System Architecture Documentation - Executive Summary

## Purpose
This document provides comprehensive answers to the system architecture questions, with references to detailed documentation in the `/docs` directory.

---

## A.1 System Architecture

### Overview
The Ticket Tracking System uses a **microservices architecture** with 5 Django backend services, 1 React frontend, PostgreSQL database, RabbitMQ message broker, and Celery workers for async processing.

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend: React 18.2 with Vite (Port 1000)                  │
└─────────────────────────────────────────────────────────────┘
                            ▼ HTTP/REST + JWT
┌─────────────────────────────────────────────────────────────┐
│ Backend Services (Django 5.x + DRF)                         │
│  • Auth Service (8000) - Authentication & Authorization     │
│  • Ticket Service (8004) - Ticket CRUD & File Management    │
│  • Workflow API (8002) - Workflow Orchestration             │
│  • Messaging (8005) - Comments & WebSocket                  │
│  • Notification (8006) - Async Notifications                │
└─────────────────────────────────────────────────────────────┘
           ▼                                ▼
┌──────────────────────┐      ┌────────────────────────┐
│ PostgreSQL 15        │      │ RabbitMQ 3 + Celery    │
│ (5 logical DBs)      │      │ (Message Queue)        │
└──────────────────────┘      └────────────────────────┘
```

### Key Technologies
- **Backend**: Django 5.x, Django REST Framework, Celery
- **Frontend**: React 18.2, Vite 7.1, Axios 1.11
- **Database**: PostgreSQL 15 (single instance, 5 logical databases)
- **Message Broker**: RabbitMQ 3 with AMQP protocol
- **Task Queue**: Celery with solo/prefork workers
- **Containerization**: Docker with Docker Compose
- **Authentication**: JWT (djangorestframework-simplejwt)

### Communication Protocols
- **Synchronous**: REST HTTP/JSON (Frontend ↔ Backend, Service ↔ Service)
- **Asynchronous**: AMQP via RabbitMQ (Background tasks, notifications)

### Deployment
- **Development**: Docker Compose with local volumes
- **Production**: Railway/Docker-compatible platforms with managed PostgreSQL
- **Orchestration**: Docker Compose (can migrate to Kubernetes)

**📖 Full Details**: [`/docs/A1_SYSTEM_ARCHITECTURE.md`](./A1_SYSTEM_ARCHITECTURE.md)

---

## A.2 Information Systems Integration

### Integration Architecture
**Pattern**: Hybrid (Synchronous HTTP + Asynchronous Message Queue)

### Integration Points

#### 1. Frontend ↔ Backend Services (HTTP/JSON)
```
Frontend (React) 
  → POST /api/v1/users/token/ (Auth Service) 
  → JWT tokens
  → Authenticated requests to all services
```

#### 2. Workflow API ↔ Auth Service (HTTP)
```
Workflow API needs user assignment
  → GET /api/v1/tts/roles/{role_id}/users/ (Auth Service)
  → User list with role
  → Round-robin assignment logic
```

#### 3. Ticket Service → Workflow API (Message Queue)
```
Ticket created in Ticket Service
  → Django signal triggers Celery task
  → RabbitMQ queue: TICKET_TASKS_PRODUCTION
  → Workflow Worker consumes task
  → Workflow API processes ticket
```

#### 4. Workflow API → Notification Service (Message Queue)
```
Task assigned in Workflow API
  → Enqueue notification task
  → RabbitMQ queue: notification-queue-default
  → Notification Worker consumes
  → Email sent via SMTP
```

### Data Transformation Example

**Ticket Service Model** → **Workflow API Model**:
```python
# Ticket Service
{
  "ticket_id": "TKT-2025-001",
  "category": "Technical Support",
  "priority": "high",
  "employee": {...}
}

# Transformed for Workflow API (adds workflow state)
{
  "ticket_id": "TKT-2025-001",
  "category": "Technical Support",  # Used for workflow matching
  "priority": "high",               # Used for workflow matching
  "is_task_allocated": False,       # Added by Workflow API
  "employee": {...}
}
```

### Integration Patterns
- **Service Discovery**: Docker DNS resolution by service name
- **Authentication**: Shared JWT secret key across services
- **Error Handling**: Celery retry with exponential backoff
- **Data Consistency**: Event-driven eventual consistency

**📖 Full Details**: [`/docs/A2_INFORMATION_SYSTEMS_INTEGRATION.md`](./A2_INFORMATION_SYSTEMS_INTEGRATION.md)

---

## A.3 Application Design and Development

### Software Design Patterns (10 Implemented)

1. **Microservices Architecture** - Independent, scalable services
2. **Repository Pattern** - Django ORM as abstraction layer
3. **Service Layer Pattern** - Business logic in service modules
4. **Observer Pattern** - Django signals for event-driven actions
5. **Factory Pattern** - DRF serializers for object creation
6. **Strategy Pattern** - Multiple authentication strategies (JWT, Session, API Key)
7. **Decorator Pattern** - Permission classes for access control
8. **Template Method Pattern** - Django generic views and ViewSets
9. **Adapter Pattern** - dj-database-url for DATABASE_URL parsing
10. **Publish-Subscribe Pattern** - RabbitMQ with Celery tasks

### Key Algorithms

#### 1. Round-Robin User Assignment
```
Input: role_id, task
1. Fetch users with role from Auth Service
2. Get current pointer for role (RoleRoundRobinPointer)
3. If pointer >= user_count, reset to 0
4. Assign to user at pointer index
5. Increment pointer
Output: Assigned user
Time: O(1) for pointer operations
```

#### 2. Workflow Matching
```
Input: ticket
1. Try exact match (category + subcategory + dept + priority)
2. Try match without priority
3. Try broad match (category + dept)
4. Try default workflow
5. Return None if no match
Output: Workflow or None
Time: O(log n) with DB indexes
```

#### 3. JWT Token Validation
```
Input: token_string
1. Decode JWT header
2. Verify signature with secret key
3. Check expiration (exp claim)
4. Extract user_id from payload
Output: user_id or exception
Time: O(1)
```

### Code Structure

**Backend (per Django service)**:
```
service_name/
├── manage.py
├── requirements.txt
├── service_name/
│   ├── settings.py      # Django configuration
│   ├── urls.py          # URL routing
│   └── celery.py        # Celery setup
├── app_name/
│   ├── models.py        # Database models
│   ├── views.py         # API endpoints
│   ├── serializers.py   # DRF serializers
│   ├── services.py      # Business logic
│   ├── tasks.py         # Celery tasks
│   └── tests.py         # Unit tests
```

**Frontend (React)**:
```
frontend/src/
├── api/                 # API integration
├── components/          # Reusable components
├── pages/               # Page components
├── routes/              # Routing
├── context/             # State management
├── hooks/               # Custom hooks
└── utils/               # Utilities
```

### Major Libraries & Frameworks

**Backend (60+ libraries)**:
- Django 5.x, Django REST Framework
- djangorestframework-simplejwt (JWT auth)
- Celery 5.x (task queue)
- psycopg2 (PostgreSQL driver)
- drf-spectacular (API docs)
- django-cors-headers (CORS)

**Frontend**:
- React 18.2, Vite 7.1
- axios 1.11 (HTTP client)
- react-router-dom 7.6 (routing)
- reactflow 11.11 (workflow diagrams)
- chart.js 4.5 (charts)

**📖 Full Details**: 
- [`/docs/A3_APPLICATION_DESIGN_AND_DEVELOPMENT.md`](./A3_APPLICATION_DESIGN_AND_DEVELOPMENT.md)
- [`/docs/A3_BACKEND_DESIGN_PATTERNS.md`](./A3_BACKEND_DESIGN_PATTERNS.md)

---

## A.5 Network Configuration

### Network Topology

```
Internet (HTTPS 443)
    ▼
Nginx Reverse Proxy (TLS termination)
    ▼
Docker Bridge Network (172.18.0.0/16)
    ├─► Auth Service (8000)
    ├─► Workflow API (8002)
    ├─► Ticket Service (8004)
    ├─► Messaging (8005)
    ├─► Notification (8006)
    ├─► PostgreSQL (5432)
    └─► RabbitMQ (5672 AMQP, 15672 Mgmt)
```

### Port Mapping

| Service | Container Port | Host Port | Public Access |
|---------|---------------|-----------|---------------|
| Frontend | 1000 | 1000 | Yes (via proxy) |
| Auth Service | 8000 | 8003 | Via load balancer |
| Workflow API | 8000 | 8002 | Via load balancer |
| Ticket Service | 7000 | 8004 | Via load balancer |
| PostgreSQL | 5432 | 5433 | Internal only |
| RabbitMQ AMQP | 5672 | 5672 | Internal only |
| RabbitMQ Mgmt | 15672 | 15672 | Dev only |

### Communication Protocols

1. **HTTP/HTTPS** (REST APIs)
   - Protocol: HTTP/1.1, HTTPS with TLS 1.2+
   - Format: JSON (application/json)
   - Auth: JWT Bearer tokens

2. **AMQP** (Message Queue)
   - Protocol: AMQP 0-9-1
   - Broker: RabbitMQ
   - Format: JSON (Celery serialization)
   - Reliability: Persistent, acknowledged

3. **PostgreSQL Wire Protocol**
   - Port: 5432
   - Connection pooling: 600s max age
   - Health checks: Enabled

4. **SSH** (Admin Access)
   - Port: 22
   - Key-based authentication only
   - Restricted to admin IP ranges

### Firewall Rules

**Incoming**:
- Port 80/443: Allow from 0.0.0.0/0 (HTTP/HTTPS)
- Port 22: Allow from admin IPs only (SSH)
- All other ports: Deny

**Internal (Docker Network)**:
- Services can communicate freely
- Database/RabbitMQ not exposed externally

### Security Configuration

**TLS/SSL**:
```nginx
# Nginx configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:...';
add_header Strict-Transport-Security "max-age=31536000";
```

**CORS**:
```python
CORS_ALLOWED_ORIGINS = [
    'https://ticketsystem.example.com',
    'http://localhost:1000'  # Development only
]
CORS_ALLOW_CREDENTIALS = True
```

**Rate Limiting**:
- **Nginx**: 10 req/s per IP
- **Django**: 5 login attempts/min per IP
- **Custom**: Device fingerprint tracking

**📖 Full Details**: [`/docs/A5_NETWORK_CONFIGURATION.md`](./A5_NETWORK_CONFIGURATION.md)

---

## A.10 APIs and Integration Points

### API Architecture
- **Pattern**: RESTful
- **Version**: v1 (URL: `/api/v1/`)
- **Authentication**: JWT Bearer tokens
- **Format**: JSON
- **Documentation**: OpenAPI/Swagger (available at `/api/docs/` in dev)

### Authentication Flow

```http
1. POST /api/v1/users/token/
   Body: {"username": "user@example.com", "password": "pass"}
   Response: {"access": "<jwt>", "refresh": "<jwt>", "user": {...}}

2. Use access token in subsequent requests:
   Authorization: Bearer <access_token>

3. Refresh when expired:
   POST /api/v1/users/token/refresh/
   Body: {"refresh": "<refresh_token>"}
   Response: {"access": "<new_access_token>"}
```

### Key Endpoints

#### Auth Service (8000)
- `POST /api/v1/users/token/` - Obtain JWT tokens
- `POST /api/v1/users/token/refresh/` - Refresh access token
- `GET /api/v1/users/profile/` - Get user profile
- `GET /api/v1/tts/roles/` - List roles
- `GET /api/v1/tts/roles/{role_id}/users/` - Get users by role

#### Ticket Service (8004)
- `GET /tickets/` - List tickets (paginated)
- `POST /tickets/` - Create ticket
- `GET /tickets/{id}/` - Get ticket details
- `PUT /tickets/{id}/` - Update ticket
- `DELETE /tickets/{id}/` - Delete ticket
- `POST /tickets/{id}/push_to_workflow/` - Trigger workflow

#### Workflow API (8002)
- `GET /workflows/` - List workflows
- `POST /workflows/` - Create workflow
- `GET /tasks/` - List user tasks
- `POST /tasks/{task_id}/action/` - Perform action
- `GET /tasks/{task_id}/available-actions/` - Get available actions
- `GET /transitions/` - Get workflow transitions

#### Notification Service (8006)
- `POST /notifications/` - Create notification (service-to-service)
- `GET /notifications/` - Get user notifications
- `PATCH /notifications/{id}/` - Mark as read

### Request/Response Examples

**Create Ticket**:
```http
POST /tickets/
Authorization: Bearer <token>
Content-Type: application/json

{
  "subject": "Login issue",
  "description": "Cannot access system",
  "category": "Technical Support",
  "priority": "high",
  "employee": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com"
  }
}

Response (201 Created):
{
  "id": 1,
  "ticket_id": "TKT-2025-0001",
  "subject": "Login issue",
  "status": "open",
  "created_at": "2025-11-19T10:00:00Z"
}
```

**Perform Task Action**:
```http
POST /tasks/uuid-task-1/action/
Authorization: Bearer <token>
Content-Type: application/json

{
  "action_id": "uuid-action-approve",
  "comment": "Approved. Moving to next step."
}

Response (200 OK):
{
  "status": "transitioned",
  "next_step": {
    "step_id": "uuid-step-2",
    "name": "Resolution",
    "assigned_to": "agent2@example.com"
  }
}
```

### HTTP Status Codes

**Success**:
- 200 OK - Successful GET, PUT, PATCH
- 201 Created - Successful POST
- 202 Accepted - Async processing accepted
- 204 No Content - Successful DELETE

**Client Errors**:
- 400 Bad Request - Validation error
- 401 Unauthorized - Missing/invalid auth
- 403 Forbidden - Lacks permission
- 404 Not Found - Resource not found
- 429 Too Many Requests - Rate limit

**Server Errors**:
- 500 Internal Server Error
- 502 Bad Gateway
- 503 Service Unavailable

### Integration Examples

**Python Client**:
```python
import requests

class TicketSystemClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.authenticate(username, password)
    
    def authenticate(self, username, password):
        response = requests.post(
            f"{self.base_url}/api/v1/users/token/",
            json={"username": username, "password": password}
        )
        self.token = response.json()['access']
    
    def create_ticket(self, subject, category, priority='medium'):
        response = requests.post(
            f"{self.base_url}/tickets/",
            headers={'Authorization': f'Bearer {self.token}'},
            json={'subject': subject, 'category': category, 'priority': priority}
        )
        return response.json()

# Usage
client = TicketSystemClient('http://localhost:8004', 'user@example.com', 'pass')
ticket = client.create_ticket('System slow', 'Technical Support', 'high')
```

**JavaScript Client**:
```javascript
import axios from 'axios';

class TicketSystemAPI {
  constructor(baseURL) {
    this.client = axios.create({ baseURL });
    this.client.interceptors.request.use(config => {
      const token = localStorage.getItem('access_token');
      if (token) config.headers.Authorization = `Bearer ${token}`;
      return config;
    });
  }
  
  async login(username, password) {
    const { data } = await this.client.post('/api/v1/users/token/', 
      { username, password });
    localStorage.setItem('access_token', data.access);
    return data;
  }
  
  async createTicket(ticketData) {
    const { data } = await this.client.post('/tickets/', ticketData);
    return data;
  }
}
```

### Rate Limiting

| Endpoint | Limit | Scope |
|----------|-------|-------|
| `/api/v1/users/token/` | 5/min | Per IP |
| `/tickets/` (POST) | 30/hour | Per user |
| All others | 60/min | Per user |

**📖 Full Details**: [`/docs/A10_APIS_AND_INTEGRATION_POINTS.md`](./A10_APIS_AND_INTEGRATION_POINTS.md)

---

## Documentation Navigation

### Quick Links
- **📖 Index**: [`/docs/README.md`](./README.md)
- **🏗️ A.1 System Architecture**: [`/docs/A1_SYSTEM_ARCHITECTURE.md`](./A1_SYSTEM_ARCHITECTURE.md)
- **🔗 A.2 Integration**: [`/docs/A2_INFORMATION_SYSTEMS_INTEGRATION.md`](./A2_INFORMATION_SYSTEMS_INTEGRATION.md)
- **💻 A.3 Application Design**: [`/docs/A3_APPLICATION_DESIGN_AND_DEVELOPMENT.md`](./A3_APPLICATION_DESIGN_AND_DEVELOPMENT.md)
- **⚙️ A.3 Backend Patterns**: [`/docs/A3_BACKEND_DESIGN_PATTERNS.md`](./A3_BACKEND_DESIGN_PATTERNS.md)
- **🌐 A.5 Network Config**: [`/docs/A5_NETWORK_CONFIGURATION.md`](./A5_NETWORK_CONFIGURATION.md)
- **📡 A.10 APIs**: [`/docs/A10_APIS_AND_INTEGRATION_POINTS.md`](./A10_APIS_AND_INTEGRATION_POINTS.md)

### By Role
- **System Architects**: A.1 → A.2 → A.5
- **Backend Developers**: A.3 → A.3 Backend → A.10
- **Frontend Developers**: A.10 → A.1
- **DevOps Engineers**: A.5 → A.1 → A.2
- **Integration Partners**: A.10 → A.2

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Total Documentation**: 196KB (6 documents + index)  
**Status**: ✅ Complete
