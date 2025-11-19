# A.10 APIs and Integration Points Documentation

## Table of Contents
1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Auth Service APIs](#auth-service-apis)
4. [Workflow API Service](#workflow-api-service)
5. [Messaging Service APIs](#messaging-service-apis)
6. [Notification Service APIs](#notification-service-apis)
7. [API Standards](#api-standards)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [API Testing](#api-testing)

---

## API Overview

The Ticket Tracking System provides RESTful APIs following OpenAPI 3.0 specifications. All APIs use JSON for request/response payloads and follow REST principles.

**Base URLs (Development)**:
- Auth Service: `http://localhost:8003`
- Workflow API: `http://localhost:8002`
- Messaging Service: `http://localhost:8005`
- Notification Service: `http://localhost:8006`

**API Documentation**:
- Auth Service: http://localhost:8003/api/docs/
- Workflow API: http://localhost:8002/docs/
- Notification Service: http://localhost:8006/api/docs/

Generated using **drf-spectacular** (Swagger/OpenAPI 3.0).

---

## Authentication

### JWT Token Authentication

**Token Endpoint**: `POST /token/`

**Request**:
```json
{
  "username": "user@example.com",
  "password": "securePassword123"
}
```

**Response**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Token Usage**:
```http
GET /api/v1/users/ HTTP/1.1
Host: auth-service:8000
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json
```

**Token Expiry**:
- Access Token: 15 minutes
- Refresh Token: 1 day

---

### Token Refresh

**Endpoint**: `POST /token/refresh/`

**Request**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Logout

**Endpoint**: `POST /logout/`

**Headers**: `Authorization: Bearer <access_token>`

**Response**:
```json
{
  "message": "Successfully logged out"
}
```

**Effect**: Blacklists the refresh token

---

## Auth Service APIs

### Base URL
`http://localhost:8003/api/v1/`

---

### User Management

#### List Users
```http
GET /api/v1/users/
Authorization: Bearer <token>
```

**Query Parameters**:
- `page` (int): Page number (default: 1)
- `page_size` (int): Results per page (default: 10, max: 100)
- `search` (string): Search by username or email

**Response (200 OK)**:
```json
{
  "count": 50,
  "next": "http://localhost:8003/api/v1/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "john.doe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "is_active": true,
      "date_joined": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

#### Get User Details
```http
GET /api/v1/users/{id}/
Authorization: Bearer <token>
```

**Response (200 OK)**:
```json
{
  "id": 1,
  "username": "john.doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "roles": [
    {
      "system": "TTS",
      "role_name": "Agent",
      "role_id": 5
    }
  ],
  "date_joined": "2025-01-01T00:00:00Z",
  "last_login": "2025-11-19T10:00:00Z"
}
```

---

#### Create User
```http
POST /api/v1/users/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "username": "jane.smith",
  "email": "jane@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "password": "SecurePass123!",
  "is_active": true
}
```

**Response (201 Created)**:
```json
{
  "id": 2,
  "username": "jane.smith",
  "email": "jane@example.com",
  "message": "User created successfully"
}
```

---

#### Update User
```http
PUT /api/v1/users/{id}/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body** (partial update with PATCH also supported):
```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane.doe@example.com"
}
```

**Response (200 OK)**:
```json
{
  "id": 2,
  "username": "jane.smith",
  "email": "jane.doe@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "message": "User updated successfully"
}
```

---

#### Delete User
```http
DELETE /api/v1/users/{id}/
Authorization: Bearer <token>
```

**Response (204 No Content)**

---

### Role Management

#### List Roles
```http
GET /api/v1/roles/
Authorization: Bearer <token>
```

**Response (200 OK)**:
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "name": "Agent",
      "description": "Support agent role",
      "permissions": ["view_ticket", "update_ticket", "add_comment"],
      "system": "TTS"
    }
  ]
}
```

---

#### Assign Role to User
```http
POST /api/v1/user-roles/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_id": 1,
  "role_id": 5,
  "system": "TTS"
}
```

**Response (201 Created)**:
```json
{
  "assignment_id": 10,
  "user_id": 1,
  "role_id": 5,
  "role_name": "Agent",
  "system": "TTS",
  "assigned_at": "2025-11-19T10:00:00Z"
}
```

---

## Workflow API Service

### Base URL
`http://localhost:8002/`

---

### Workflow Management

#### List Workflows
```http
GET /workflows/
Authorization: Bearer <token>
```

**Query Parameters**:
- `status` (string): Filter by status (draft, deployed, paused)
- `category` (string): Filter by category
- `page` (int): Page number

**Response (200 OK)**:
```json
{
  "count": 20,
  "results": [
    {
      "workflow_id": 1,
      "name": "IT Support Workflow",
      "description": "Workflow for IT support tickets",
      "category": "IT Support",
      "sub_category": "Network",
      "department": "Operations",
      "status": "deployed",
      "is_published": true,
      "low_sla": "2 days",
      "medium_sla": "1 day",
      "high_sla": "8 hours",
      "urgent_sla": "4 hours",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-11-01T00:00:00Z"
    }
  ]
}
```

---

