# Workflow Management System - Quick Start Guide

## 🚀 Quick Start

### Step 1: Access the Workflow Editor
Open your browser and navigate to:
```
http://localhost:5173/test/workflow/1
```
Replace `1` with your actual workflow ID.

### Step 2: View Your Workflow
The editor will display:
- **Left side**: Interactive workflow diagram with all steps and transitions
- **Right side**: Properties panel (initially empty)
- **Bottom**: Save button and workflow edit button

### Step 3: Edit a Step
1. Click on any **blue step node** in the diagram
2. The right panel opens showing step details:
   - Step Name
   - Assigned Role (dropdown)
   - Description
   - Instruction
3. Modify the fields as needed
4. Click **"Save Step"** to persist changes

### Step 4: Edit a Transition
1. Click on any **connection/edge** between steps
2. The right panel shows:
   - From Step ID
   - To Step ID
   - Transition Name/Label
3. Update the label (e.g., "Approved", "Rejected")
4. Click **"Save Transition"** to persist

### Step 5: Edit Workflow Metadata
1. Click **"Edit Workflow Details"** button in the right panel
2. Update:
   - Workflow name and description
   - Category, sub-category, department
   - SLA times (Low, Medium, High, Urgent)
   - End logic
3. Click **"Save Workflow"** to persist

### Step 6: Save All Changes
After making any changes to the graph structure:
1. Click **"Save Changes"** button at the bottom
2. Wait for confirmation (button will show "Saving...")
3. All modifications are now persisted

## 📁 File Structure Created

```
frontend/src/
├── api/
│   ├── useWorkflowAPI.jsx              ✅ Main API hooks
│   └── useWorkflowRoles.jsx            ✅ Fetch roles
├── components/workflow/WorkflowEditor/
│   ├── WorkflowEditorLayout.jsx        ✅ Main editor
│   ├── WorkflowEditorLayout.module.css ✅ Editor styles
│   ├── StepNode.jsx                    ✅ Step node component
│   ├── StepNode.module.css             ✅ Node styles
│   ├── StepEditPanel.jsx               ✅ Edit step panel
│   ├── StepEditPanel.module.css        ✅ Step panel styles
│   ├── TransitionEditPanel.jsx         ✅ Edit transition panel
│   ├── TransitionEditPanel.module.css  ✅ Transition styles
│   ├── WorkflowEditPanel.jsx           ✅ Edit workflow panel
│   ├── WorkflowEditPanel.module.css    ✅ Workflow styles
│   └── README.md                       ✅ Full documentation
├── pages/test/
│   ├── WorkflowEditorPage.jsx          ✅ Page wrapper
│   └── WorkflowEditorPage.module.css   ✅ Page styles
├── types/
│   └── workflow.types.ts               ✅ TypeScript interfaces
└── routes/
    └── MainRoute.jsx                   ✅ Routes updated
```

