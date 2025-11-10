# Workflow Management API Documentation - Updated Graph Format

## Overview
This API provides comprehensive workflow management capabilities including:
- Creating workflows with graph-based step and transition definitions
- Editing workflow details and graphs
- Managing individual step and transition properties
- Retrieving workflow structure with database IDs and frontend design coordinates

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
  "graph": {
    "nodes": [
      {
        "temp_id": "n1",
        "type": "start",
        "label": "Request Received",
        "description": "Initial request submission",
        "design": {"x": 100, "y": 200}
      },
      {
        "temp_id": "n2",
        "type": "task",
        "label": "Helpdesk Reset Password",
        "role_id": 1,
        "description": "Helpdesk processes the request",
        "instruction": "Verify user identity and reset password",
        "order": 1,
        "design": {"x": 350, "y": 200}
      },
      {
        "temp_id": "n3",
        "type": "task",
        "label": "Send Confirmation Email",
        "role_id": 2,
        "description": "IT Admin confirms completion",
        "instruction": "Send confirmation to user",
        "order": 2,
        "design": {"x": 600, "y": 200}
      },
      {
        "temp_id": "n4",
        "type": "end",
        "label": "Done",
        "description": "Request completed",
        "design": {"x": 850, "y": 200}
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

**Node Fields**:
- `temp_id` (required): Temporary ID for frontend identification (e.g., "n1", "n2")
- `type` (required): One of `'start'`, `'task'`, `'end'`
- `label` (required): Display name for the node
- `role_id` (required for task nodes): The role ID assigned to this task
- `description` (optional): Detailed description of the step
- `instruction` (optional): Instructions for executing this step
- `order` (optional): Execution order (defaults to array position)
- `design` (optional): Frontend coordinates `{"x": number, "y": number}`

**Edge Fields**:
- `from_temp_id` (required): Source node temp_id
- `to_temp_id` (required): Target node temp_id
- `name` (optional): Transition label

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
  "graph": {
    "nodes": [
      {
        "id": 1,
        "name": "Request Received",
        "role": "System",
        "description": "Initial request submission",
        "instruction": "",
        "created_at": "2025-11-10T10:00:00Z",
        "updated_at": "2025-11-10T10:00:00Z",
        "design": {"x": 100, "y": 200}
      },
      {
        "id": 2,
        "name": "Helpdesk Reset Password",
        "role": "Helpdesk",
        "description": "Helpdesk processes the request",
        "instruction": "Verify user identity and reset password",
        "created_at": "2025-11-10T10:00:00Z",
        "updated_at": "2025-11-10T10:00:00Z",
        "design": {"x": 350, "y": 200}
      },
      {
        "id": 3,
        "name": "Send Confirmation Email",
        "role": "IT Admin",
        "description": "IT Admin confirms completion",
        "instruction": "Send confirmation to user",
        "created_at": "2025-11-10T10:00:00Z",
        "updated_at": "2025-11-10T10:00:00Z",
        "design": {"x": 600, "y": 200}
      },
      {
        "id": 4,
        "name": "Done",
        "role": "System",
        "description": "Request completed",
        "instruction": "",
        "created_at": "2025-11-10T10:00:00Z",
        "updated_at": "2025-11-10T10:00:00Z",
        "design": {"x": 850, "y": 200}
      }
    ],
    "edges": [
      {
        "id": 1,
        "from": 1,
        "to": 2,
        "name": "Initial Assignment"
      },
      {
        "id": 2,
        "from": 2,
        "to": 3,
        "name": "Password Reset Complete"
      },
      {
        "id": 3,
        "from": 3,
        "to": 4,
        "name": "Confirmation Sent"
      }
    ]
  },
  "created_at": "2025-11-10T10:00:00Z",
  "updated_at": "2025-11-10T10:00:00Z"
}
```

**Response Graph Format**:
- Nodes use `id` (database step_id) instead of temp_id
- Edges use `from` and `to` (database step_ids) instead of from_temp_id/to_temp_id
- All coordinates and metadata are preserved

---

## 2. RETRIEVING WORKFLOW WITH GRAPH

### Endpoint: `GET /workflows/{workflow_id}/`

**Description**: Get complete workflow information including the graph with database IDs.

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
  "graph": {
    "nodes": [
      {
        "id": 1,
        "name": "Triage Ticket",
        "role": "Admin",
        "description": "Initial triage to verify ticket completeness",
        "instruction": "Set the initial priority level",
        "created_at": "2025-11-10T09:33:46.426711Z",
        "updated_at": "2025-11-10T09:33:46.426736Z",
        "design": {"x": 100, "y": 200}
      },
      {
        "id": 2,
        "name": "Resolve Ticket",
        "role": "Admin",
        "description": "Resolve the ticket",
        "instruction": "Work on resolving the issue",
        "created_at": "2025-11-10T09:33:46.426711Z",
        "updated_at": "2025-11-10T09:33:46.426736Z",
        "design": {"x": 350, "y": 200}
      }
    ],
    "edges": [
      {
        "id": 1,
        "from": 1,
        "to": 2,
        "name": "Proceed"
      }
    ]
  },
  "created_at": "2025-11-10T09:33:46.426711Z",
  "updated_at": "2025-11-10T09:33:46.426736Z"
}
```

---

## 3. EDITING WORKFLOWS

### 3.1 Edit Workflow Details

**Endpoint**: `PUT /workflows/{workflow_id}/` or `PATCH /workflows/{workflow_id}/`

**Description**: Update workflow properties WITHOUT modifying the graph structure.

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

**Response** (200 OK): Same as workflow retrieval with updated graph

### 3.2 Edit Workflow Graph

**Endpoint**: `PUT /workflows/{workflow_id}/update-graph/` or `PATCH /workflows/{workflow_id}/update-graph/`

**Description**: Replace the entire workflow graph. Uses temp_ids during request but returns database IDs.

**Request Body** (same format as creation):
```json
{
  "graph": {
    "nodes": [
      {
        "temp_id": "n1",
        "type": "start",
        "label": "Start",
        "design": {"x": 100, "y": 200}
      },
      {
        "temp_id": "n2",
        "type": "task",
        "label": "Process",
        "role_id": 1,
        "order": 1,
        "design": {"x": 350, "y": 200}
      },
      {
        "temp_id": "n3",
        "type": "end",
        "label": "End",
        "design": {"x": 600, "y": 200}
      }
    ],
    "edges": [
      {"from_temp_id": "n1", "to_temp_id": "n2", "name": "Go"},
      {"from_temp_id": "n2", "to_temp_id": "n3", "name": "Finish"}
    ]
  }
}
```

**Response** (200 OK): Returns complete workflow with new graph using database IDs

---

## 4. EDITING STEP DETAILS

### Endpoint: `PUT /steps/{step_id}/update-details/`

**Description**: Update individual step properties including design coordinates.

**Request Body** (all fields optional):
```json
{
  "name": "Updated Step Name",
  "description": "Updated description",
  "instruction": "Updated instructions",
  "order": 2,
  "design": {"x": 400, "y": 250}
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
  "instruction": "Updated instructions",
  "order": 2,
  "design": {"x": 400, "y": 250},
  "is_initialized": false,
  "created_at": "2025-11-10T10:00:00Z",
  "updated_at": "2025-11-10T10:10:00Z"
}
```

**Note**: Cannot change `role_id` or `workflow_id` using this endpoint. Use graph update for structural changes.

---

## 5. EDITING TRANSITION DETAILS

### Endpoint: `PUT /transitions/{transition_id}/update-details/`

**Description**: Update transition name/label only.

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
  "created_at": "2025-11-10T10:00:00Z",
  "updated_at": "2025-11-10T10:10:00Z"
}
```

---

## 6. LISTING WORKFLOWS AND COMPONENTS

### 6.1 List All Workflows

**Endpoint**: `GET /workflows/`

**Response** (200 OK):
```json
{
  "count": 2,
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

### 6.2 List All Steps in Workflow

**Endpoint**: `GET /workflows/{workflow_id}/steps/`

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
      "design": {"x": 100, "y": 200},
      "is_initialized": false,
      "created_at": "2025-11-10T10:00:00Z",
      "updated_at": "2025-11-10T10:00:00Z"
    }
  ],
  "count": 1
}
```

### 6.3 List All Transitions in Workflow

**Endpoint**: `GET /workflows/{workflow_id}/transitions/`

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
      "created_at": "2025-11-10T10:00:00Z",
      "updated_at": "2025-11-10T10:00:00Z"
    }
  ],
  "count": 1
}
```

