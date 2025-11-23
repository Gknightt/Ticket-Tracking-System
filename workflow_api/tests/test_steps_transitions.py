"""
Test suite for Steps and Transitions
Tests: step assignment, weight, priority, and transition logic
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from workflow.models import Workflows
from step.models import Steps, StepTransition
from role.models import Roles
from decimal import Decimal


class StepsTransitionsTestCase(TestCase):
    """Test cases for step and transition specific operations"""
    
    def setUp(self):
        """Set up test client and initial data"""
        self.client = APIClient()
        
        # Create test roles
        self.role1 = Roles.objects.create(
            role_id=1,
            name="Primary Role",
            system="tts"
        )
        self.role2 = Roles.objects.create(
            role_id=2,
            name="Escalation Role",
            system="tts"
        )
        
        # Create test workflow
        self.workflow = Workflows.objects.create(
            user_id=1,
            name="Steps Test Workflow",
            category="IT",
            sub_category="Hardware",
            department="IT Department"
        )
    
    def test_step_role_assignment(self):
        """Test assigning a role to a step"""
        step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Role Assignment Test",
            order=1
        )
        
        self.assertEqual(step.role_id, self.role1)
    
    def test_step_escalation_role(self):
        """Test assigning an escalation role to a step"""
        step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            escalate_to=self.role2,
            name="Escalation Test",
            order=1
        )
        
        self.assertEqual(step.escalate_to, self.role2)
    
    def test_step_weight_values(self):
        """Test setting and validating step weight values"""
        step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Weight Test",
            order=1,
            weight=Decimal("2.5")
        )
        
        self.assertEqual(step.weight, Decimal("2.5"))
    
    def test_step_weight_default(self):
        """Test default weight value for steps"""
        step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Default Weight Test",
            order=1
        )
        
        self.assertEqual(step.weight, Decimal("0.5"))
    
    def test_step_order_priority(self):
        """Test step ordering determines execution priority"""
        step1 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="High Priority",
            order=1
        )
        step2 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Medium Priority",
            order=2
        )
        step3 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Low Priority",
            order=3
        )
        
        steps = list(Steps.objects.filter(workflow_id=self.workflow).order_by('order'))
        self.assertEqual(steps[0].order, 1)
        self.assertEqual(steps[1].order, 2)
        self.assertEqual(steps[2].order, 3)
    
    def test_step_is_initialized_flag(self):
        """Test is_initialized flag for steps"""
        step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Initialized Test",
            order=1,
            is_initialized=True
        )
        
        self.assertTrue(step.is_initialized)
    
    def test_step_instructions(self):
        """Test step instructions field"""
        instructions = "1. Review ticket\n2. Assign to team\n3. Follow up"
        step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Instructions Test",
            order=1,
            instruction=instructions
        )
        
        self.assertEqual(step.instruction, instructions)
    
    def test_transition_naming(self):
        """Test naming transitions"""
        step1 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Step 1",
            order=1
        )
        step2 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Step 2",
            order=2
        )
        
        transition = StepTransition.objects.create(
            workflow_id=self.workflow,
            from_step_id=step1,
            to_step_id=step2,
            name="Approve"
        )
        
        self.assertEqual(transition.name, "Approve")
    
    def test_step_timestamps(self):
        """Test that step timestamps are set automatically"""
        step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Timestamp Test",
            order=1
        )
        
        self.assertIsNotNone(step.created_at)
        self.assertIsNotNone(step.updated_at)
    
    def test_transition_timestamps(self):
        """Test that transition timestamps are set automatically"""
        step1 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Step 1",
            order=1
        )
        step2 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Step 2",
            order=2
        )
        
        transition = StepTransition.objects.create(
            workflow_id=self.workflow,
            from_step_id=step1,
            to_step_id=step2
        )
        
        self.assertIsNotNone(transition.created_at)
        self.assertIsNotNone(transition.updated_at)
    
    def test_step_multiple_weights(self):
        """Test that different steps can have different weights"""
        step1 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Heavy Step",
            order=1,
            weight=Decimal("5.0")
        )
        step2 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Light Step",
            order=2,
            weight=Decimal("1.0")
        )
        
        self.assertEqual(step1.weight, Decimal("5.0"))
        self.assertEqual(step2.weight, Decimal("1.0"))
    
    def test_transition_outgoing_incoming_relationships(self):
        """Test outgoing and incoming transition relationships"""
        step1 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Step 1",
            order=1
        )
        step2 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role1,
            name="Step 2",
            order=2
        )
        
        transition = StepTransition.objects.create(
            workflow_id=self.workflow,
            from_step_id=step1,
            to_step_id=step2
        )
        
        # Check outgoing from step1
        self.assertIn(transition, step1.outgoing_transitions.all())
        
        # Check incoming to step2
        self.assertIn(transition, step2.incoming_transitions.all())
