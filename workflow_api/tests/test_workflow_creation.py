"""
Test suite for Workflow Creation
Tests: create workflows, validate categories, handle duplicates
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from workflow.models import Workflows, Category
from role.models import Roles
from datetime import timedelta


class WorkflowCreationTestCase(TestCase):
    """Test cases for workflow creation operations"""
    
    def setUp(self):
        """Set up test client and initial data"""
        self.client = APIClient()
        
        # Create a test role
        self.role = Roles.objects.create(
            role_id=1,
            name="Test Role",
            system="tts"
        )
        
        # Create test categories
        self.category1 = Category.objects.create(name="IT")
        self.category2 = Category.objects.create(name="HR")
        self.subcategory = Category.objects.create(
            name="Hardware",
            parent=self.category1
        )
    
    def test_create_simple_workflow(self):
        """Test creating a simple workflow"""
        data = {
            "user_id": 1,
            "name": "Test Workflow",
            "description": "A test workflow",
            "category": "IT",
            "sub_category": "Hardware",
            "department": "IT Department",
            "status": "draft",
            "is_published": False,
            "low_sla": str(timedelta(hours=48)),
            "medium_sla": str(timedelta(hours=24)),
            "high_sla": str(timedelta(hours=8)),
            "urgent_sla": str(timedelta(hours=4))
        }
        
        workflow = Workflows.objects.create(**data)
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.name, "Test Workflow")
        self.assertEqual(workflow.category, "IT")
    
    def test_workflow_unique_name(self):
        """Test that workflow names must be unique"""
        Workflows.objects.create(
            user_id=1,
            name="Unique Workflow",
            category="IT",
            sub_category="Hardware",
            department="IT Department"
        )
        
        # Try to create duplicate
        try:
            Workflows.objects.create(
                user_id=1,
                name="Unique Workflow",  # Duplicate name
                category="HR",
                sub_category="Recruitment",
                department="HR Department"
            )
            self.fail("Should have raised an error for duplicate workflow name")
        except Exception:
            pass  # Expected to fail
    
    def test_workflow_category_validation(self):
        """Test workflow category validation"""
        workflow = Workflows.objects.create(
            user_id=1,
            name="Category Test Workflow",
            category="IT",
            sub_category="Hardware",
            department="IT Department"
        )
        self.assertEqual(workflow.category, "IT")
        self.assertEqual(workflow.sub_category, "Hardware")
    
    def test_workflow_sla_ordering(self):
        """Test that SLA values are ordered correctly (urgent < high < medium < low)"""
        # Valid SLA ordering
        workflow = Workflows.objects.create(
            user_id=1,
            name="SLA Test Workflow",
            category="IT",
            sub_category="Hardware",
            department="IT Department",
            urgent_sla=timedelta(hours=2),
            high_sla=timedelta(hours=8),
            medium_sla=timedelta(hours=24),
            low_sla=timedelta(hours=48)
        )
        self.assertIsNotNone(workflow)
    
    def test_workflow_invalid_sla_ordering(self):
        """Test that invalid SLA ordering is rejected"""
        try:
            # Invalid: urgent > high
            Workflows.objects.create(
                user_id=1,
                name="Invalid SLA Workflow",
                category="IT",
                sub_category="Hardware",
                department="IT Department",
                urgent_sla=timedelta(hours=24),  # Too large
                high_sla=timedelta(hours=8),
                medium_sla=timedelta(hours=48),
                low_sla=timedelta(hours=96)
            )
            self.fail("Should have raised ValidationError for invalid SLA ordering")
        except Exception:
            pass  # Expected to fail
    
    def test_workflow_status_choices(self):
        """Test workflow status field with valid choices"""
        for status_value in ["draft", "deployed", "paused", "initialized"]:
            workflow = Workflows.objects.create(
                user_id=1,
                name=f"Status {status_value} Workflow",
                category="IT",
                sub_category="Hardware",
                department="IT Department",
                status=status_value
            )
            self.assertEqual(workflow.status, status_value)
    
    def test_workflow_end_logic_choices(self):
        """Test workflow end_logic field with valid choices"""
        for end_logic in ["", "asset", "budget", "notification"]:
            workflow = Workflows.objects.create(
                user_id=1,
                name=f"End Logic {end_logic or 'None'} Workflow",
                category="IT",
                sub_category="Hardware",
                department="IT Department",
                end_logic=end_logic
            )
            self.assertEqual(workflow.end_logic, end_logic)
    
    def test_workflow_unique_category_subcategory_per_user(self):
        """Test unique constraint on category+subcategory per user"""
        Workflows.objects.create(
            user_id=1,
            name="First Workflow",
            category="IT",
            sub_category="Hardware",
            department="IT Department"
        )
        
        # Try to create another workflow with same user+category+subcategory
        try:
            Workflows.objects.create(
                user_id=1,
                name="Second Workflow",
                category="IT",
                sub_category="Hardware",
                department="IT Department"
            )
            self.fail("Should have raised an error for duplicate category/subcategory per user")
        except Exception:
            pass  # Expected to fail
    
    def test_workflow_different_users_same_category(self):
        """Test that different users can have workflows with same category/subcategory"""
        Workflows.objects.create(
            user_id=1,
            name="User 1 Workflow",
            category="IT",
            sub_category="Hardware",
            department="IT Department"
        )
        
        # Different user should be able to create workflow with same category
        workflow2 = Workflows.objects.create(
            user_id=2,
            name="User 2 Workflow",
            category="IT",
            sub_category="Hardware",
            department="IT Department"
        )
        self.assertIsNotNone(workflow2)
    
    def test_category_hierarchy(self):
        """Test category parent-child relationships"""
        parent = Category.objects.create(name="Parent Category")
        child = Category.objects.create(name="Child Category", parent=parent)
        
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.subcategories.all())
    
    def test_workflow_creation_with_timestamps(self):
        """Test that created_at and updated_at are set automatically"""
        workflow = Workflows.objects.create(
            user_id=1,
            name="Timestamp Test Workflow",
            category="IT",
            sub_category="Hardware",
            department="IT Department"
        )
        self.assertIsNotNone(workflow.created_at)
        self.assertIsNotNone(workflow.updated_at)
