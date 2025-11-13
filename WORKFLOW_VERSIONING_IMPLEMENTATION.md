# Workflow Versioning Implementation

## Overview
Implemented a complete workflow versioning system that creates immutable snapshots of workflows when they transition to "initialized" status. This allows tasks to reference specific workflow versions, enabling historical tracking and preventing issues from workflow definition changes mid-execution.

## Changes Made

### 1. WorkflowVersion Model (`workflow/models.py`)
✅ **Added new `WorkflowVersion` model** with:
- `workflow`: ForeignKey to `Workflows` with `related_name='versions'`
- `version`: PositiveIntegerField for version tracking
- `created_at`: Auto timestamp
- `definition`: JSONField containing full workflow structure:
  - **nodes**: Array of steps with metadata (id, label, description, role, order, status)
  - **edges**: Array of transitions (id, from_step, to_step, action)
  - **metadata**: Workflow-level data (SLAs, category, department, end_logic, etc.)
- `is_active`: Boolean flag (default=True) to track active version
- **Meta constraints**:
  - `unique_together = ('workflow', 'version')`
  - Proper indexing for performance on `(workflow, -version)` and `(workflow, is_active)`

### 2. Workflow Version Creation Trigger (`workflow/signals.py`)
✅ **Created `create_workflow_version()` function** that:
- Automatically executes when `Workflows.status` transitions to "initialized"
- Collects all steps, transitions, and metadata from the workflow
- Builds a complete JSONField definition with nodes, edges, and metadata
- Automatically increments version numbers
- Deactivates previous versions when creating new ones
- Handles errors gracefully with logging

✅ **Modified `push_initialized_workflow` signal** to:
- Call `create_workflow_version()` when workflow status becomes "initialized"
- Provides comprehensive logging of versioning events

### 3. Task Model Enhancement (`task/models.py`)
✅ **Added `workflow_version` ForeignKey to Task model**:
- Links task to specific `WorkflowVersion`
- `on_delete=models.SET_NULL` for historical retention
- `null=True, blank=True` for backward compatibility with existing tasks
- `related_name='tasks'` for reverse queries
- Clear help text documenting the purpose

### 4. Task Creation Logic (`tickets/utils.py`)
✅ **Created `get_latest_workflow_version()` helper function** that:
- Fetches the active (is_active=True) WorkflowVersion for a workflow
- Handles graceful fallback if no version exists
- Includes error handling and logging

✅ **Updated `allocate_task_for_ticket()` to**:
- Call `get_latest_workflow_version()` for each workflow
- Assign the `workflow_version` when creating Task instances
- Maintains backward compatibility if version doesn't exist

✅ **Updated `manually_assign_task()` to**:
- Fetch and assign the latest workflow version
- Ensures manual task assignment uses versioned workflow
- Maintains existing validation logic

### 5. Transition Navigation Logic (`task/transitions.py`)
✅ **Created `get_workflow_definition()` helper function** that:
- Hydrates workflow definition from `WorkflowVersion.definition` JSONField
- Falls back to database models if no version is assigned (legacy compatibility)
- Provides comprehensive logging to track which source is used

✅ **Modified `TaskTransitionView.create()` to**:
- Include `workflow_version` in `select_related()` for efficient querying
- Log workflow version information at task retrieval
- Distinguish between versioned (from JSONField) and database-driven flows
- Added detailed logging showing version usage

## How It Works

### Workflow Initialization Flow
1. User completes workflow definition (steps, transitions, roles, metadata)
2. User marks workflow as "ready to initialize"
3. System validates workflow completeness via `compute_workflow_status()`
4. When validation passes, workflow status → "initialized"
5. **Signal triggered**: `push_initialized_workflow()`
6. **Version created**: `create_workflow_version()` captures complete definition
7. Version marked as `is_active=True`, previous versions marked `is_active=False`

### Task Creation Flow
1. Ticket arrives and matches a department/category
2. `allocate_task_for_ticket()` is called
3. For each matching workflow:
   - Fetch latest active `WorkflowVersion`
   - Create `Task` with reference to `workflow_version`
4. Task now has immutable reference to workflow definition

### Transition Navigation Flow
1. Task exists with `workflow_version` reference
2. User initiates transition via `TaskTransitionView`
3. Task is loaded with `select_related('workflow_version')`
4. System can now hydrate full workflow definition from JSONField
5. Transitions use versioned definition for consistency
6. All historical context preserved for audit trail

## Benefits

✅ **Immutability**: Once a workflow is initialized, its definition is frozen in a version
✅ **Auditability**: Can trace exactly which workflow version was used for each task
✅ **History**: Can compare workflow versions to understand how process evolved
✅ **Concurrency**: Multiple workflow versions can coexist for different tasks
✅ **Fallback**: System gracefully handles tasks without versions (backward compatible)
✅ **Performance**: JSONField reduces repeated database queries for workflow structure
✅ **Migration Path**: Existing tasks can continue working; new tasks use versioning

## Database Migration Required

Run the following to create the new model and field:
```bash
python manage.py makemigrations
python manage.py migrate
```

This will:
1. Create `workflow_workflowversion` table
2. Add `workflow_version_id` column to `task_task` table
3. Create necessary indexes for performance

## Backward Compatibility

✅ All changes are backward compatible:
- `workflow_version` is nullable on Task (existing tasks unaffected)
- `get_latest_workflow_version()` returns None if no versions exist
- `transitions.py` logs warnings but continues with database models if needed
- No breaking changes to existing APIs or database constraints

## Testing Recommendations

1. **Version Creation**:
   - Create a workflow with steps/transitions
   - Verify status → "initialized" creates WorkflowVersion
   - Check version number increments correctly

2. **Task Assignment**:
   - Create ticket matching workflow
   - Verify Task.workflow_version is populated
   - Create second workflow version and new task
   - Verify tasks point to correct versions

3. **Transition Logic**:
   - Perform task transitions with versioned workflows
   - Verify logging shows "Using WorkflowVersion X"
   - Compare with legacy behavior (empty version_id)

4. **Historical Data**:
   - Query WorkflowVersion.definition JSONField
   - Verify nodes, edges, metadata are complete
   - Compare with original workflow structure

## Files Modified

1. ✅ `workflow/models.py` - Added WorkflowVersion model
2. ✅ `workflow/signals.py` - Added versioning trigger logic
3. ✅ `task/models.py` - Added workflow_version ForeignKey
4. ✅ `tickets/utils.py` - Updated task creation logic
5. ✅ `task/transitions.py` - Added version hydration support

## Future Enhancements

- Admin interface for viewing/comparing workflow versions
- API endpoint to query historical versions
- Automatic archival of old versions
- Version rollback capability
- Workflow version diff visualization
