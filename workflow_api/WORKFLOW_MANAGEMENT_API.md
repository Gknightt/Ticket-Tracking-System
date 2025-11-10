# Workflow Management API Documentation

## Overview
This API provides comprehensive workflow management capabilities including:
- Creating workflows with graph-based step and transition definitions
- Editing workflow details and graphs
- Managing individual step and transition properties
- Retrieving workflow structure and metadata

## Base URL
```
/workflows/
```

---

## 1. CREATING WORKFLOWS

### Endpoint: `POST /workflows/`

**Description**: Create a new workflow with its complete graph (steps and transitions).

**Request Body**:
```json
{
  "name": "Password Reset Workflow",
  "description": "Handles IT password reset requests",
  "category": "IT",
  "sub_category": "Support",
  "department": "IT Support",
  "end_logic": "",
  "graph": {
    "nodes": [
      {
        "temp_id": "n1",
        "type": "start",
        "label": "Request Received",
        "description": "Initial request submission"
      },
      {
        "temp_id": "n2",
        "type": "task",
        "label": "Helpdesk Reset Password",
        "role_id": 1,
        "description": "Helpdesk processes the request",
        "instruction": "Verify user identity and reset password",
        "order": 1
      },
      {
        "temp_id": "n3",
        "type": "task",
        "label": "Send Confirmation Email",
        "role_id": 2,
        "description": "IT Admin confirms completion",
        "instruction": "Send confirmation to user",
        "order": 2
      },
      {
        "temp_id": "n4",
        "type": "end",
        "label": "Done",
        "description": "Request completed"
      }
    ],
    "edges": [
      {
        "from_temp_id": "n1",
        "to_temp_id": "n2",
        "name": "Initial Assignment"
      },
      {
        "from_temp_id": "n2",
        "to_temp_id": "n3",
        "name": "Password Reset Complete"
      },
      {
        "from_temp_id": "n3",
        "to_temp_id": "n4",
        "name": "Confirmation Sent"
      }
    ]
  }
}
```

**Optional Fields**:
- `low_sla`: Duration field (e.g., "08:00:00" for 8 hours)
- `medium_sla`: Duration field
- `high_sla`: Duration field
- `urgent_sla`: Duration field

**SLA Ordering Requirement**: `urgent < high < medium < low`

**Graph Validation Rules**:
1. Must have exactly ONE `start` node and ONE `end` node
2. All nodes must have unique `temp_id`
3. Task nodes MUST have a valid `role_id`
4. All edges must reference existing nodes
5. No self-loops allowed
6. No outgoing edges from `end` nodes
7. No incoming edges to `start` nodes
8. All nodes must be reachable from the start node
9. End node must be reachable from all paths

**Response** (201 Created):
```json
{
  "workflow_id": 1,
  "user_id": 1,
  "name": "Password Reset Workflow",
  "description": "Handles IT password reset requests",
  "category": "IT",
  "sub_category": "Support",
  "department": "IT Support",
  "status": "draft",
  "is_published": false,
  "end_logic": "",
  "low_sla": null,
  "medium_sla": null,
  "high_sla": null,
  "urgent_sla": null,
  "steps": [
    {
      "step_id": 1,
      "workflow_id": 1,
      "role_id": 3,
      "role_name": "System",
      "name": "Request Received",
      "description": "Initial request submission",
      "instruction": null,
      "order": 0,
      "is_initialized": false,
      "created_at": "2025-11-10T10:00:00Z",
      "updated_at": "2025-11-10T10:00:00Z"
    },
    ...
  ],
  "transitions": [
    {
      "transition_id": 1,
      "workflow_id": 1,
      "from_step_id": 1,
      "from_step_name": "Request Received",
      "to_step_id": 2,
      "to_step_name": "Helpdesk Reset Password",
      "name": "Initial Assignment",
      "created_at": "2025-11-10T10:00:00Z"
    },
    ...
  ],
  "created_at": "2025-11-10T10:00:00Z",
  "updated_at": "2025-11-10T10:00:00Z"
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "Failed to create workflow: Node temp_ids must be unique"
}
```

---

## 2. EDITING WORKFLOWS

### 2.1 Edit Workflow Details

**Endpoint**: `PUT /workflows/{workflow_id}/` or `PATCH /workflows/{workflow_id}/`

**Description**: Update workflow properties (description, status, SLAs, etc.) WITHOUT modifying the graph structure.

**Request Body** (all fields optional):
```json
{
  "description": "Updated description",
  "category": "IT",
  "sub_category": "Support",
  "department": "IT Support",
  "status": "deployed",
  "end_logic": "notification",
  "urgent_sla": "01:00:00",
  "high_sla": "02:00:00",
  "medium_sla": "04:00:00",
  "low_sla": "08:00:00"
}
```

**Valid Status Values**: `draft`, `deployed`, `paused`, `initialized`

**Valid end_logic Values**: `""`, `asset`, `budget`, `notification`