---

## Graph Format Summary

### Input Format (for creation/updates)
- Uses `temp_id` for nodes (temporary frontend identifiers)
- Uses `from_temp_id` and `to_temp_id` for edges

### Output Format (in responses)
- Uses `id` for nodes (database step_id)
- Uses `from` and `to` for edges (database step_ids)
- Includes `design` coordinates for frontend positioning
- Includes timestamps for audit tracking

### Design Coordinates
- `design` field stores `{"x": number, "y": number}` coordinates
- Used for positioning nodes in frontend diagram
- Can be updated via step detail endpoint
- Defaults to `{"x": 100 + (order * 250), "y": 200}` if not provided

---

## Validation Rules

### Graph Structure
- ✅ Exactly 1 start node and exactly 1 end node
- ✅ All temp_ids must be unique
- ✅ Task nodes must have role_id
- ✅ No self-loops
- ✅ No outgoing edges from end nodes
- ✅ No incoming edges to start nodes
- ✅ All nodes reachable from start (BFS validation)
- ✅ End node reachable from start

### SLA Ordering
- `urgent_sla < high_sla < medium_sla < low_sla`

---

## Error Handling

**400 Bad Request**:
```json
{
  "error": "Failed to create workflow: Node temp_ids must be unique"
}
```

**404 Not Found**:
```json
{
  "error": "Workflow with ID 999 not found"
}
```

---

## Migration Required

After updating the code, run:
```bash
python manage.py makemigrations step
python manage.py migrate
```

This adds the `design` JSONField to the Steps model for storing frontend coordinates.

---

## Example Frontend Integration

```javascript
// Fetching workflow with graph
const response = await fetch('/workflows/1/');
const workflow = await response.json();

// Accessing graph data
workflow.graph.nodes.forEach(node => {
  renderNode(node.id, node.name, node.design.x, node.design.y);
});

workflow.graph.edges.forEach(edge => {
  connectNodes(edge.from, edge.to, edge.name);
});

// Updating graph from frontend
const updatedGraph = {
  graph: {
    nodes: nodes.map(n => ({
      temp_id: n.tempId,
      type: n.type,
      label: n.label,
      role_id: n.roleId,
      description: n.description,
      instruction: n.instruction,
      design: {x: n.x, y: n.y}
    })),
    edges: edges.map(e => ({
      from_temp_id: e.fromTempId,
      to_temp_id: e.toTempId,
      name: e.label
    }))
  }
};

await fetch('/workflows/1/update-graph/', {
  method: 'PATCH',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(updatedGraph)
});
```
