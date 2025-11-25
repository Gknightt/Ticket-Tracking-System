# A.10 APIs and Integration Points

## Overview

This document provides comprehensive API documentation for the Ticket Tracking System, including all endpoints, request/response specifications, authentication requirements, error codes, and integration patterns for external systems.

## API Architecture

### RESTful Design Principles

The system follows REST (Representational State Transfer) architectural constraints:

- **Client-Server**: Separation of concerns between UI and backend
- **Stateless**: Each request contains all information needed (JWT tokens)
- **Cacheable**: Responses indicate cacheability
- **Uniform Interface**: Consistent URL structure and HTTP methods
- **Layered System**: API gateway, service layer, data layer

### API Versioning

**Current Version**: v1

**URL Structure**: `/api/v1/<resource>/`

**Future Versioning Strategy**:
- Breaking changes require new version (v2, v3, etc.)
- Non-breaking changes deployed to existing version
- Deprecation notices given 6 months before version removal

## Authentication

### JWT (JSON Web Token) Authentication

**Token Acquisition**:

```http
POST /api/v1/users/token/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "securepassword"
}
```

**Response**:

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6InVzZXJAZXhhbXBsZS5jb20iLCJleHAiOjE3MzIwMjAwMDB9.signature",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MzI2MjQ4MDB9.signature",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": {
      "id": 5,
      "name": "Agent"
    }
  }
}
```

**Using Access Token**:

```http
GET /api/v1/tickets/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token Refresh**:

```http
POST /api/v1/users/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Token Expiration**:
- Access Token: 1 hour
- Refresh Token: 7 days

### API Key Authentication (Service-to-Service)

**Header**: `X-API-Key`

**Usage**:

```http
GET /api/notifications/
X-API-Key: demo-api-key-123
```

**Applicable Services**: Notification Service

## Auth Service API

**Base URL**: `http://auth-service:8000/api/v1/`

### User Endpoints

#### 1. Obtain JWT Token

```http
POST /users/token/
```

**Request Body**:
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response** (200 OK):
```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

**Errors**:
- `401 Unauthorized`: Invalid credentials
- `429 Too Many Requests`: Rate limit exceeded

#### 2. Refresh Access Token

```http
POST /users/token/refresh/
```

**Request Body**:
```json
{
  "refresh": "<jwt_refresh_token>"
}
```

**Response** (200 OK):
```json
{
  "access": "<new_jwt_access_token>"
}
```

#### 3. Get User Profile

```http
GET /users/profile/
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "id": 1,
  "username": "user@example.com",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "role": {
    "id": 5,
    "name": "Agent"
  },
  "systems": ["TTS", "HDTS"]
}
```

#### 4. Update Profile

```http
PUT /users/profile/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Smith",
  "phone_number": "+0987654321"
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "first_name": "Jane",
  "last_name": "Smith",
  "phone_number": "+0987654321"
}
```

#### 5. Change Password

```http
POST /users/change-password/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "oldpass123",
  "new_password": "newpass456"
}
```

**Response** (200 OK):
```json
{
  "message": "Password changed successfully"
}
```

**Errors**:
- `400 Bad Request`: Old password incorrect or new password too weak

### Role Management Endpoints

#### 6. List Roles

```http
GET /tts/roles/
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "count": 5,
  "results": [
    {
      "role_id": "uuid-role-1",
      "name": "L1 Support",
      "description": "Level 1 support agents"
    },
    {
      "role_id": "uuid-role-2",
      "name": "L2 Support",
      "description": "Level 2 support agents"
    }
  ]
}
```

#### 7. Get Users by Role

```http
GET /tts/roles/{role_id}/users/
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "role": {
    "role_id": "uuid-role-1",
    "name": "L1 Support"
  },
  "users": [
    {
      "id": 5,
      "username": "agent1",
      "email": "agent1@example.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    {
      "id": 7,
      "username": "agent2",
      "email": "agent2@example.com",
      "first_name": "Jane",
      "last_name": "Smith"
    }
  ]
}
```

## Ticket Service API

**Base URL**: `http://ticket-service:8004/`

### Ticket Endpoints

#### 1. List Tickets