**Response** (200 OK):
```json
{
  "workflow_id": 1,
  "user_id": 1,
  "name": "Password Reset Workflow",
  "description": "Updated description",
  "category": "IT",
  "sub_category": "Support",
  "department": "IT Support",
  "status": "deployed",
  "is_published": false,
  "end_logic": "notification",
  "urgent_sla": "01:00:00",
  "high_sla": "02:00:00",
  "medium_sla": "04:00:00",
  "low_sla": "08:00:00",
  "steps": [...],
  "transitions": [...],
  "created_at": "2025-11-10T10:00:00Z",
  "updated_at": "2025-11-10T10:00:00Z"
}
```

**Error Response** (400 Bad Request - SLA Validation):
```json
{
  "error": "Failed to update workflow: urgent_sla should be less than high_sla"
}
```

### 2.2 Edit Workflow Graph

**Endpoint**: `PUT /workflows/{workflow_id}/update-graph/`

**Description**: Replace the entire workflow graph (all steps and transitions). The existing graph is completely deleted and replaced with the new one.

**Request Body**:
```json
{
  "graph": {
    "nodes": [
      {
        "temp_id": "n1",
        "type": "start",
        "label": "Request Received"
      },
      {
        "temp_id": "n2",
        "type": "task",
        "label": "New Task",
        "role_id": 1,
        "order": 1
      },
      {
        "temp_id": "n3",
        "type": "end",
        "label": "Complete"
      }
    ],
    "edges": [
      { "from_temp_id": "n1", "to_temp_id": "n2" },
      { "from_temp_id": "n2", "to_temp_id": "n3" }
    ]
  }
}
```

**Response** (200 OK):
```json
{
  "workflow_id": 1,
  "name": "Password Reset Workflow",
  "description": "Updated description",
  "steps": [
    // New steps with updated structure
  ],
  "transitions": [
    // New transitions
  ],
  ...
}
```

**Graph Validation** (same as creation):
- Exactly one start and one end node
- All nodes reachable from start
- End node reachable from all paths
- No self-loops
- All edges reference existing nodes
- Task nodes must have role_id

**Error Response** (400 Bad Request):
```json
{
  "error": "Failed to update workflow graph: Unreachable nodes from start: {'n4'}"
}
```

---

## 3. EDITING STEP DETAILS

### Endpoint: `PUT /steps/{step_id}/update-details/`

**Description**: Update individual step properties (name, description, instruction, order) WITHOUT changing role or workflow relationships.

**Request Body** (all fields optional):
```json
{
  "name": "Updated Step Name",
  "description": "Updated description",
  "instruction": "Updated instructions for this step",
  "order": 2
}
```

**Response** (200 OK):
```json
{
  "step_id": 2,
  "workflow_id": 1,
  "role_id": 1,
  "role_name": "Helpdesk",
  "name": "Updated Step Name",
  "description": "Updated description",
  "instruction": "Updated instructions for this step",
  "order": 2,
  "is_initialized": false,
  "created_at": "2025-11-10T10:00:00Z",
  "updated_at": "2025-11-10T10:10:00Z"
}
```

**Note**: You CANNOT change `role_id` or `workflow_id` using this endpoint. Use `update-graph` to restructure the workflow.

**Error Response** (404 Not Found):
```json
{
  "error": "Step with ID 999 not found"
}
```

---

## 4. EDITING TRANSITION DETAILS

### Endpoint: `PUT /transitions/{transition_id}/update-details/`

**Description**: Update transition name/label. Does NOT modify the step relationships.

**Request Body**:
```json
{
  "name": "Updated Transition Name"
}
```

**Response** (200 OK):
```json
{
  "transition_id": 1,
  "workflow_id": 1,
  "from_step_id": 1,
  "from_step_name": "Request Received",
  "to_step_id": 2,
  "to_step_name": "Helpdesk Reset Password",
  "name": "Updated Transition Name",
  "created_at": "2025-11-10T10:00:00Z"
}
```

**Note**: You CANNOT change `from_step_id` or `to_step_id` using this endpoint. Use `update-graph` to modify transitions.

**Error Response** (404 Not Found):
```json
{
  "error": "Transition with ID 999 not found"
}
```

---

## 5. RETRIEVING WORKFLOW INFORMATION

### 5.1 Get Workflow Details

**Endpoint**: `GET /workflows/{workflow_id}/`

**Description**: Retrieve complete workflow information including all steps and transitions.