#### Get Workflow Details
```http
GET /workflows/{id}/
Authorization: Bearer <token>
```

**Response (200 OK)**:
```json
{
  "workflow_id": 1,
  "name": "IT Support Workflow",
  "description": "Workflow for IT support tickets",
  "steps": [
    {
      "step_id": 1,
      "name": "Initial Triage",
      "role": "L1 Support",
      "order": 1,
      "requires_approval": false
    },
    {
      "step_id": 2,
      "name": "Technical Analysis",
      "role": "L2 Support",
      "order": 2,
      "requires_approval": true
    }
  ],
  "status": "deployed"
}
```

---

#### Create Workflow
```http
POST /workflows/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "name": "HR Onboarding Workflow",
  "description": "Workflow for new employee onboarding",
  "category": "HR",
  "sub_category": "Onboarding",
  "department": "Human Resources",
  "low_sla": "P5D",
  "medium_sla": "P3D",
  "high_sla": "P1D",
  "urgent_sla": "PT12H"
}
```

**Response (201 Created)**:
```json
{
  "workflow_id": 15,
  "name": "HR Onboarding Workflow",
  "status": "draft",
  "message": "Workflow created successfully"
}
```

---

#### Deploy Workflow
```http
POST /workflows/{id}/deploy/
Authorization: Bearer <token>
```

**Response (200 OK)**:
```json
{
  "workflow_id": 15,
  "status": "deployed",
  "message": "Workflow deployed successfully"
}
```

---

### Task Management

#### List Tasks
```http
GET /tasks/
Authorization: Bearer <token>
```

**Query Parameters**:
- `status` (string): pending, in_progress, completed, closed
- `assigned_user` (int): Filter by assigned user ID
- `priority` (string): low, medium, high, urgent
- `workflow_id` (int): Filter by workflow

**Response (200 OK)**:
```json
{
  "count": 100,
  "results": [
    {
      "task_id": "T-456",
      "workflow_id": 1,
      "workflow_name": "IT Support Workflow",
      "title": "Network connectivity issue",
      "description": "User cannot access internal servers",
      "priority": "high",
      "status": "in_progress",
      "assigned_user": 5,
      "assigned_user_name": "john.doe",
      "current_step": 2,
      "sla_deadline": "2025-11-19T18:00:00Z",
      "created_at": "2025-11-19T10:00:00Z",
      "started_at": "2025-11-19T10:30:00Z"
    }
  ]
}
```

---

#### Get Task Details
```http
GET /tasks/{task_id}/
Authorization: Bearer <token>
```

**Response (200 OK)**:
```json
{
  "task_id": "T-456",
  "workflow": {
    "workflow_id": 1,
    "name": "IT Support Workflow"
  },
  "external_ticket_id": "HDTS-12345",
  "title": "Network connectivity issue",
  "description": "User cannot access internal servers",
  "priority": "high",
  "status": "in_progress",
  "assigned_user": {
    "id": 5,
    "username": "john.doe",
    "email": "john@example.com"
  },
  "current_step": {
    "step_id": 2,
    "name": "Technical Analysis",
    "role": "L2 Support"
  },
  "sla_deadline": "2025-11-19T18:00:00Z",
  "is_sla_breached": false,
  "history": [
    {
      "timestamp": "2025-11-19T10:00:00Z",
      "action": "created",
      "user": "system"
    },
    {
      "timestamp": "2025-11-19T10:30:00Z",
      "action": "started",
      "user": "john.doe"
    }
  ]
}
```

---

#### Update Task
```http
PATCH /tasks/{task_id}/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "status": "completed",
  "notes": "Issue resolved by rebooting network equipment"
}
```

**Response (200 OK)**:
```json
{
  "task_id": "T-456",
  "status": "completed",
  "message": "Task updated successfully"
}
```

---

### Audit Logs

#### Get Audit Logs
```http
GET /audit/
Authorization: Bearer <token>
```

**Query Parameters**:
- `task_id` (string): Filter by task ID
- `user_id` (int): Filter by user
- `action` (string): Filter by action type
- `start_date` (datetime): Filter from date
- `end_date` (datetime): Filter to date

**Response (200 OK)**:
```json
{
  "count": 500,
  "results": [
    {
      "id": 1,
      "timestamp": "2025-11-19T10:30:00Z",
      "user": "john.doe",
      "action": "task_updated",
      "task_id": "T-456",
      "details": {
        "field": "status",
        "old_value": "in_progress",
        "new_value": "completed"
      },
      "ip_address": "192.168.1.100"
    }
  ]
}
```

---

## Messaging Service APIs

### Base URL
`http://localhost:8005/`

---

### Comment Management

#### Create Comment
```http
POST /api/comments/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "ticket_id": 123,
  "text": "Issue has been identified. Will resolve soon.",
  "parent_id": null
}
```

**Response (201 Created)**:
```json
{
  "id": 1,
  "ticket_id": 123,
  "user_id": 5,
  "username": "john.doe",
  "text": "Issue has been identified. Will resolve soon.",
  "parent_id": null,
  "created_at": "2025-11-19T10:45:00Z",
  "updated_at": "2025-11-19T10:45:00Z"
}
```

