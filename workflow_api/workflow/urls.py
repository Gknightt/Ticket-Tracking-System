from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkflowViewSet, CategoryViewSet, StepManagementViewSet, TransitionManagementViewSet

# Create routers
workflow_router = DefaultRouter()
workflow_router.register(r'', WorkflowViewSet, basename='workflow')
workflow_router.register(r'categories', CategoryViewSet, basename='category')

app_name = 'workflow'

urlpatterns = [
    # Workflow management endpoints
    # POST /workflows/ - Create workflow with graph
    # GET /workflows/ - List workflows
    # GET /workflows/{id}/ - Get workflow details
    # PUT /workflows/{id}/ - Update workflow details (non-graph)
    # PATCH /workflows/{id}/ - Partially update workflow details
    # PUT /workflows/{id}/update-graph/ - Update workflow graph
    # GET /workflows/{id}/steps/ - List steps in workflow
    # GET /workflows/{id}/transitions/ - List transitions in workflow
    path('', include(workflow_router.urls)),
    
    # Step management endpoints
    # PUT /steps/{id}/update-details/ - Update step details
    path('steps/<int:step_id>/update-details/', StepManagementViewSet.as_view({'put': 'update_details'}), name='step-update-details'),
    
    # Transition management endpoints
    # PUT /transitions/{id}/update-details/ - Update transition details
    path('transitions/<int:transition_id>/update-details/', TransitionManagementViewSet.as_view({'put': 'update_details'}), name='transition-update-details'),
]