```http
GET /tickets/?page=1&page_size=50&status=open&priority=high
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `page` (int): Page number (default: 1)
- `page_size` (int): Results per page (default: 50, max: 100)
- `status` (string): Filter by status (open, closed, assigned, etc.)
- `priority` (string): Filter by priority (low, medium, high, urgent)
- `category` (string): Filter by category
- `assigned_to` (string): Filter by assignee email
- `search` (string): Search in subject and description

**Response** (200 OK):
```json
{
  "count": 150,
  "next": "http://ticket-service:8004/tickets/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "ticket_id": "TKT-2025-0001",
      "subject": "Login issue",
      "description": "Cannot access the system",
      "category": "Technical Support",
      "subcategory": "Authentication",
      "department": "IT",
      "priority": "high",
      "status": "open",
      "assigned_to": "agent1@example.com",
      "employee": {
        "id": 123,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "department": "Sales"
      },
      "attachments": [
        {
          "filename": "screenshot.png",
          "url": "/media/attachments/screenshot.png",
          "size": 45678
        }
      ],
      "created_at": "2025-11-19T10:00:00Z",
      "updated_at": "2025-11-19T10:30:00Z"
    }
  ]
}
```

#### 2. Create Ticket

```http
POST /tickets/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "subject": "System performance issue",
  "description": "Application is running slowly",
  "category": "Technical Support",
  "subcategory": "Performance",
  "department": "IT",
  "priority": "medium",
  "employee": {
    "id": 456,
    "name": "Jane Smith",
    "email": "jane.smith@example.com",
    "department": "Marketing"
  },
  "attachments": []
}
```

**Response** (201 Created):
```json
{
  "id": 2,
  "ticket_id": "TKT-2025-0002",
  "subject": "System performance issue",
  "status": "open",
  "created_at": "2025-11-19T11:00:00Z"
}
```

**Errors**:
- `400 Bad Request`: Validation errors
  ```json
  {
    "subject": ["This field is required"],
    "priority": ["Invalid priority value"]
  }
  ```

#### 3. Get Ticket Details

```http
GET /tickets/{id}/
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "id": 1,
  "ticket_id": "TKT-2025-0001",
  "subject": "Login issue",
  "description": "Cannot access the system",
  "category": "Technical Support",
  "subcategory": "Authentication",
  "department": "IT",
  "priority": "high",
  "status": "open",
  "assigned_to": "agent1@example.com",
  "employee": {
    "id": 123,
    "name": "John Doe",
    "email": "john.doe@example.com"
  },
  "attachments": [],
  "created_at": "2025-11-19T10:00:00Z",
  "updated_at": "2025-11-19T10:30:00Z"
}
```

**Errors**:
- `404 Not Found`: Ticket does not exist

#### 4. Update Ticket

```http
PUT /tickets/{id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "in_progress",
  "priority": "urgent",
  "assigned_to": "agent2@example.com"
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "ticket_id": "TKT-2025-0001",
  "status": "in_progress",
  "priority": "urgent",
  "assigned_to": "agent2@example.com",
  "updated_at": "2025-11-19T12:00:00Z"
}
```

#### 5. Delete Ticket

```http
DELETE /tickets/{id}/
Authorization: Bearer <access_token>
```

**Response** (204 No Content)

**Errors**:
- `403 Forbidden`: User lacks permission to delete
- `404 Not Found`: Ticket does not exist

#### 6. Push Ticket to Workflow

```http
POST /tickets/{id}/push_to_workflow/
Authorization: Bearer <access_token>
```

**Response** (202 Accepted):
```json
{
  "message": "Ticket TKT-2025-0001 enqueued for workflow push."
}
```

## Workflow API

**Base URL**: `http://workflow-api:8002/`

### Workflow Endpoints

#### 1. List Workflows

