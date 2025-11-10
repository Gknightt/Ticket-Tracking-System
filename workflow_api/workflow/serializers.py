from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Workflows, Category
from step.models import Steps, StepTransition
from role.models import Roles
import logging

logger = logging.getLogger(__name__)


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for workflow categories"""
    class Meta:
        model = Category
        fields = ['category_id', 'name', 'parent']


class WorkflowBasicSerializer(serializers.ModelSerializer):
    """Basic workflow information serializer"""
    class Meta:
        model = Workflows
        fields = [
            'workflow_id',
            'user_id',
            'name',
            'description',
            'category',
            'sub_category',
            'department',
            'status',
            'is_published',
            'end_logic',
            'low_sla',
            'medium_sla',
            'high_sla',
            'urgent_sla',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['workflow_id', 'created_at', 'updated_at']


class GraphNodeDesignSerializer(serializers.Serializer):
    """Serializer for node design coordinates"""
    x = serializers.FloatField()
    y = serializers.FloatField()


class GraphNodeForCreationSerializer(serializers.Serializer):
    """Serializer for graph nodes during creation (uses temp_id)"""
    temp_id = serializers.CharField(max_length=50, required=True)
    type = serializers.ChoiceField(choices=['start', 'task', 'end'], required=True)
    label = serializers.CharField(max_length=255, required=True)
    role_id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(max_length=256, required=False, allow_blank=True)
    instruction = serializers.CharField(required=False, allow_blank=True)
    order = serializers.IntegerField(required=False, default=0)
    design = GraphNodeDesignSerializer(required=False, allow_null=True)


class GraphNodeForResponseSerializer(serializers.Serializer):
    """Serializer for graph nodes in responses (uses database id)"""
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    role = serializers.CharField(max_length=100)
    description = serializers.CharField()
    instruction = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    design = GraphNodeDesignSerializer()


class GraphEdgeForCreationSerializer(serializers.Serializer):
    """Serializer for graph edges during creation (uses temp_id)"""
    from_temp_id = serializers.CharField(max_length=50, required=True)
    to_temp_id = serializers.CharField(max_length=50, required=True)
    name = serializers.CharField(max_length=64, required=False, allow_blank=True)


class GraphEdgeForResponseSerializer(serializers.Serializer):
    """Serializer for graph edges in responses (uses database id)"""
    id = serializers.IntegerField()
    from_step_id = serializers.IntegerField(source='from')
    to_step_id = serializers.IntegerField(source='to')
    name = serializers.CharField()


class WorkflowGraphForCreationSerializer(serializers.Serializer):
    """Serializer for workflow graph during creation"""
    nodes = GraphNodeForCreationSerializer(many=True)
    edges = GraphEdgeForCreationSerializer(many=True)

    def validate_nodes(self, nodes):
        """Validate nodes structure"""
        if not nodes:
            raise serializers.ValidationError("Workflow must have at least one node")
        
        # Check for duplicate temp_ids
        temp_ids = [node['temp_id'] for node in nodes]
        if len(temp_ids) != len(set(temp_ids)):
            raise serializers.ValidationError("Node temp_ids must be unique")
        
        # Check for start and end nodes
        node_types = [node['type'] for node in nodes]
        if 'start' not in node_types:
            raise serializers.ValidationError("Workflow must have exactly one 'start' node")
        if 'end' not in node_types:
            raise serializers.ValidationError("Workflow must have exactly one 'end' node")
        
        start_count = node_types.count('start')
        end_count = node_types.count('end')
        if start_count != 1:
            raise serializers.ValidationError(f"Workflow must have exactly one 'start' node, found {start_count}")
        if end_count != 1:
            raise serializers.ValidationError(f"Workflow must have exactly one 'end' node, found {end_count}")
        
        # Validate task nodes have role_id
        for node in nodes:
            if node['type'] == 'task':
                if 'role_id' not in node or node['role_id'] is None:
                    raise serializers.ValidationError(f"Task node '{node['temp_id']}' must have a valid role_id")
                
                # Verify role exists
                try:
                    Roles.objects.get(role_id=node['role_id'])
                except Roles.DoesNotExist:
                    raise serializers.ValidationError(f"Role with ID {node['role_id']} does not exist")
        
        return nodes

    def validate_edges(self, edges):
        """Validate edges structure"""
        if not edges:
            raise serializers.ValidationError("Workflow must have at least one transition")
        
        return edges

    def validate(self, attrs):
        """Validate complete graph structure"""
        nodes = attrs.get('nodes', [])
        edges = attrs.get('edges', [])
        
        if not nodes or not edges:
            raise serializers.ValidationError("Graph must contain both nodes and edges")
        
        # Create temp_id to node mapping
        node_map = {node['temp_id']: node for node in nodes}
        temp_ids = set(node_map.keys())
        
        # Validate edges reference existing nodes
        for edge in edges:
            if edge['from_temp_id'] not in temp_ids:
                raise serializers.ValidationError(f"Edge references non-existent node: {edge['from_temp_id']}")
            if edge['to_temp_id'] not in temp_ids:
                raise serializers.ValidationError(f"Edge references non-existent node: {edge['to_temp_id']}")
            
            # No self-loops
            if edge['from_temp_id'] == edge['to_temp_id']:
                raise serializers.ValidationError(f"Self-loop not allowed: {edge['from_temp_id']} -> {edge['to_temp_id']}")
            
            # No edges from/to start or to end (except edges TO end and FROM start)
            from_node = node_map[edge['from_temp_id']]
            to_node = node_map[edge['to_temp_id']]
            
            if from_node['type'] == 'end':
                raise serializers.ValidationError(f"Cannot have outgoing edges from 'end' node {edge['from_temp_id']}")
            if to_node['type'] == 'start':
                raise serializers.ValidationError(f"Cannot have incoming edges to 'start' node {edge['to_temp_id']}")
        
        # Validate graph connectivity using BFS
        adjacency = {node['temp_id']: [] for node in nodes}
        for edge in edges:
            adjacency[edge['from_temp_id']].append(edge['to_temp_id'])
        
        # Find start node
        start_node = next((n for n in nodes if n['type'] == 'start'), None)
        end_node = next((n for n in nodes if n['type'] == 'end'), None)
        
        # BFS to check connectivity
        visited = set()
        queue = [start_node['temp_id']]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            queue.extend(adjacency.get(current, []))
        
        # Check all nodes are reachable from start
        unreachable = set(temp_ids) - visited
        if unreachable:
            raise serializers.ValidationError(f"Unreachable nodes from start: {unreachable}")
        
        # Check end node is reachable
        if end_node['temp_id'] not in visited:
            raise serializers.ValidationError("End node is not reachable from start node")
        
        return attrs


class CreateWorkflowSerializer(serializers.Serializer):
    """Serializer for creating workflows with graph"""
    name = serializers.CharField(max_length=64, required=True)
    description = serializers.CharField(max_length=256, required=False, allow_blank=True)
    category = serializers.CharField(max_length=64, required=True)
    sub_category = serializers.CharField(max_length=64, required=True)
    department = serializers.CharField(max_length=64, required=True)
    end_logic = serializers.ChoiceField(
        choices=['', 'asset', 'budget', 'notification'],
        required=False,
        allow_blank=True
    )
    low_sla = serializers.DurationField(required=False, allow_null=True)
    medium_sla = serializers.DurationField(required=False, allow_null=True)
    high_sla = serializers.DurationField(required=False, allow_null=True)
    urgent_sla = serializers.DurationField(required=False, allow_null=True)
    graph = WorkflowGraphForCreationSerializer(required=True)
    
    def validate_name(self, value):
        """Check if workflow name already exists"""
        if Workflows.objects.filter(name=value).exists():
            raise serializers.ValidationError(f"Workflow with name '{value}' already exists")
        return value
    
    def validate(self, attrs):
        """Validate SLA ordering"""
        slas = {
            'urgent': attrs.get('urgent_sla'),
            'high': attrs.get('high_sla'),
            'medium': attrs.get('medium_sla'),
            'low': attrs.get('low_sla'),
        }
        
        sla_list = [
            ('urgent_sla', slas['urgent']),
            ('high_sla', slas['high']),
            ('medium_sla', slas['medium']),
            ('low_sla', slas['low']),
        ]
        
        for i in range(len(sla_list) - 1):
            current_name, current = sla_list[i]
            next_name, next_val = sla_list[i + 1]
            if current and next_val and current >= next_val:
                raise serializers.ValidationError(
                    f"{current_name} should be less than {next_name} (i.e., urgent < high < medium < low)"
                )
        
        return attrs


class UpdateWorkflowDetailsSerializer(serializers.Serializer):
    """Serializer for updating workflow details (non-graph fields)"""
    description = serializers.CharField(max_length=256, required=False, allow_blank=True)
    category = serializers.CharField(max_length=64, required=False)
    sub_category = serializers.CharField(max_length=64, required=False)
    department = serializers.CharField(max_length=64, required=False)
    end_logic = serializers.ChoiceField(
        choices=['', 'asset', 'budget', 'notification'],
        required=False,
        allow_blank=True
    )
    low_sla = serializers.DurationField(required=False, allow_null=True)
    medium_sla = serializers.DurationField(required=False, allow_null=True)
    high_sla = serializers.DurationField(required=False, allow_null=True)
    urgent_sla = serializers.DurationField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=['draft', 'deployed', 'paused', 'initialized'],
        required=False
    )
    
    def validate(self, attrs):
        """Validate SLA ordering"""
        sla_fields = ['urgent_sla', 'high_sla', 'medium_sla', 'low_sla']
        if any(field in attrs for field in sla_fields):
            instance = self.instance
            slas = {
                'urgent': attrs.get('urgent_sla', instance.urgent_sla),
                'high': attrs.get('high_sla', instance.high_sla),
                'medium': attrs.get('medium_sla', instance.medium_sla),
                'low': attrs.get('low_sla', instance.low_sla),
            }
            
            sla_list = [
                ('urgent_sla', slas['urgent']),
                ('high_sla', slas['high']),
                ('medium_sla', slas['medium']),
                ('low_sla', slas['low']),
            ]
            
            for i in range(len(sla_list) - 1):
                current_name, current = sla_list[i]
                next_name, next_val = sla_list[i + 1]
                if current and next_val and current >= next_val:
                    raise serializers.ValidationError(
                        f"{current_name} should be less than {next_name} (i.e., urgent < high < medium < low)"
                    )
        
        return attrs


class UpdateWorkflowGraphSerializer(serializers.Serializer):
    """Serializer for updating workflow graph (steps and transitions)"""
    graph = WorkflowGraphForCreationSerializer(required=True)


class GraphNodeForUpdateSerializer(serializers.Serializer):
    """Serializer for graph nodes during update (supports both database IDs and temp IDs, with delete flag)"""
    id = serializers.CharField(required=True)  # Can be integer (from DB) or string (temp ID like "temp-1")
    name = serializers.CharField(max_length=255, required=False)
    role = serializers.CharField(max_length=100, required=False)  # For new nodes, use role name
    description = serializers.CharField(max_length=256, required=False, allow_blank=True)
    instruction = serializers.CharField(required=False, allow_blank=True)
    order = serializers.IntegerField(required=False)
    design = GraphNodeDesignSerializer(required=False)
    to_delete = serializers.BooleanField(required=False, default=False)


class GraphEdgeForUpdateSerializer(serializers.Serializer):
    """Serializer for graph edges during update (supports both database IDs and temp IDs, with delete flag)"""
    id = serializers.CharField(required=True)  # Can be integer (from DB) or string (temp ID like "temp-e1")
    from_id = serializers.CharField(required=False)  # Can be integer (step_id) or string (temp ID)
    to_id = serializers.CharField(required=False)  # Can be integer (step_id) or string (temp ID)
    name = serializers.CharField(max_length=64, required=False, allow_blank=True)
    to_delete = serializers.BooleanField(required=False, default=False)

    def to_internal_value(self, data):
        """Map 'from'/'to' fields to 'from_id'/'to_id' for internal consistency"""
        if 'from' in data and 'from_id' not in data:
            data = dict(data)
            data['from_id'] = data.pop('from')
        if 'to' in data and 'to_id' not in data:
            data = dict(data)
            data['to_id'] = data.pop('to')
        return super().to_internal_value(data)


class WorkflowGraphForUpdateSerializer(serializers.Serializer):
    """Serializer for updating workflow graph incrementally (create, update, delete nodes and edges)"""
    nodes = GraphNodeForUpdateSerializer(many=True, required=False)
    edges = GraphEdgeForUpdateSerializer(many=True, required=False)

    def validate(self, attrs):
        """Validate graph structure for updates"""
        nodes = attrs.get('nodes', [])
        edges = attrs.get('edges', [])
        
        # Build mappings for validation
        node_ids = {}
        for node in nodes:
            if not node.get('to_delete', False):  # Skip deleted nodes in validation
                node_ids[str(node['id'])] = node
        
        # Validate edges reference existing or new nodes
        for edge in edges:
            if not edge.get('to_delete', False):  # Skip deleted edges in validation
                from_id = str(edge.get('from_id', ''))
                to_id = str(edge.get('to_id', ''))
                
                # Only validate if these are new edges (have from_id and to_id)
                if from_id and to_id:
                    # Check references exist in nodes being sent or are existing DB IDs
                    # (we can't validate DB IDs here, backend will handle that)
                    pass
        
        return attrs


class UpdateWorkflowGraphSerializerV2(serializers.Serializer):
    """Serializer for updating workflow graph with incremental changes"""
    graph = WorkflowGraphForUpdateSerializer(required=True)


class StepSerializer(serializers.ModelSerializer):
    """Serializer for step details"""
    role_name = serializers.CharField(source='role_id.name', read_only=True)
    
    class Meta:
        model = Steps
        fields = [
            'step_id',
            'workflow_id',
            'role_id',
            'role_name',
            'name',
            'description',
            'instruction',
            'order',
            'design',
            'is_initialized',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['step_id', 'workflow_id', 'created_at', 'updated_at']


class UpdateStepDetailsSerializer(serializers.Serializer):
    """Serializer for updating step details (non-relationship fields)"""
    name = serializers.CharField(max_length=64, required=False)
    description = serializers.CharField(max_length=256, required=False, allow_blank=True)
    instruction = serializers.CharField(required=False, allow_blank=True)
    order = serializers.IntegerField(required=False)
    design = GraphNodeDesignSerializer(required=False)


class TransitionSerializer(serializers.ModelSerializer):
    """Serializer for transition details"""
    from_step_name = serializers.CharField(source='from_step_id.name', read_only=True)
    to_step_name = serializers.CharField(source='to_step_id.name', read_only=True)
    
    class Meta:
        model = StepTransition
        fields = [
            'transition_id',
            'workflow_id',
            'from_step_id',
            'from_step_name',
            'to_step_id',
            'to_step_name',
            'name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['transition_id', 'workflow_id', 'created_at', 'updated_at']


class UpdateTransitionDetailsSerializer(serializers.Serializer):
    """Serializer for updating transition details (name only)"""
    name = serializers.CharField(max_length=64, required=False, allow_blank=True)


class WorkflowGraphResponseSerializer(serializers.ModelSerializer):
    """Serializer for workflow with graph in new format (uses database IDs)"""
    graph = serializers.SerializerMethodField()
    
    class Meta:
        model = Workflows
        fields = [
            'workflow_id',
            'user_id',
            'name',
            'description',
            'category',
            'sub_category',
            'department',
            'status',
            'is_published',
            'end_logic',
            'low_sla',
            'medium_sla',
            'high_sla',
            'urgent_sla',
            'graph',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['workflow_id', 'created_at', 'updated_at']
    
    def get_graph(self, obj):
        """Convert steps and transitions to graph format with database IDs"""
        steps = Steps.objects.filter(workflow_id=obj).order_by('order')
        transitions = StepTransition.objects.filter(workflow_id=obj)
        
        # Build nodes with database IDs
        nodes = []
        for step in steps:
            design = step.design if step.design else {'x': 100 + (step.order * 250), 'y': 200}
            node = {
                'id': step.step_id,
                'name': step.name,
                'role': step.role_id.name if step.role_id else 'System',
                'description': step.description or '',
                'instruction': step.instruction or '',
                'created_at': step.created_at.isoformat() if step.created_at else '',
                'updated_at': step.updated_at.isoformat() if step.updated_at else '',
                'design': design,
            }
            nodes.append(node)
        
        # Build edges with database IDs
        edges = []
        for transition in transitions:
            edge = {
                'id': transition.transition_id,
                'from': transition.from_step_id.step_id if transition.from_step_id else None,
                'to': transition.to_step_id.step_id if transition.to_step_id else None,
                'name': transition.name or '',
            }
            edges.append(edge)
        
        return {
            'nodes': nodes,
            'edges': edges,
        }


class WorkflowDetailSerializer(serializers.ModelSerializer):
    """Detailed workflow serializer with steps and transitions (old format, for backward compatibility)"""
    steps = StepSerializer(source='steps_set', many=True, read_only=True)
    transitions = TransitionSerializer(source='steptransition_set', many=True, read_only=True)
    
    class Meta:
        model = Workflows
        fields = [
            'workflow_id',
            'user_id',
            'name',
            'description',
            'category',
            'sub_category',
            'department',
            'status',
            'is_published',
            'end_logic',
            'low_sla',
            'medium_sla',
            'high_sla',
            'urgent_sla',
            'steps',
            'transitions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['workflow_id', 'created_at', 'updated_at']
