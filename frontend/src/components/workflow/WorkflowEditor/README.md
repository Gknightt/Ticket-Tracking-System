# Workflow Management System - Frontend Documentation

## Overview

This is a comprehensive workflow management system built with React, ReactFlow, and Dagre for visual workflow editing. The system allows admins to create, edit, and visualize workflow structures with steps (nodes) and transitions (edges).

## Features

✅ **Visual Workflow Editor** - Interactive drag-and-drop workflow visualization using ReactFlow
✅ **Step Management** - Create, edit, and manage workflow steps with role assignments
✅ **Transition Management** - Define and edit transitions between workflow steps
✅ **Workflow Metadata** - Configure workflow name, SLA times, categories, and more
✅ **Auto-Layout** - Automatic hierarchical layout using Dagre algorithm
✅ **Real-time Editing** - Live editing with unsaved changes tracking
✅ **Role-based Assignment** - Assign roles to each step from available system roles

## Architecture

### Directory Structure

```
frontend/src/
├── api/
│   ├── useWorkflowAPI.jsx              # Main workflow API hooks
│   ├── useWorkflowRoles.jsx            # Fetch available roles
│   └── axios.jsx                        # Axios instance configuration
├── components/
│   └── workflow/
│       └── WorkflowEditor/
│           ├── WorkflowEditorLayout.jsx    # Main editor layout
│           ├── StepNode.jsx                # Custom node component
│           ├── StepEditPanel.jsx           # Step details editor
│           ├── TransitionEditPanel.jsx     # Transition editor
│           ├── WorkflowEditPanel.jsx       # Workflow metadata editor
│           └── *.module.css                # Component styles
├── pages/
│   └── test/
│       ├── WorkflowEditorPage.jsx      # Page wrapper with routing
│       └── WorkflowEditorPage.module.css
├── types/
│   └── workflow.types.ts               # TypeScript interfaces
└── routes/
    └── MainRoute.jsx                   # Routes configuration
```

## API Integration

### Base URL
The system connects to the workflow API using the `VITE_BACKEND_API` environment variable (default: `http://localhost:8002/`)

### Endpoints Used

#### Workflow Details
```
GET /workflow/{workflowId}/detail/
Returns: { workflow: WorkflowMetadata, graph: WorkflowGraph }
```

#### Workflow Graph
```
GET /workflow/{workflowId}/graph/
Returns: { nodes: Step[], edges: Transition[] }
```

#### Update Workflow Graph
```
PUT /workflow/{workflowId}/update-graph/
Body: { nodes: Step[], edges: Transition[] }
```

#### Update Workflow Details
```
PUT /workflow/{workflowId}/update-details/
Body: WorkflowMetadata
```

#### Update Step Details
```
PUT /step/{stepId}/update-details/
Body: { name, description, instruction, role }
```

#### Update Transition Details
```
PUT /transition/{transitionId}/update-details/
Body: { name }
```

#### Get Roles
```
GET /role/
Returns: Role[]
```

## Hooks

### useWorkflowAPI()
Main hook for all workflow API operations.

**Functions:**
- `getWorkflowDetail(workflowId)` - Fetch workflow with graph
- `getWorkflowGraph(workflowId)` - Fetch graph only
- `updateWorkflowGraph(workflowId, graphData)` - Save graph changes
- `updateWorkflowDetails(workflowId, detailsData)` - Save metadata
- `updateStepDetails(stepId, stepData)` - Save step changes
- `updateTransitionDetails(transitionId, transitionData)` - Save transition changes

**State:**
- `loading` - Boolean indicating API call in progress
- `error` - Error message if any

### useWorkflowRoles()
Hook to fetch available system roles.

**Returns:**
- `roles` - Array of Role objects
- `loading` - Boolean
- `error` - Error message if any

## Components

### WorkflowEditorLayout
Main container component that manages the entire editor state and layout.

**Props:**
- `workflowId` (string, required) - The workflow ID to edit

**Features:**
- Loads workflow data on mount
- Manages editing state (step, transition, workflow)
- Handles panel switching
- Coordinates between flow and edit panels

### WorkflowEditorContent (Internal)
Internal component that renders ReactFlow with all nodes and edges.

**Features:**
- Custom node rendering with StepNode
- Edge connection handling
- Edge click detection
- Save changes functionality

### StepNode
Custom ReactFlow node component for workflow steps.

**Display:**
- Step name (label)
- Assigned role
- Description (truncated to 2 lines)

**Interaction:**
- Click to select and edit
- Visual feedback on hover

### StepEditPanel
Panel for editing step details.

**Fields:**
- Step Name (required)
- Role (dropdown, required)
- Description (textarea)
- Instruction (textarea)

**Actions:**
- Save changes
- Cancel without saving

### TransitionEditPanel
Panel for editing transition details.

**Display:**
- From Step ID
- To Step ID

**Fields:**
- Transition Name/Label

**Actions:**
- Save changes
- Cancel without saving