```http
GET /workflows/?is_published=true&category=Technical+Support
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `is_published` (boolean): Filter by publish status
- `category` (string): Filter by category
- `department` (string): Filter by department

**Response** (200 OK):
```json
{
  "count": 10,
  "results": [
    {
      "workflow_id": "uuid-workflow-1",
      "name": "Standard IT Support Workflow",
      "description": "3-step workflow for IT support tickets",
      "category": "Technical Support",
      "subcategory": "General",
      "department": "IT",
      "is_published": true,
      "status": "active",
      "steps": [
        {
          "step_id": "uuid-step-1",
          "name": "Initial Assessment",
          "order": 1,
          "role": {
            "role_id": "uuid-role-1",
            "name": "L1 Support"
          }
        },
        {
          "step_id": "uuid-step-2",
          "name": "Resolution",
          "order": 2,
          "role": {
            "role_id": "uuid-role-2",
            "name": "L2 Support"
          }
        }
      ],
      "sla": {
        "low": "P2D",
        "medium": "P1D",
        "high": "PT8H",
        "urgent": "PT4H"
      }
    }
  ]
}
```

#### 2. Create Workflow

```http
POST /workflows/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "New Support Workflow",
  "description": "Custom workflow for specific category",
  "category": "Technical Support",
  "subcategory": "Hardware",
  "department": "IT",
  "is_published": false,
  "steps": [
    {
      "name": "Triage",
      "description": "Initial ticket triage",
      "order": 1,
      "role_id": "uuid-role-1",
      "instruction": "Review ticket and categorize"
    },
    {
      "name": "Resolve",
      "description": "Fix the issue",
      "order": 2,
      "role_id": "uuid-role-2",
      "instruction": "Implement solution"
    }
  ]
}
```

**Response** (201 Created):
```json
{
  "workflow_id": "uuid-workflow-new",
  "name": "New Support Workflow",
  "is_published": false,
  "created_at": "2025-11-19T12:00:00Z"
}
```

### Task Endpoints

#### 3. List User Tasks

```http
GET /tasks/?status=pending&user_id=5
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `status` (string): Filter by task status (pending, completed)
- `user_id` (int): Filter by assigned user
- `workflow_id` (string): Filter by workflow

**Response** (200 OK):
```json
{
  "count": 15,
  "results": [
    {
      "task_id": "uuid-task-1",
      "ticket": {
        "ticket_id": "TKT-2025-0001",
        "subject": "Login issue",
        "priority": "high"
      },
      "workflow": {
        "workflow_id": "uuid-workflow-1",
        "name": "Standard IT Support Workflow"
      },
      "current_step": {
        "step_id": "uuid-step-1",
        "name": "Initial Assessment"
      },
      "assigned_to": "agent1@example.com",
      "status": "pending",
      "created_at": "2025-11-19T10:00:00Z"
    }
  ]
}
```

#### 4. Perform Task Action

```http
POST /tasks/{task_id}/action/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "action_id": "uuid-action-approve",
  "comment": "Reviewed and approved. Moving to next step."
}
```

**Response** (200 OK):
```json
{
  "status": "transitioned",
  "message": "Task moved to next step",
  "next_step": {
    "step_id": "uuid-step-2",
    "name": "Resolution",
    "assigned_to": "agent2@example.com"
  },
  "action_log": {
    "action_log_id": "uuid-log-1",
    "action": "approve",
    "user": "agent1@example.com",
    "comment": "Reviewed and approved. Moving to next step.",
    "timestamp": "2025-11-19T13:00:00Z"
  }
}
```

**Errors**:
- `400 Bad Request`: Invalid action or missing required fields
- `403 Forbidden`: User not assigned to this task
- `404 Not Found`: Task or action not found

#### 5. Get Available Actions

```http
GET /tasks/{task_id}/available-actions/
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "task_id": "uuid-task-1",
  "current_step": "Initial Assessment",
  "available_actions": [
    {
      "action_id": "uuid-action-approve",
      "name": "Approve",
      "description": "Approve and move to next step"
    },
    {
      "action_id": "uuid-action-reject",
      "name": "Reject",
      "description": "Reject and close ticket"
    },
    {
      "action_id": "uuid-action-escalate",
      "name": "Escalate",
      "description": "Escalate to senior agent"
    }
  ]
}
```

### Step Transition Endpoints

#### 6. Get Transitions

```http
GET /transitions/?workflow_id=uuid-workflow-1
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "count": 3,
  "results": [
    {
      "transition_id": "uuid-trans-1",
      "workflow_id": "uuid-workflow-1",
      "from_step": {
        "step_id": "uuid-step-1",
        "name": "Initial Assessment"
      },
      "to_step": {
        "step_id": "uuid-step-2",
        "name": "Resolution"
      },
      "action": {
        "action_id": "uuid-action-approve",
        "name": "Approve"
      }
    }
  ]
}
```

## Notification Service API

**Base URL**: `http://notification-service:8006/`

### Notification Endpoints

#### 1. Create Notification (Service-to-Service)

```http
POST /notifications/
X-API-Key: demo-api-key-123
Content-Type: application/json

{
  "user_id": 5,
  "user_email": "agent1@example.com",
  "type": "assignment",
  "subject": "New Task Assigned",
  "message": "You have been assigned task TKT-2025-0001",
  "metadata": {
    "task_id": "uuid-task-1",
    "ticket_id": "TKT-2025-0001"
  }
}
```

