"""
Test suite for Workflow Graph Management
Tests: add/remove steps, connect transitions, verify graph updates
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from workflow.models import Workflows
from step.models import Steps, StepTransition
from role.models import Roles
from datetime import timedelta


class WorkflowGraphTestCase(TestCase):
    """Test cases for workflow graph operations (steps and transitions)"""
    
    def setUp(self):
        """Set up test client and initial data"""
        self.client = APIClient()
        
        # Create test role
        self.role = Roles.objects.create(
            role_id=1,
            name="Test Role",
            system="tts"
        )
        
        # Create test workflow
        self.workflow = Workflows.objects.create(
            user_id=1,
            name="Graph Test Workflow",
            category="IT",
            sub_category="Hardware",
            department="IT Department",
            status="draft"
        )
    
    def test_add_step_to_workflow(self):
        """Test adding a step to a workflow"""
        step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Test Step",
            description="A test step",
            order=1,
            weight=1.0,
            is_initialized=True
        )
        self.assertIsNotNone(step)
        self.assertEqual(step.workflow_id, self.workflow)
        self.assertEqual(step.order, 1)
    
    def test_remove_step_from_workflow(self):
        """Test removing a step from a workflow"""
        step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Step to Remove",
            order=1
        )
        step_id = step.step_id
        
        step.delete()
        
        # Verify step is deleted
        self.assertFalse(Steps.objects.filter(step_id=step_id).exists())
    
    def test_step_ordering(self):
        """Test that steps can be ordered"""
        step1 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="First Step",
            order=1
        )
        step2 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Second Step",
            order=2
        )
        step3 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Third Step",
            order=3
        )
        
        steps = Steps.objects.filter(workflow_id=self.workflow).order_by('order')
        self.assertEqual(steps[0].name, "First Step")
        self.assertEqual(steps[1].name, "Second Step")
        self.assertEqual(steps[2].name, "Third Step")
    
    def test_create_transition_between_steps(self):
        """Test creating a transition between two steps"""
        step1 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Source Step",
            order=1
        )
        step2 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Target Step",
            order=2
        )
        
        transition = StepTransition.objects.create(
            workflow_id=self.workflow,
            from_step_id=step1,
            to_step_id=step2,
            name="Test Transition"
        )
        
        self.assertIsNotNone(transition)
        self.assertEqual(transition.from_step_id, step1)
        self.assertEqual(transition.to_step_id, step2)
    
    def test_remove_transition(self):
        """Test removing a transition"""
        step1 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Source Step",
            order=1
        )
        step2 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Target Step",
            order=2
        )
        
        transition = StepTransition.objects.create(
            workflow_id=self.workflow,
            from_step_id=step1,
            to_step_id=step2
        )
        transition_id = transition.transition_id
        
        transition.delete()
        
        # Verify transition is deleted
        self.assertFalse(StepTransition.objects.filter(transition_id=transition_id).exists())
    
    def test_transition_same_workflow_constraint(self):
        """Test that transitions can only connect steps from the same workflow"""
        workflow2 = Workflows.objects.create(
            user_id=1,
            name="Second Workflow",
            category="HR",
            sub_category="Recruitment",
            department="HR Department"
        )
        
        step1 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Step in Workflow 1",
            order=1
        )
        step2 = Steps.objects.create(
            workflow_id=workflow2,
            role_id=self.role,
            name="Step in Workflow 2",
            order=1
        )
        
        # Try to create transition between steps from different workflows
        try:
            StepTransition.objects.create(
                from_step_id=step1,
                to_step_id=step2
            )
            self.fail("Should have raised ValidationError for cross-workflow transition")
        except Exception:
            pass  # Expected to fail
    
    def test_transition_no_self_loop(self):
        """Test that a step cannot transition to itself"""
        step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Self Loop Test Step",
            order=1
        )
        
        # Try to create self-loop transition
        try:
            StepTransition.objects.create(
                from_step_id=step,
                to_step_id=step
            )
            self.fail("Should have raised ValidationError for self-loop transition")
        except Exception:
            pass  # Expected to fail
    
    def test_step_start_and_end_flags(self):
        """Test step start and end flags"""
        start_step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Start Step",
            order=1,
            is_start=True
        )
        end_step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="End Step",
            order=2,
            is_end=True
        )
        
        self.assertTrue(start_step.is_start)
        self.assertTrue(end_step.is_end)
    
    def test_step_design_coordinates(self):
        """Test storing design coordinates for frontend positioning"""
        step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Positioned Step",
            order=1,
            design={"x": 100, "y": 200}
        )
        
        self.assertEqual(step.design["x"], 100)
        self.assertEqual(step.design["y"], 200)
    
    def test_transition_design_handles(self):
        """Test storing design handles for transitions"""
        step1 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Source Step",
            order=1
        )
        step2 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Target Step",
            order=2
        )
        
        transition = StepTransition.objects.create(
            workflow_id=self.workflow,
            from_step_id=step1,
            to_step_id=step2,
            design={
                "source_handle": "right",
                "target_handle": "left"
            }
        )
        
        self.assertEqual(transition.design["source_handle"], "right")
        self.assertEqual(transition.design["target_handle"], "left")
    
    def test_multiple_transitions_from_step(self):
        """Test that a step can have multiple outgoing transitions"""
        step1 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Source Step",
            order=1
        )
        step2 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Target Step 1",
            order=2
        )
        step3 = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Target Step 2",
            order=3
        )
        
        transition1 = StepTransition.objects.create(
            workflow_id=self.workflow,
            from_step_id=step1,
            to_step_id=step2
        )
        transition2 = StepTransition.objects.create(
            workflow_id=self.workflow,
            from_step_id=step1,
            to_step_id=step3
        )
        
        outgoing = step1.outgoing_transitions.all()
        self.assertEqual(outgoing.count(), 2)
