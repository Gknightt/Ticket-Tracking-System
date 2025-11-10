# Workflow Management System - Quick Reference

## What Was Created

### 1. **Serializers** (`workflow/serializers.py`)
- `CreateWorkflowSerializer` - Validates graph structure and creates workflows
- `UpdateWorkflowDetailsSerializer` - Updates workflow properties
- `UpdateWorkflowGraphSerializer` - Validates and updates workflow graphs
- `UpdateStepDetailsSerializer` - Updates step details only
- `UpdateTransitionDetailsSerializer` - Updates transition details only
- `WorkflowDetailSerializer` - Returns complete workflow with steps/transitions
- Graph validation with BFS connectivity checking

### 2. **Views** (`workflow/views.py`)
- `WorkflowViewSet` - Main workflow CRUD operations
  - `create()` - Create workflow with graph (atomic transaction)
  - `update()` / `partial_update()` - Update workflow details
  - `update_graph()` - Replace entire workflow graph
  - `list_steps()` - Get all steps in a workflow
  - `list_transitions()` - Get all transitions in a workflow
  
- `StepManagementViewSet` - Update step details
- `TransitionManagementViewSet` - Update transition details
- `CategoryViewSet` - View workflow categories

### 3. **URLs** (`workflow/urls.py`)
All endpoints registered and ready to use

### 4. **Documentation** (`WORKFLOW_MANAGEMENT_API.md`)
Complete API documentation with examples

---

## Endpoint Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/workflows/` | Create workflow with graph |
| GET | `/workflows/` | List all workflows |
| GET | `/workflows/{id}/` | Get workflow details with steps/transitions |
| PUT | `/workflows/{id}/` | Update workflow details (non-graph) |
| PATCH | `/workflows/{id}/` | Partial update workflow details |
| PUT | `/workflows/{id}/update-graph/` | Replace entire workflow graph |
| GET | `/workflows/{id}/steps/` | List all steps in workflow |
| GET | `/workflows/{id}/transitions/` | List all transitions in workflow |
| PUT | `/steps/{id}/update-details/` | Update step details only |
| PUT | `/transitions/{id}/update-details/` | Update transition details only |

---

## Key Features

✅ **Graph Validation**
- Exactly one start and one end node required
- BFS connectivity checking - all nodes reachable from start
- No self-loops allowed
- Task nodes must have valid role_id
- Duplicate node IDs prevented

✅ **Comprehensive Error Handling**
- Detailed error messages for all validation failures
- 400 Bad Request with descriptive errors
- 404 Not Found for missing resources
- Transaction rollback on errors

✅ **SLA Support**
- Per-priority SLAs (urgent, high, medium, low)
- Automatic validation: `urgent < high < medium < low`
- Applied at workflow level

✅ **Atomic Operations**
- Workflow creation is fully transactional
- If any step/transition fails, entire workflow creation rolls back
- No orphaned records

✅ **Graph Update Strategy**
- When updating graph: DELETE all steps/transitions then RECREATE
- Ensures clean state, no dangling references
- Validated before any changes made

---

## Example Usage

### Create a Workflow
```bash
curl -X POST http://localhost:8000/workflows/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Password Reset Workflow",
    "description": "Handles IT reset requests",
    "category": "IT",
    "sub_category": "Support",
    "department": "IT Support",
    "graph": {
      "nodes": [
        {"temp_id": "n1", "type": "start", "label": "Request Received"},
        {"temp_id": "n2", "type": "task", "label": "Reset Password", "role_id": 1},
        {"temp_id": "n3", "type": "end", "label": "Done"}
      ],
      "edges": [
        {"from_temp_id": "n1", "to_temp_id": "n2"},
        {"from_temp_id": "n2", "to_temp_id": "n3"}
      ]
    }
  }'
```

### Update Workflow Details
```bash
curl -X PUT http://localhost:8000/workflows/1/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "status": "deployed"
  }'
```

### Update Workflow Graph
```bash
curl -X PUT http://localhost:8000/workflows/1/update-graph/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "graph": {
      "nodes": [
        {"temp_id": "n1", "type": "start", "label": "Start"},
        {"temp_id": "n2", "type": "task", "label": "Task 1", "role_id": 1},
        {"temp_id": "n3", "type": "task", "label": "Task 2", "role_id": 2},
        {"temp_id": "n4", "type": "end", "label": "End"}
      ],
      "edges": [
        {"from_temp_id": "n1", "to_temp_id": "n2"},
        {"from_temp_id": "n2", "to_temp_id": "n3"},
        {"from_temp_id": "n3", "to_temp_id": "n4"}
      ]
    }
  }'
```

### Update Step Details
```bash
curl -X PUT http://localhost:8000/steps/2/update-details/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Step Name",
    "description": "New description",
    "order": 2
  }'
```

### Update Transition Details
```bash
curl -X PUT http://localhost:8000/transitions/1/update-details/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Transition Name"
  }'
```

---

## Validation Rules Enforced

### Graph Structure
- ✅ Exactly 1 start node, exactly 1 end node
- ✅ All nodes have unique temp_id
- ✅ Task nodes must have role_id
- ✅ No self-loops (from_temp_id ≠ to_temp_id)
- ✅ No edges from end nodes
- ✅ No edges to start nodes
- ✅ All nodes reachable from start (BFS check)
- ✅ End node reachable from start

### Workflow Details
- ✅ Unique workflow names
- ✅ Valid role references
- ✅ SLA ordering: urgent < high < medium < low
- ✅ Valid status values: draft, deployed, paused, initialized
- ✅ Valid end_logic values: '', asset, budget, notification

### Step/Transition Updates
- ✅ Step can only update: name, description, instruction, order
- ✅ Cannot change role_id or workflow_id (use graph update)
- ✅ Transition can only update: name
- ✅ Cannot change from_step_id or to_step_id (use graph update)

---

## Database Operations

### On Workflow Creation
1. Create Workflows record (status='draft')
2. Create Steps records from nodes (system role for start/end)
3. Create StepTransition records from edges
4. All in single atomic transaction

### On Graph Update
1. Delete all existing Steps (cascades to StepTransition)
2. Delete all StepTransition records
3. Create new Steps from new nodes
4. Create new StepTransition from new edges
5. All in single atomic transaction

### On Detail Updates
1. Update only specified fields
2. No cascade operations
3. Maintain referential integrity

---

## Notes for Integration

1. **Authentication**: Uses `JWTCookieAuthentication` - ensure JWT token is valid
2. **User ID**: Extracted from `request.user.id` during workflow creation
3. **System Role**: Auto-created if doesn't exist for start/end nodes
4. **Logging**: All operations logged with ✅/❌ indicators
5. **Timezone**: Uses UTC (Django TZ setting)
6. **Transaction Safety**: Django's atomic decorator ensures rollback on errors

---

## Next Steps

1. ✅ All endpoints are implemented and ready
2. ✅ Complete error handling and validation
3. ✅ Full API documentation provided
4. Test endpoints in your environment
5. Integrate with frontend graph builder
6. Consider adding filters/search to list endpoints if needed