**Response** (201 Created):
```json
{
  "notification_id": "uuid-notif-1",
  "status": "sent",
  "timestamp": "2025-11-19T14:00:00Z"
}
```

#### 2. Get User Notifications

```http
GET /notifications/?user_id=5&is_read=false
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "count": 5,
  "results": [
    {
      "notification_id": "uuid-notif-1",
      "type": "assignment",
      "subject": "New Task Assigned",
      "message": "You have been assigned task TKT-2025-0001",
      "is_read": false,
      "created_at": "2025-11-19T14:00:00Z"
    }
  ]
}
```

#### 3. Mark Notification as Read

```http
PATCH /notifications/{notification_id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "is_read": true
}
```

**Response** (200 OK):
```json
{
  "notification_id": "uuid-notif-1",
  "is_read": true,
  "read_at": "2025-11-19T15:00:00Z"
}
```

## HTTP Status Codes

### Success Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST (resource created) |
| 202 | Accepted | Request accepted for async processing |
| 204 | No Content | Successful DELETE |

### Client Error Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 400 | Bad Request | Validation error, malformed request |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but lacks permission |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource conflict (duplicate, etc.) |
| 422 | Unprocessable Entity | Semantic error in request |
| 429 | Too Many Requests | Rate limit exceeded |

### Server Error Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 500 | Internal Server Error | Server-side error |
| 502 | Bad Gateway | Upstream service unavailable |
| 503 | Service Unavailable | Service temporarily down |
| 504 | Gateway Timeout | Upstream service timeout |

## Error Response Format

**Standard Error Response**:

```json
{
  "error": "Validation Error",
  "message": "One or more fields contain invalid data",
  "details": {
    "subject": ["This field is required"],
    "priority": ["Invalid choice. Must be one of: low, medium, high, urgent"]
  },
  "code": "VALIDATION_ERROR",
  "timestamp": "2025-11-19T16:00:00Z"
}
```

**Authentication Error**:

```json
{
  "error": "Authentication Failed",
  "message": "Invalid or expired token",
  "code": "AUTH_FAILED",
  "timestamp": "2025-11-19T16:05:00Z"
}
```

**Rate Limit Error**:

```json
{
  "error": "Rate Limit Exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60,
  "code": "RATE_LIMIT_EXCEEDED",
  "timestamp": "2025-11-19T16:10:00Z"
}
```

## API Documentation (OpenAPI/Swagger)

### Accessing API Documentation

**Development**:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/docs/`
- OpenAPI Schema: `http://localhost:8000/api/schema/`

**Production**:
- API documentation disabled in production (set `DEBUG=False`)
- Access via internal documentation portal

### Example OpenAPI Spec (Excerpt)

```yaml
openapi: 3.0.0
info:
  title: Ticket Tracking System API
  version: 1.0.0
  description: Comprehensive API for ticket management and workflow automation

servers:
  - url: http://localhost:8000/api/v1
    description: Development server
  - url: https://api.ticketsystem.example.com/v1
    description: Production server

paths:
  /users/token/:
    post:
      summary: Obtain JWT token
      tags:
        - Authentication
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                username:
                  type: string
                  example: user@example.com
                password:
                  type: string
                  format: password
                  example: securepassword
      responses:
        '200':
          description: Successful authentication
          content:
            application/json:
              schema:
                type: object
                properties:
                  access:
                    type: string
                  refresh:
                    type: string
                  user:
                    $ref: '#/components/schemas/User'
        '401':
          description: Invalid credentials

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        username:
          type: string
        email:
          type: string
          format: email
        first_name:
          type: string
        last_name:
          type: string
    
    Ticket:
      type: object
      properties:
        id:
          type: integer
        ticket_id:
          type: string
        subject:
          type: string
        description:
          type: string
        priority:
          type: string
          enum: [low, medium, high, urgent]
        status:
          type: string
          enum: [open, in_progress, closed]
  
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - bearerAuth: []
```

## Integration Examples

### Python Integration Example

