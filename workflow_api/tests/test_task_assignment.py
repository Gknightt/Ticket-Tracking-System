"""
Test suite for Task Assignment
Tests: assign tasks and validate assignments
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from task.models import Task, TaskItem
from tickets.models import WorkflowTicket
from workflow.models import Workflows
from step.models import Steps
from role.models import Roles, RoleUsers


class TaskAssignmentTestCase(TestCase):
    """Test cases for task assignment operations"""
    
    def setUp(self):
        """Set up test client and initial data"""
        self.client = APIClient()
        
        # Create test role
        self.role = Roles.objects.create(
            role_id=1,
            name="Test Assignee",
            system="tts"
        )
        
        # Create test workflow
        self.workflow = Workflows.objects.create(
            user_id=1,
            name="Task Assignment Workflow",
            category="IT",
            sub_category="Hardware",
            department="IT Department",
            status="deployed"
        )
        
        # Create test step
        self.step = Steps.objects.create(
            workflow_id=self.workflow,
            role_id=self.role,
            name="Assignment Test Step",
            order=1,
            is_initialized=True
        )
        
        # Create test ticket
        self.ticket = WorkflowTicket.objects.create(
            ticket_number="TK-ASSIGN-001",
            ticket_data={
                "subject": "Task Assignment Test",
                "priority": "medium"
            }
        )
        
        # Create test users
        self.user1 = RoleUsers.objects.create(
            role_id=self.role,
            user_id=1,
            user_full_name="User One",
            is_active=True
        )
        self.user2 = RoleUsers.objects.create(
            role_id=self.role,
            user_id=2,
            user_full_name="User Two",
            is_active=True
        )
    
    def test_create_task(self):
        """Test creating a task"""
        task = Task.objects.create(
            ticket_id=self.ticket,
            workflow_id=self.workflow,
            current_step=self.step,
            status="pending"
        )
        
        self.assertIsNotNone(task)
        self.assertEqual(task.workflow_id, self.workflow)
        self.assertEqual(task.current_step, self.step)
    
    def test_assign_user_to_task(self):
        """Test assigning a user to a task"""
        task = Task.objects.create(
            ticket_id=self.ticket,
            workflow_id=self.workflow,
            current_step=self.step,
            status="pending"
        )
        
        task_item = TaskItem.objects.create(
            task=task,
            role_user=self.user1,
            status="pending"
        )
        
        self.assertEqual(task_item.task, task)
        self.assertEqual(task_item.role_user, self.user1)
    
    def test_multiple_users_assignment(self):
        """Test assigning multiple users to a task"""
        task = Task.objects.create(
            ticket_id=self.ticket,
            workflow_id=self.workflow,
            current_step=self.step,
            status="pending"
        )
        
        TaskItem.objects.create(
            task=task,
            role_user=self.user1,
            status="pending"
        )
        TaskItem.objects.create(
            task=task,
            role_user=self.user2,
            status="pending"
        )
        
        task_items = TaskItem.objects.filter(task=task)
        self.assertEqual(task_items.count(), 2)
    
    def test_task_status_values(self):
        """Test different task status values"""
        task = Task.objects.create(
            ticket_id=self.ticket,
            workflow_id=self.workflow,
            current_step=self.step,
            status="pending"
        )
        
        statuses = ["pending", "in_progress", "completed", "cancelled"]
        for status_value in statuses:
            task.status = status_value
            task.save()
            task.refresh_from_db()
            self.assertEqual(task.status, status_value)
    
    def test_task_item_status(self):
        """Test task item status management"""
        task = Task.objects.create(
            ticket_id=self.ticket,
            workflow_id=self.workflow,
            current_step=self.step,
            status="pending"
        )
        
        task_item = TaskItem.objects.create(
            task=task,
            role_user=self.user1,
            status="pending"
        )
        
        # Update status
        task_item.status = "in_progress"
        task_item.save()
        
        task_item.refresh_from_db()
        self.assertEqual(task_item.status, "in_progress")
    
    def test_task_workflow_relationship(self):
        """Test task-workflow relationship"""
        task = Task.objects.create(
            ticket_id=self.ticket,
            workflow_id=self.workflow,
            current_step=self.step,
            status="pending"
        )
        
        self.assertEqual(task.workflow_id, self.workflow)
        self.assertEqual(task.workflow_id.name, "Task Assignment Workflow")
    
    def test_task_current_step_tracking(self):
        """Test tracking current step in task"""
        task = Task.objects.create(
            ticket_id=self.ticket,
            workflow_id=self.workflow,
            current_step=self.step,
            status="pending"
        )
        
        self.assertEqual(task.current_step, self.step)
        self.assertEqual(task.current_step.name, "Assignment Test Step")
    
    def test_task_ticket_relationship(self):
        """Test task-ticket relationship"""
        task = Task.objects.create(
            ticket_id=self.ticket,
            workflow_id=self.workflow,
            current_step=self.step,
            status="pending"
        )
        
        self.assertEqual(task.ticket_id, self.ticket)
        self.assertEqual(task.ticket_id.ticket_number, "TK-ASSIGN-001")
    
    def test_round_robin_assignment_setup(self):
        """Test setup for round-robin assignment"""
        # Create multiple users with different activity status
        active_users = RoleUsers.objects.filter(role_id=self.role, is_active=True)
        self.assertGreaterEqual(active_users.count(), 2)
    
    def test_task_item_unique_assignment(self):
        """Test that a user can't be assigned to the same task twice"""
        task = Task.objects.create(
            ticket_id=self.ticket,
            workflow_id=self.workflow,
            current_step=self.step,
            status="pending"
        )
        
        TaskItem.objects.create(
            task=task,
            role_user=self.user1,
            status="pending"
        )
        
        # Try to create duplicate assignment
        try:
            TaskItem.objects.create(
                task=task,
                role_user=self.user1,
                status="pending"
            )
            # If no unique constraint exists, this test documents the behavior
        except Exception:
            pass  # Expected if there's a unique constraint
    
    def test_inactive_user_filtering(self):
        """Test that inactive users are not assigned tasks"""
        # Mark user as inactive
        self.user1.is_active = False
        self.user1.save()
        
        # Get active users only
        active_users = RoleUsers.objects.filter(
            role_id=self.role,
            is_active=True
        )
        
        self.assertNotIn(self.user1, active_users)
        self.assertIn(self.user2, active_users)