## 🔌 API Endpoints Connected

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/workflow/{id}/detail/` | Load workflow with graph |
| PUT | `/workflow/{id}/update-graph/` | Save graph changes |
| PUT | `/workflow/{id}/update-details/` | Save workflow metadata |
| PUT | `/step/{id}/update-details/` | Save step changes |
| PUT | `/transition/{id}/update-details/` | Save transition changes |
| GET | `/role/` | Fetch available roles |

## 🎨 Key Features

### ✅ Implemented
- ✅ Visual workflow editor with ReactFlow
- ✅ Automatic hierarchical layout (Dagre)
- ✅ Interactive step nodes with role display
- ✅ Edit panels for steps, transitions, and workflow metadata
- ✅ Real-time unsaved changes tracking
- ✅ Role-based step assignment
- ✅ SLA configuration (Low, Medium, High, Urgent)
- ✅ Responsive split-panel layout
- ✅ Error handling and loading states
- ✅ TypeScript interfaces for type safety

### 🚧 Ready for Future Enhancement
- [ ] Drag-and-drop node creation
- [ ] Node/edge deletion buttons
- [ ] Undo/Redo functionality
- [ ] Workflow validation
- [ ] Export to JSON/PNG
- [ ] Collaborative editing
- [ ] Workflow versioning
- [ ] Custom styling per role

## 🔧 Environment Setup

Ensure your `.env` file has:
```env
VITE_BACKEND_API=http://localhost:8002/
VITE_WORKFLOW_API=http://localhost:8002/workflow
```

## 🧪 Testing the System

### Test Scenario 1: View Existing Workflow
```
1. Navigate to /test/workflow/1
2. Verify all steps render as blue nodes
3. Verify transitions show as connecting lines
4. Check that roles display under step names
```

### Test Scenario 2: Edit a Step
```
1. Click on a step node
2. Change the step name
3. Change the role from dropdown
4. Add a description
5. Click "Save Step"
6. Verify changes persist
```

### Test Scenario 3: Edit a Transition
```
1. Click on a connecting edge
2. Update the transition label
3. Click "Save Transition"
4. Verify label updates on the edge
```

### Test Scenario 4: Update Workflow Metadata
```
1. Click "Edit Workflow Details"
2. Change workflow name and description
3. Set SLA times for each priority
4. Click "Save Workflow"
5. Verify changes persist
```

### Test Scenario 5: Save Graph Changes
```
1. Make any changes to steps/transitions
2. Click "Save Changes" button
3. Monitor console for success/error
4. Refresh page to verify persistence
```

## 📊 Data Model

### Step Object
```javascript
{
  id: number,
  name: string,
  role: string,
  description?: string,
  instruction?: string,
  design: { x: number, y: number },
  to_delete?: boolean
}
```

### Transition Object
```javascript
{
  id: number,
  from: number,          // From Step ID
  to: number,            // To Step ID
  name: string,          // Label/action
  to_delete?: boolean
}
```

### Workflow Object
```javascript
{
  id: number,
  name: string,
  description?: string,
  category?: string,
  sub_category?: string,
  department?: string,
  end_logic?: string,
  low_sla?: number,      // Hours
  medium_sla?: number,   // Hours
  high_sla?: number,     // Hours
  urgent_sla?: number    // Hours
}
```

## 🐛 Debugging Tips

### Enable Verbose Logging
Add to components:
```javascript
console.log('Workflow loaded:', data);
console.log('Nodes:', nodes);
console.log('Edges:', edges);
```

### Check API Responses
In browser DevTools → Network tab:
1. Filter by XHR
2. Look for workflow requests
3. Check response status and payload
4. Verify data format matches interfaces

### ReactFlow Debug Mode
- Use keyboard shortcuts:
  - `↑↓←→` - Pan around
  - `+/-` - Zoom in/out
  - `Shift+Click` - Select multiple nodes
  - `Delete` - Remove selected (if implemented)

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "No Workflow ID Provided" | Missing :workflowId in URL | Use /test/workflow/1 format |
| "Failed to fetch workflow" | API not running | Start workflow_api service |
| "Failed to update step" | Invalid role | Select from dropdown |
| Network 404 | Wrong endpoint path | Check base URL in .env |
| Network 500 | Backend error | Check workflow_api logs |

## 📚 Additional Resources

- **Workflow API Docs**: `workflow_api/WORKFLOW_MANAGEMENT_API.md`
- **ReactFlow Docs**: https://reactflow.dev/
- **Dagre Docs**: https://dagrejs.github.io/
- **Project README**: Root `ReadMe.md`

## 🎯 Next Steps

1. **Test with your workflow data**
   - Create a workflow in workflow_api
   - Access via /test/workflow/:id

2. **Integrate with admin workflow page**
   - Link from `/admin/workflow` to `/test/workflow/:id`
   - Add edit buttons to workflow list

3. **Add authentication** (optional)
   - Wrap route in `<ProtectedRoute requireAdmin={true} />`

4. **Enhance UI**
   - Add workflow title header
   - Add breadcrumb navigation
   - Add help tooltips

5. **Performance optimization**
   - Add virtualization for large workflows
   - Implement debounced saves
   - Add caching layer

---

**Happy workflow editing! 🎉**
