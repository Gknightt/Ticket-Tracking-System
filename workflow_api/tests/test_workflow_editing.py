"""
Test suite for Workflow Editing
Tests: update workflow details, SLAs, and metadata
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from workflow.models import Workflows
from datetime import timedelta


class WorkflowEditingTestCase(TestCase):
    """Test cases for workflow editing operations"""
    
    def setUp(self):
        """Set up test client and initial data"""
        self.client = APIClient()
        
        # Create a test workflow
        self.workflow = Workflows.objects.create(
            user_id=1,
            name="Test Workflow",
            description="Original description",
            category="IT",
            sub_category="Hardware",
            department="IT Department",
            status="draft",
            urgent_sla=timedelta(hours=2),
            high_sla=timedelta(hours=8),
            medium_sla=timedelta(hours=24),
            low_sla=timedelta(hours=48)
        )
    
    def test_update_workflow_description(self):
        """Test updating workflow description"""
        self.workflow.description = "Updated description"
        self.workflow.save()
        
        self.workflow.refresh_from_db()
        self.assertEqual(self.workflow.description, "Updated description")
    
    def test_update_workflow_status(self):
        """Test updating workflow status"""
        self.workflow.status = "deployed"
        self.workflow.save()
        
        self.workflow.refresh_from_db()
        self.assertEqual(self.workflow.status, "deployed")
    
    def test_update_workflow_slas(self):
        """Test updating workflow SLA values"""
        self.workflow.urgent_sla = timedelta(hours=1)
        self.workflow.high_sla = timedelta(hours=4)
        self.workflow.medium_sla = timedelta(hours=12)
        self.workflow.low_sla = timedelta(hours=24)
        self.workflow.save()
        
        self.workflow.refresh_from_db()
        self.assertEqual(self.workflow.urgent_sla, timedelta(hours=1))
        self.assertEqual(self.workflow.low_sla, timedelta(hours=24))
    
    def test_update_workflow_department(self):
        """Test updating workflow department"""
        self.workflow.department = "Updated Department"
        self.workflow.save()
        
        self.workflow.refresh_from_db()
        self.assertEqual(self.workflow.department, "Updated Department")
    
    def test_update_workflow_is_published(self):
        """Test updating workflow is_published flag"""
        self.workflow.is_published = True
        self.workflow.save()
        
        self.workflow.refresh_from_db()
        self.assertTrue(self.workflow.is_published)
    
    def test_update_workflow_end_logic(self):
        """Test updating workflow end_logic"""
        self.workflow.end_logic = "notification"
        self.workflow.save()
        
        self.workflow.refresh_from_db()
        self.assertEqual(self.workflow.end_logic, "notification")
    
    def test_update_workflow_invalid_sla(self):
        """Test that invalid SLA updates are rejected"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.workflow.urgent_sla = timedelta(hours=100)  # Invalid: larger than others
            self.workflow.save()
    
    def test_update_workflow_name_unique(self):
        """Test that workflow name must remain unique on update"""
        from django.db import IntegrityError
        # Create another workflow
        Workflows.objects.create(
            user_id=1,
            name="Another Workflow",
            category="HR",
            sub_category="Recruitment",
            department="HR Department"
        )
        
        # Try to rename first workflow to duplicate name
        with self.assertRaises(IntegrityError):
            self.workflow.name = "Another Workflow"
            self.workflow.save()
    
    def test_update_workflow_timestamps(self):
        """Test that updated_at changes on save"""
        original_updated_at = self.workflow.updated_at
        
        # Make a change
        self.workflow.description = "New description"
        self.workflow.save()
        
        self.workflow.refresh_from_db()
        self.assertNotEqual(self.workflow.updated_at, original_updated_at)
    
    def test_update_workflow_category(self):
        """Test updating workflow category"""
        self.workflow.category = "HR"
        self.workflow.sub_category = "Recruitment"
        self.workflow.save()
        
        self.workflow.refresh_from_db()
        self.assertEqual(self.workflow.category, "HR")
        self.assertEqual(self.workflow.sub_category, "Recruitment")
    
    def test_partial_sla_update(self):
        """Test updating only some SLA values"""
        self.workflow.urgent_sla = timedelta(hours=1)
        # Keep other SLAs the same
        self.workflow.save()
        
        self.workflow.refresh_from_db()
        self.assertEqual(self.workflow.urgent_sla, timedelta(hours=1))
        self.assertEqual(self.workflow.high_sla, timedelta(hours=8))