**Response** (200 OK):
```json
{
  "workflow_id": 1,
  "user_id": 1,
  "name": "Password Reset Workflow",
  "description": "Handles IT password reset requests",
  "category": "IT",
  "sub_category": "Support",
  "department": "IT Support",
  "status": "draft",
  "is_published": false,
  "end_logic": "",
  "low_sla": null,
  "medium_sla": null,
  "high_sla": null,
  "urgent_sla": null,
  "steps": [
    {
      "step_id": 1,
      "workflow_id": 1,
      "role_id": 3,
      "role_name": "System",
      "name": "Request Received",
      "description": "Initial request submission",
      "instruction": null,
      "order": 0,
      "is_initialized": false,
      "created_at": "2025-11-10T10:00:00Z",
      "updated_at": "2025-11-10T10:00:00Z"
    },
    {
      "step_id": 2,
      "workflow_id": 1,
      "role_id": 1,
      "role_name": "Helpdesk",
      "name": "Helpdesk Reset Password",
      "description": "Helpdesk processes the request",
      "instruction": "Verify user identity and reset password",
      "order": 1,
      "is_initialized": false,
      "created_at": "2025-11-10T10:00:00Z",
      "updated_at": "2025-11-10T10:00:00Z"
    }
  ],
  "transitions": [
    {
      "transition_id": 1,
      "workflow_id": 1,
      "from_step_id": 1,
      "from_step_name": "Request Received",
      "to_step_id": 2,
      "to_step_name": "Helpdesk Reset Password",
      "name": "Initial Assignment",
      "created_at": "2025-11-10T10:00:00Z"
    }
  ],
  "created_at": "2025-11-10T10:00:00Z",
  "updated_at": "2025-11-10T10:00:00Z"
}
```

### 5.2 List All Steps in Workflow

**Endpoint**: `GET /workflows/{workflow_id}/steps/`

**Description**: Get all steps in a workflow ordered by execution order.

**Response** (200 OK):
```json
{
  "workflow_id": 1,
  "workflow_name": "Password Reset Workflow",
  "steps": [
    {
      "step_id": 1,
      "workflow_id": 1,
      "role_id": 3,
      "role_name": "System",
      "name": "Request Received",
      "description": "Initial request submission",
      "instruction": null,
      "order": 0,
      "is_initialized": false,
      "created_at": "2025-11-10T10:00:00Z",
      "updated_at": "2025-11-10T10:00:00Z"
    }
  ],
  "count": 1
}
```

### 5.3 List All Transitions in Workflow

**Endpoint**: `GET /workflows/{workflow_id}/transitions/`

**Description**: Get all transitions in a workflow.

**Response** (200 OK):
```json
{
  "workflow_id": 1,
  "workflow_name": "Password Reset Workflow",
  "transitions": [
    {
      "transition_id": 1,
      "workflow_id": 1,
      "from_step_id": 1,
      "from_step_name": "Request Received",
      "to_step_id": 2,
      "to_step_name": "Helpdesk Reset Password",
      "name": "Initial Assignment",
      "created_at": "2025-11-10T10:00:00Z"
    }
  ],
  "count": 1
}
```

### 5.4 List All Workflows

**Endpoint**: `GET /workflows/`

**Description**: List all workflows with basic information.

**Query Parameters**:
- No filtering currently implemented, but can be extended

**Response** (200 OK):
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "workflow_id": 1,
      "user_id": 1,
      "name": "Password Reset Workflow",
      "description": "Handles IT password reset requests",
      "category": "IT",
      "sub_category": "Support",
      "department": "IT Support",
      "status": "draft",
      "is_published": false,
      "end_logic": "",
      "low_sla": null,
      "medium_sla": null,
      "high_sla": null,
      "urgent_sla": null,
      "created_at": "2025-11-10T10:00:00Z",
      "updated_at": "2025-11-10T10:00:00Z"
    }
  ]
}
```

---

## Error Handling

All endpoints follow consistent error response patterns:

**400 Bad Request** - Validation error:
```json
{
  "error": "Descriptive error message"
}
```

**404 Not Found** - Resource not found:
```json
{
  "error": "Workflow with ID 999 not found"
}
```

**401 Unauthorized** - Missing/invalid authentication:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## Common Validation Errors

### Workflow Creation/Graph Update:

1. **Duplicate Nodes**: `"Node temp_ids must be unique"`
2. **Missing Start/End**: `"Workflow must have exactly one 'start' node"`
3. **Invalid Role**: `"Role with ID 999 does not exist"`
4. **Missing Role for Task**: `"Task node 'n2' must have a valid role_id"`
5. **Self-Loop**: `"Self-loop not allowed: n1 -> n1"`
6. **Unreachable Nodes**: `"Unreachable nodes from start: {'n4'}"`
7. **Disconnected End**: `"End node is not reachable from start node"`
8. **Invalid Edge**: `"Edge references non-existent node: n99"`
9. **Duplicate Workflow Name**: `"Workflow with name 'Name' already exists"`

### SLA Validation:

1. **Invalid Order**: `"urgent_sla should be less than high_sla (i.e., urgent < high < medium < low)"`

---

## Authentication

All endpoints require JWT authentication via cookie or header:

```
Authorization: Bearer <token>
```

or

```
Cookie: access_token=<token>
```

---

## Implementation Notes

- All workflow creation operations are **atomic** - if any step fails, the entire transaction is rolled back
- Graph updates **DELETE and RECREATE** all steps and transitions
- Start and End nodes automatically use a "System" role
- Step order is determined by the `order` field in nodes, defaulting to array position
- Transitions are created based on edge definitions
