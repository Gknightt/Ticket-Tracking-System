from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.db import transaction
import logging

from .models import Workflows, Category
from .serializers import (
    WorkflowBasicSerializer,
    WorkflowGraphResponseSerializer,
    CreateWorkflowSerializer,
    UpdateWorkflowDetailsSerializer,
    UpdateWorkflowGraphSerializer,
    UpdateWorkflowGraphSerializerV2,
    CategorySerializer,
    StepSerializer,
    UpdateStepDetailsSerializer,
    TransitionSerializer,
    UpdateTransitionDetailsSerializer,
)
from step.models import Steps, StepTransition
from role.models import Roles
from authentication import JWTCookieAuthentication

logger = logging.getLogger(__name__)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing workflow categories.
    
    Actions:
    - list: GET /categories/ - List all categories
    - retrieve: GET /categories/{id}/ - Get category details
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]


class WorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workflows.
    
    Actions:
    - list: GET /workflows/ - List all workflows
    - create: POST /workflows/ - Create a new workflow with graph
    - retrieve: GET /workflows/{id}/ - Get workflow details with graph
    - update: PUT /workflows/{id}/ - Update workflow details (non-graph)
    - partial_update: PATCH /workflows/{id}/ - Partially update workflow details
    - update_graph: PUT/PATCH /workflows/{id}/update-graph/ - Update workflow graph incrementally
    - list_steps: GET /workflows/{id}/steps/ - List steps in workflow
    - list_transitions: GET /workflows/{id}/transitions/ - List transitions in workflow
    """
    
    serializer_class = WorkflowBasicSerializer
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Workflows.objects.all()
    lookup_field = 'workflow_id'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return CreateWorkflowSerializer
        elif self.action == 'retrieve':
            return WorkflowGraphResponseSerializer
        elif self.action == 'update_graph':
            return UpdateWorkflowGraphSerializerV2
        elif self.action in ['update', 'partial_update']:
            return UpdateWorkflowDetailsSerializer
        return WorkflowBasicSerializer
    
    def get_serializer(self, *args, **kwargs):
        """Override to prevent passing instance to non-ModelSerializer classes"""
        # For update_graph action, don't pass instance to serializer
        if self.action == 'update_graph' and args and isinstance(args[0], Workflows):
            # Remove the instance argument
            args = args[1:]
        return super().get_serializer(*args, **kwargs)
    
    def get_object(self):
        """Override to use workflow_id instead of id"""
        workflow_id = self.kwargs.get(self.lookup_field)
        try:
            return Workflows.objects.get(workflow_id=workflow_id)
        except Workflows.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound(f"Workflow with ID {workflow_id} not found")
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create a new workflow with steps and transitions.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Extract graph data
            graph_data = serializer.validated_data.pop('graph')
            nodes = graph_data['nodes']
            edges = graph_data['edges']
            
            # Get user_id from JWT token
            user_id = request.user.id if hasattr(request.user, 'id') else 1
            
            # Create workflow
            workflow = Workflows.objects.create(
                user_id=user_id,
                name=serializer.validated_data['name'],
                description=serializer.validated_data.get('description', ''),
                category=serializer.validated_data['category'],
                sub_category=serializer.validated_data['sub_category'],
                department=serializer.validated_data['department'],
                end_logic=serializer.validated_data.get('end_logic', ''),
                low_sla=serializer.validated_data.get('low_sla'),
                medium_sla=serializer.validated_data.get('medium_sla'),
                high_sla=serializer.validated_data.get('high_sla'),
                urgent_sla=serializer.validated_data.get('urgent_sla'),
                status='draft'
            )
            
            logger.info(f"✅ Created workflow: {workflow.name} (ID: {workflow.workflow_id})")
            
            # Create steps from nodes
            temp_id_to_step = {}
            for idx, node in enumerate(nodes):
                order = node.get('order', idx)
                design = node.get('design', {'x': 100 + (idx * 250), 'y': 200})
                
                if node['type'] == 'start':
                    start_role = Roles.objects.filter(name__iexact='system').first()
                    if not start_role:
                        start_role = Roles.objects.create(user_id=user_id, name='System', description='System role')
                    
                    step = Steps.objects.create(
                        workflow_id=workflow,
                        role_id=start_role,
                        name=node['label'],
                        description=node.get('description', ''),
                        instruction=node.get('instruction', ''),
                        order=order,
                        design=design
                    )
                
                elif node['type'] == 'end':
                    end_role = Roles.objects.filter(name__iexact='system').first()
                    if not end_role:
                        end_role = Roles.objects.create(user_id=user_id, name='System', description='System role')
                    
                    step = Steps.objects.create(
                        workflow_id=workflow,
                        role_id=end_role,
                        name=node['label'],
                        description=node.get('description', ''),
                        instruction=node.get('instruction', ''),
                        order=order,
                        design=design
                    )
                
                elif node['type'] == 'task':
                    role = Roles.objects.get(role_id=node['role_id'])
                    step = Steps.objects.create(
                        workflow_id=workflow,
                        role_id=role,
                        name=node['label'],
                        description=node.get('description', ''),
                        instruction=node.get('instruction', ''),
                        order=order,
                        design=design
                    )
                
                temp_id_to_step[node['temp_id']] = step
                logger.info(f"✅ Created step: {step.name} (ID: {step.step_id})")
            
            # Create transitions from edges
            for edge in edges:
                from_step = temp_id_to_step[edge['from_temp_id']]
                to_step = temp_id_to_step[edge['to_temp_id']]
                
                transition = StepTransition.objects.create(
                    workflow_id=workflow,
                    from_step_id=from_step,
                    to_step_id=to_step,
                    name=edge.get('name', '')
                )
                logger.info(f"✅ Created transition: {from_step.name} -> {to_step.name}")
            
            # Return created workflow with graph in new format
            output_serializer = WorkflowGraphResponseSerializer(workflow)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"❌ Error creating workflow: {str(e)}")
            return Response(
                {'error': f'Failed to create workflow: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def retrieve(self, request, *args, **kwargs):
        """Get workflow with graph in the new format (using database IDs)."""
        workflow = self.get_object()
        serializer = self.get_serializer(workflow)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update workflow details (non-graph fields)."""
        workflow = self.get_object()
        serializer = self.get_serializer(workflow, data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            for field, value in serializer.validated_data.items():
                setattr(workflow, field, value)
            workflow.save()
            
            logger.info(f"✅ Updated workflow: {workflow.name} (ID: {workflow.workflow_id})")
            
            output_serializer = WorkflowGraphResponseSerializer(workflow)
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"❌ Error updating workflow: {str(e)}")
            return Response(
                {'error': f'Failed to update workflow: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def partial_update(self, request, *args, **kwargs):
        """Partially update workflow details."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @transaction.atomic
    @action(detail=True, methods=['put', 'patch'], url_path='update-graph')
    def update_graph(self, request, workflow_id=None):
        """
        Update workflow graph incrementally.
        Supports updating existing nodes/edges, creating new ones, and deleting marked ones.
        
        Request body format:
        {
            "graph": {
                "nodes": [
                    { "id": 1, "name": "Updated Name", "design": {"x": 150, "y": 220} },
                    { "id": "temp-1", "name": "New Node", "role": "Admin", "design": {"x": 300, "y": 400} },
                    { "id": 2, "to_delete": true }
                ],
                "edges": [
                    { "id": 1, "from": 1, "to": 2, "name": "Updated Edge" },
                    { "id": "temp-e1", "from": 1, "to": "temp-1", "name": "New Edge" },
                    { "id": 3, "to_delete": true }
                ]
            }
        }
        """
        workflow = self.get_object()
        # Directly instantiate serializer without passing instance
        serializer = UpdateWorkflowGraphSerializerV2(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            graph_data = serializer.validated_data['graph']
            nodes_data = graph_data.get('nodes', [])
            edges_data = graph_data.get('edges', [])
            
            logger.info(f"🔄 Updating workflow graph: {workflow.name} (ID: {workflow.workflow_id})")
            
            # Track temp_id to DB id mappings for new nodes
            temp_id_map = {}
            
            # Step 1: Delete marked nodes (cascades to edges)
            for node_data in nodes_data:
                if node_data.get('to_delete', False) and isinstance(node_data.get('id'), int):
                    try:
                        step = Steps.objects.get(step_id=node_data['id'], workflow_id=workflow)
                        logger.info(f"🗑️ Deleting step: {step.name} (ID: {step.step_id})")
                        step.delete()
                    except Steps.DoesNotExist:
                        logger.warning(f"Step {node_data['id']} not found for deletion")
            
            # Step 2: Delete marked edges
            for edge_data in edges_data:
                if edge_data.get('to_delete', False) and isinstance(edge_data.get('id'), int):
                    try:
                        transition = StepTransition.objects.get(transition_id=edge_data['id'], workflow_id=workflow)
                        logger.info(f"🗑️ Deleting transition: {transition.transition_id}")
                        transition.delete()
                    except StepTransition.DoesNotExist:
                        logger.warning(f"Transition {edge_data['id']} not found for deletion")
            
            # Step 3: Update existing nodes (skip deleted ones)
            for node_data in nodes_data:
                if node_data.get('to_delete', False):
                    continue
                
                node_id = node_data.get('id')
                
                # If it's a database ID (integer), update existing node
                if isinstance(node_id, int):
                    try:
                        step = Steps.objects.get(step_id=node_id, workflow_id=workflow)
                        
                        # Update fields if provided
                        if 'name' in node_data:
                            step.name = node_data['name']
                        if 'description' in node_data:
                            step.description = node_data.get('description', '')
                        if 'instruction' in node_data:
                            step.instruction = node_data.get('instruction', '')
                        if 'order' in node_data:
                            step.order = node_data['order']
                        if 'design' in node_data and node_data['design']:
                            step.design = node_data['design']
                        
                        step.save()
                        logger.info(f"✏️ Updated step: {step.name} (ID: {step.step_id})")
                    
                    except Steps.DoesNotExist:
                        logger.warning(f"Step {node_id} not found for update")
                
                # If it's a temp ID (string), create new node
                elif isinstance(node_id, str) and node_id.startswith('temp-'):
                    try:
                        # Determine role
                        if 'role' in node_data:
                            role_name = node_data['role']
                            role = Roles.objects.filter(name__iexact=role_name).first()
                            if not role:
                                role = Roles.objects.filter(name__iexact='system').first()
                        else:
                            role = Roles.objects.filter(name__iexact='system').first()
                        
                        if not role:
                            role = Roles.objects.create(
                                user_id=workflow.user_id,
                                name='System',
                                description='System role'
                            )
                        
                        design = node_data.get('design', {'x': 100, 'y': 200})
                        
                        # Create new step
                        step = Steps.objects.create(
                            workflow_id=workflow,
                            role_id=role,
                            name=node_data.get('name', 'Unnamed Step'),
                            description=node_data.get('description', ''),
                            instruction=node_data.get('instruction', ''),
                            order=node_data.get('order', 0),
                            design=design
                        )
                        
                        # Map temp_id to real ID
                        temp_id_map[node_id] = step.step_id
                        logger.info(f"✅ Created step: {step.name} (ID: {step.step_id}) from temp {node_id}")
                    
                    except Exception as e:
                        logger.error(f"❌ Error creating step from temp_id {node_id}: {str(e)}")
            
            # Step 4: Update existing edges (skip deleted ones)
            for edge_data in edges_data:
                if edge_data.get('to_delete', False):
                    continue
                
                edge_id = edge_data.get('id')
                
                # If it's a database ID (integer), update existing edge
                if isinstance(edge_id, int):
                    try:
                        transition = StepTransition.objects.get(transition_id=edge_id, workflow_id=workflow)
                        
                        # Update name if provided
                        if 'name' in edge_data:
                            transition.name = edge_data.get('name', '')
                        
                        transition.save()
                        logger.info(f"✏️ Updated transition: {transition.transition_id}")
                    
                    except StepTransition.DoesNotExist:
                        logger.warning(f"Transition {edge_id} not found for update")
            
            # Step 5: Create new edges (skip deleted ones)
            for edge_data in edges_data:
                if edge_data.get('to_delete', False):
                    continue
                
                edge_id = edge_data.get('id')
                
                # If it's a temp ID (string), create new edge
                if isinstance(edge_id, str) and edge_id.startswith('temp-'):
                    try:
                        from_id = edge_data.get('from')
                        to_id = edge_data.get('to')
                        
                        # Resolve temp IDs to real IDs
                        from_step_id = temp_id_map.get(from_id, from_id) if isinstance(from_id, str) else from_id
                        to_step_id = temp_id_map.get(to_id, to_id) if isinstance(to_id, str) else to_id
                        
                        from_step = Steps.objects.get(step_id=from_step_id, workflow_id=workflow)
                        to_step = Steps.objects.get(step_id=to_step_id, workflow_id=workflow)
                        
                        transition = StepTransition.objects.create(
                            workflow_id=workflow,
                            from_step_id=from_step,
                            to_step_id=to_step,
                            name=edge_data.get('name', '')
                        )
                        
                        logger.info(f"✅ Created transition: {from_step.name} -> {to_step.name}")
                    
                    except Exception as e:
                        logger.error(f"❌ Error creating edge from temp_id {edge_id}: {str(e)}")
            
            # Return updated workflow
            output_serializer = WorkflowGraphResponseSerializer(workflow)
            response_data = output_serializer.data
            
            # Add temp_id mapping to response for frontend sync
            if temp_id_map:
                response_data['temp_id_mapping'] = temp_id_map
                logger.info(f"📍 Temp ID mappings: {temp_id_map}")
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"❌ Error updating workflow graph: {str(e)}")
            return Response(
                {'error': f'Failed to update workflow graph: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], url_path='steps')
    def list_steps(self, request, workflow_id=None):
        """Get all steps in a workflow."""
        workflow = self.get_object()
        steps = Steps.objects.filter(workflow_id=workflow).order_by('order')
        serializer = StepSerializer(steps, many=True)
        
        return Response({
            'workflow_id': workflow.workflow_id,
            'workflow_name': workflow.name,
            'steps': serializer.data,
            'count': steps.count()
        })
    
    @action(detail=True, methods=['get'], url_path='transitions')
    def list_transitions(self, request, workflow_id=None):
        """Get all transitions in a workflow."""
        workflow = self.get_object()
        transitions = StepTransition.objects.filter(workflow_id=workflow)
        serializer = TransitionSerializer(transitions, many=True)
        
        return Response({
            'workflow_id': workflow.workflow_id,
            'workflow_name': workflow.name,
            'transitions': serializer.data,
            'count': transitions.count()
        })


class StepManagementViewSet(viewsets.ViewSet):
    """ViewSet for managing step details."""
    
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['put'], url_path='(?P<step_id>[^/.]+)/update-details')
    def update_details(self, request, step_id=None):
        """Update step details (name, description, instruction, order, design)."""
        try:
            step = Steps.objects.get(step_id=step_id)
        except Steps.DoesNotExist:
            return Response(
                {'error': f'Step with ID {step_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UpdateStepDetailsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            for field, value in serializer.validated_data.items():
                setattr(step, field, value)
            step.save()
            
            logger.info(f"✅ Updated step: {step.name} (ID: {step.step_id})")
            
            output_serializer = StepSerializer(step)
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"❌ Error updating step: {str(e)}")
            return Response(
                {'error': f'Failed to update step: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class TransitionManagementViewSet(viewsets.ViewSet):
    """ViewSet for managing transition details."""
    
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['put'], url_path='(?P<transition_id>[^/.]+)/update-details')
    def update_details(self, request, transition_id=None):
        """Update transition details (name only)."""
        try:
            transition = StepTransition.objects.get(transition_id=transition_id)
        except StepTransition.DoesNotExist:
            return Response(
                {'error': f'Transition with ID {transition_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UpdateTransitionDetailsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            for field, value in serializer.validated_data.items():
                setattr(transition, field, value)
            transition.save()
            
            logger.info(f"✅ Updated transition: {transition.transition_id}")
            
            output_serializer = TransitionSerializer(transition)
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"❌ Error updating transition: {str(e)}")
            return Response(
                {'error': f'Failed to update transition: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