### WorkflowEditPanel
Panel for editing workflow metadata.

**Sections:**
1. **Basic Information**
   - Workflow Name (required)
   - Description

2. **Classification**
   - Category
   - Sub-Category
   - Department

3. **SLA Times** (in hours)
   - Low Priority
   - Medium Priority
   - High Priority
   - Urgent Priority

4. **End Logic**
   - Custom end logic definition

**Actions:**
- Save changes
- Cancel without saving

## Routing

### URL Pattern
```
/test/workflow/:workflowId
```

**Example:**
```
/test/workflow/123
/test/workflow/abc-def-ghi
```

**Route:**
- Added to `MainRoute.jsx`
- No authentication required (can be added via ProtectedRoute)
- Displays error if workflowId is missing

## Data Flow

### Loading Workflow
```
1. Component mounts with workflowId
2. useWorkflowAPI.getWorkflowDetail(workflowId)
3. Convert API response to ReactFlow format
4. Calculate layout using Dagre
5. Render nodes and edges
```

### Editing Step
```
1. User clicks on node
2. StepEditPanel opens with step data
3. User modifies fields
4. Click "Save Step"
5. updateStepDetails() called
6. Panel closes on success
```

### Saving Graph
```
1. User makes changes (edit steps/transitions)
2. unsavedChanges flag set to true
3. Click "Save Changes" button
4. Collect all nodes and edges data
5. updateWorkflowGraph() called
6. On success, clear unsavedChanges flag
```

## Styling

All components use CSS Modules for scoped styling:

- **Colors:**
  - Primary Blue: `#3b82f6`
  - Success Green: `#10b981`
  - Gray: `#6b7280`, `#d1d5db`, `#e5e7eb`

- **Responsive:**
  - Flow container takes remaining space
  - Panel fixed at 320px width
  - Action bar at bottom with consistent padding

- **Interactions:**
  - Smooth transitions (0.2s-0.3s)
  - Hover states for all interactive elements
  - Focus states for accessibility

## TypeScript Interfaces

See `src/types/workflow.types.ts` for all interface definitions:

- `Step` - Workflow step/node
- `Transition` - Edge between steps
- `WorkflowGraph` - Collection of nodes and edges
- `WorkflowMetadata` - Workflow details
- `WorkflowDetail` - Combined workflow data
- `Role` - User role
- `WorkflowNode` - ReactFlow node wrapper
- `WorkflowEdge` - ReactFlow edge wrapper
- `*Request` - API request payloads

## Usage Example

### Access the Workflow Editor
```
Navigate to: http://localhost:5173/test/workflow/1
```

Where `1` is your workflow ID.

### Typical Workflow
1. **View**: Workflow loads with all steps and transitions visualized
2. **Edit Step**: Click a step node, modify its properties, save
3. **Edit Transition**: Click an edge, update its label, save
4. **Edit Workflow**: Click "Edit Workflow Details" button, update metadata, save
5. **Create Transitions**: Connect two nodes by dragging from source to target
6. **Save All**: Click "Save Changes" to persist graph modifications

## Environment Configuration

Add to `.env`:
```
VITE_BACKEND_API=http://localhost:8002/
VITE_WORKFLOW_API=http://localhost:8002/workflow
```

## Dependencies

Already included in `package.json`:
- `reactflow` - Flow diagram library
- `dagre` - Graph layout algorithm
- `react-router-dom` - Routing
- `axios` - HTTP client

## Common Issues & Solutions

### Workflow Won't Load
- Check workflow ID is valid
- Verify `VITE_BACKEND_API` is set correctly
- Check browser console for API errors

### Changes Not Saving
- Ensure "Save Changes" button is not disabled
- Check network tab for failed requests
- Verify user has permission to update workflow

### Layout Issues
- Clear browser cache
- Reload the page
- Check console for JavaScript errors

### Role Dropdown Empty
- Verify `/role/` endpoint is accessible
- Check that roles exist in the database
- Inspect network response in DevTools

## Performance Considerations

- Graph layout (Dagre) is calculated on data load
- Efficient re-renders using React hooks
- Images and assets are served from CDN
- Panel scrolling for long content
- Virtualization for large workflows (can be added if needed)

## Future Enhancements

- [ ] Drag-and-drop node creation
- [ ] Node deletion from canvas
- [ ] Undo/Redo functionality
- [ ] Workflow validation rules
- [ ] Export workflow to JSON/image
- [ ] Collaborative editing
- [ ] Real-time synchronization
- [ ] Workflow versioning
- [ ] Advanced styling options
- [ ] Custom node types

## Support

For issues or questions:
1. Check the workflow API documentation at `workflow_api/WORKFLOW_MANAGEMENT_API.md`
2. Review ReactFlow documentation: https://reactflow.dev/
3. Check browser console for errors
4. Verify API endpoints are responding correctly

---

**Last Updated:** November 10, 2025
**Version:** 1.0.0