```python
import requests

class TicketSystemClient:
    """Python client for Ticket Tracking System API"""
    
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.token = None
        self.authenticate(username, password)
    
    def authenticate(self, username, password):
        """Obtain JWT token"""
        response = requests.post(
            f"{self.base_url}/api/v1/users/token/",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data['access']
    
    def _headers(self):
        """Get authentication headers"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def create_ticket(self, subject, description, category, priority='medium'):
        """Create a new ticket"""
        response = requests.post(
            f"{self.base_url}/tickets/",
            headers=self._headers(),
            json={
                'subject': subject,
                'description': description,
                'category': category,
                'priority': priority
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_tickets(self, status=None, page=1):
        """List tickets with optional filters"""
        params = {'page': page}
        if status:
            params['status'] = status
        
        response = requests.get(
            f"{self.base_url}/tickets/",
            headers=self._headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_user_tasks(self, user_id):
        """Get tasks assigned to user"""
        response = requests.get(
            f"{self.base_url}/tasks/",
            headers=self._headers(),
            params={'user_id': user_id, 'status': 'pending'}
        )
        response.raise_for_status()
        return response.json()

# Usage
client = TicketSystemClient(
    base_url='http://localhost:8004',
    username='agent@example.com',
    password='password123'
)

# Create ticket
ticket = client.create_ticket(
    subject='System is slow',
    description='Application performance degraded',
    category='Technical Support',
    priority='high'
)
print(f"Created ticket: {ticket['ticket_id']}")

# List open tickets
tickets = client.get_tickets(status='open')
print(f"Found {tickets['count']} open tickets")
```

### JavaScript Integration Example

```javascript
// frontend/src/api/ticketSystemAPI.js
import axios from 'axios';

class TicketSystemAPI {
  constructor(baseURL) {
    this.client = axios.create({
      baseURL: baseURL,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // Add token to requests if available
    this.client.interceptors.request.use(config => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
    
    // Handle token refresh on 401
    this.client.interceptors.response.use(
      response => response,
      async error => {
        if (error.response?.status === 401) {
          await this.refreshToken();
          return this.client(error.config);
        }
        return Promise.reject(error);
      }
    );
  }
  
  async login(username, password) {
    const response = await this.client.post('/api/v1/users/token/', {
      username,
      password
    });
    
    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);
    
    return response.data;
  }
  
  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await this.client.post('/api/v1/users/token/refresh/', {
      refresh: refreshToken
    });
    
    localStorage.setItem('access_token', response.data.access);
  }
  
  async createTicket(ticketData) {
    const response = await this.client.post('/tickets/', ticketData);
    return response.data;
  }
  
  async getTickets(filters = {}) {
    const response = await this.client.get('/tickets/', {
      params: filters
    });
    return response.data;
  }
  
  async getUserTasks(userId) {
    const response = await this.client.get('/tasks/', {
      params: { user_id: userId, status: 'pending' }
    });
    return response.data;
  }
  
  async performTaskAction(taskId, actionId, comment) {
    const response = await this.client.post(`/tasks/${taskId}/action/`, {
      action_id: actionId,
      comment
    });
    return response.data;
  }
}

export default new TicketSystemAPI('http://localhost:8004');

// Usage in React component:
// import ticketAPI from './api/ticketSystemAPI';
//
// const tickets = await ticketAPI.getTickets({ status: 'open' });
```

## Rate Limiting

### Rate Limit Configuration

| Endpoint | Rate Limit | Scope |
|----------|-----------|-------|
| `/api/v1/users/token/` | 5 requests/minute | Per IP address |
| `/tickets/` (POST) | 30 requests/hour | Per user |
| `/tickets/` (GET) | 100 requests/minute | Per user |
| All other endpoints | 60 requests/minute | Per user |

### Rate Limit Headers

**Response Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1732032000
```

**Rate Limit Exceeded Response**:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1732032000

{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

## Webhooks (Future Enhancement)

**Planned webhook events**:
- `ticket.created`
- `ticket.updated`
- `ticket.assigned`
- `task.completed`
- `workflow.completed`

**Webhook payload example**:
```json
{
  "event": "ticket.created",
  "timestamp": "2025-11-19T17:00:00Z",
  "data": {
    "ticket_id": "TKT-2025-0001",
    "subject": "New issue",
    "priority": "high"
  }
}
```

## References

- **System Architecture**: `/docs/A1_SYSTEM_ARCHITECTURE.md`
- **Integration Guide**: `/docs/A2_INFORMATION_SYSTEMS_INTEGRATION.md`
- **OpenAPI Specification**: Available at `/api/schema/` in development
- **Django REST Framework**: https://www.django-rest-framework.org/
- **JWT Documentation**: https://jwt.io/

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Authors**: API Development Team