**Effect**: Broadcasts to all WebSocket clients connected to ticket 123

---

#### List Comments
```http
GET /api/comments/?ticket_id=123
Authorization: Bearer <token>
```

**Response (200 OK)**:
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "ticket_id": 123,
      "user_id": 5,
      "username": "john.doe",
      "text": "Issue has been identified.",
      "parent_id": null,
      "replies": [
        {
          "id": 2,
          "user_id": 6,
          "username": "jane.smith",
          "text": "Thanks for the update!",
          "created_at": "2025-11-19T10:50:00Z"
        }
      ],
      "ratings": {
        "thumbs_up": 2,
        "thumbs_down": 0
      },
      "created_at": "2025-11-19T10:45:00Z"
    }
  ]
}
```

---

### WebSocket Connection

**Endpoint**: `ws://localhost:8005/ws/comments/{ticket_id}/`

**Connection**:
```javascript
const socket = new WebSocket('ws://localhost:8005/ws/comments/123/');

socket.onopen = () => {
  console.log('Connected');
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
  
  if (data.type === 'comment_update') {
    // Handle comment update
    displayComment(data.comment);
  }
};

// Send ping for health check
socket.send(JSON.stringify({
  type: 'ping',
  timestamp: Date.now()
}));
```

**Message Types Received**:
- `connection_established`: Connection confirmed
- `comment_update`: New/updated comment
- `pong`: Response to ping

---

## Notification Service APIs

### Base URL
`http://localhost:8006/api/v1/`

---

### Send Notification

#### Email Notification
```http
POST /api/v1/notifications/send/
X-API-Key: <api-key>
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_email": "user@example.com",
  "user_name": "John Doe",
  "notification_type": "task_assignment",
  "context_data": {
    "task_id": "T-456",
    "task_title": "Network Issue",
    "role_name": "L2 Support"
  }
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Notification sent successfully"
}
```

---

### In-App Notifications

#### Get User Notifications
```http
GET /api/v2/notifications/inapp/
Authorization: Bearer <token>
```

**Query Parameters**:
- `is_read` (boolean): Filter by read status
- `page` (int): Page number

**Response (200 OK)**:
```json
{
  "count": 25,
  "unread_count": 5,
  "results": [
    {
      "id": "uuid",
      "subject": "New Task Assignment",
      "message": "You have been assigned to task T-456",
      "is_read": false,
      "created_at": "2025-11-19T10:00:00Z"
    }
  ]
}
```

---

#### Mark as Read
```http
PATCH /api/v2/notifications/inapp/{id}/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "is_read": true
}
```

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "is_read": true,
  "read_at": "2025-11-19T11:00:00Z"
}
```

---

## API Standards

### Request/Response Format

**Request Headers**:
```
Content-Type: application/json
Authorization: Bearer <token>
Accept: application/json
```

**Response Format**:
```json
{
  "data": {},
  "message": "Success message",
  "errors": []
}
```

---

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource conflict (e.g., duplicate) |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Service temporarily unavailable |

---

## Error Handling

### Error Response Format

```json
{
  "error": "Validation failed",
  "details": {
    "field": "email",
    "message": "Invalid email format"
  },
  "code": "VALIDATION_ERROR",
  "timestamp": "2025-11-19T10:00:00Z"
}
```

---

### Common Error Codes

| Code | Description | Action |
|------|-------------|--------|
| VALIDATION_ERROR | Input validation failed | Check request data |
| AUTH_FAILED | Authentication failed | Check credentials |
| TOKEN_EXPIRED | JWT token expired | Refresh token |
| PERMISSION_DENIED | Insufficient permissions | Check user role |
| RESOURCE_NOT_FOUND | Resource does not exist | Check resource ID |
| RATE_LIMIT_EXCEEDED | Too many requests | Wait and retry |

---

## Rate Limiting

**Limits**:
- Unauthenticated: 100 requests/hour per IP
- Authenticated: 1000 requests/hour per user
- Admin: 5000 requests/hour per user

**Rate Limit Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1637338800
```

**Rate Limit Exceeded Response (429)**:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 3600
}
```

---

## API Testing

### Using cURL

**Get Access Token**:
```bash
curl -X POST http://localhost:8003/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

**List Workflows**:
```bash
curl -X GET http://localhost:8002/workflows/ \
  -H "Authorization: Bearer <token>"
```

**Create Task**:
```bash
curl -X POST http://localhost:8002/tasks/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": 1,
    "title": "Test Task",
    "priority": "high"
  }'
```

---

### Using Postman

**Import OpenAPI Spec**:
1. Open Postman
2. Import → Link → Enter API docs URL
3. Example: http://localhost:8002/schema/

**Environment Variables**:
```
base_url: http://localhost:8002
access_token: <token>
```

---

### Using Python

```python
import requests

# Get token
response = requests.post(
    'http://localhost:8003/token/',
    json={'username': 'user', 'password': 'pass'}
)
token = response.json()['access']

# Call API
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'http://localhost:8002/workflows/',
    headers=headers
)
workflows = response.json()
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Maintained By**: API Development Team
