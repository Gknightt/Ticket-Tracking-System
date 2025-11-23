"""
Test suite for Ticket Generation
Tests: generate tickets and verify correctness
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from tickets.models import WorkflowTicket
from workflow.models import Workflows
from django.utils import timezone


class TicketGenerationTestCase(TestCase):
    """Test cases for ticket generation operations"""
    
    def setUp(self):
        """Set up test client and initial data"""
        self.client = APIClient()
        
        # Create test workflow
        self.workflow = Workflows.objects.create(
            user_id=1,
            name="Ticket Test Workflow",
            category="IT",
            sub_category="Hardware",
            department="IT Department",
            status="deployed",
            is_published=True
        )
    
    def test_create_ticket(self):
        """Test creating a new ticket"""
        ticket_data = {
            "subject": "Test Ticket",
            "category": "IT",
            "sub_category": "Hardware",
            "department": "IT Department",
            "description": "Test ticket description",
            "priority": "medium",
            "status": "open",
            "employee": "test@example.com"
        }
        
        ticket = WorkflowTicket.objects.create(
            ticket_number="TK-001",
            ticket_data=ticket_data,
            is_task_allocated=False
        )
        
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.ticket_data["subject"], "Test Ticket")
        self.assertEqual(ticket.ticket_data["priority"], "medium")
    
    def test_ticket_number_generation(self):
        """Test that ticket numbers are unique"""
        ticket1 = WorkflowTicket.objects.create(
            ticket_number="TK-001",
            ticket_data={"subject": "Ticket 1"}
        )
        ticket2 = WorkflowTicket.objects.create(
            ticket_number="TK-002",
            ticket_data={"subject": "Ticket 2"}
        )
        
        self.assertNotEqual(ticket1.ticket_number, ticket2.ticket_number)
    
    def test_ticket_with_priority(self):
        """Test creating tickets with different priorities"""
        priorities = ["low", "medium", "high", "urgent"]
        
        for priority in priorities:
            ticket = WorkflowTicket.objects.create(
                ticket_number=f"TK-{priority}",
                ticket_data={
                    "subject": f"{priority} priority ticket",
                    "priority": priority
                }
            )
            self.assertEqual(ticket.ticket_data["priority"], priority)
    
    def test_ticket_with_category(self):
        """Test creating tickets with category information"""
        ticket = WorkflowTicket.objects.create(
            ticket_number="TK-CAT-001",
            ticket_data={
                "subject": "Categorized Ticket",
                "category": "IT",
                "sub_category": "Hardware"
            }
        )
        
        self.assertEqual(ticket.ticket_data["category"], "IT")
        self.assertEqual(ticket.ticket_data["sub_category"], "Hardware")
    
    def test_ticket_task_allocation_flag(self):
        """Test ticket task allocation flag"""
        ticket = WorkflowTicket.objects.create(
            ticket_number="TK-ALLOC-001",
            ticket_data={"subject": "Allocation Test"},
            is_task_allocated=False
        )
        
        self.assertFalse(ticket.is_task_allocated)
        
        # Simulate task allocation
        ticket.is_task_allocated = True
        ticket.save()
        
        ticket.refresh_from_db()
        self.assertTrue(ticket.is_task_allocated)
    
    def test_ticket_with_employee_info(self):
        """Test ticket with employee information"""
        ticket = WorkflowTicket.objects.create(
            ticket_number="TK-EMP-001",
            ticket_data={
                "subject": "Employee Ticket",
                "employee": "john.doe@example.com",
                "employee_name": "John Doe"
            }
        )
        
        self.assertEqual(ticket.ticket_data["employee"], "john.doe@example.com")
    
    def test_ticket_with_description(self):
        """Test ticket with detailed description"""
        description = "This is a detailed description of the issue that needs to be resolved."
        ticket = WorkflowTicket.objects.create(
            ticket_number="TK-DESC-001",
            ticket_data={
                "subject": "Detailed Ticket",
                "description": description
            }
        )
        
        self.assertEqual(ticket.ticket_data["description"], description)
    
    def test_ticket_with_attachments(self):
        """Test ticket with attachments metadata"""
        ticket = WorkflowTicket.objects.create(
            ticket_number="TK-ATT-001",
            ticket_data={
                "subject": "Ticket with Attachments",
                "attachments": [
                    {"filename": "screenshot.png", "size": 1024},
                    {"filename": "log.txt", "size": 512}
                ]
            }
        )
        
        self.assertEqual(len(ticket.ticket_data["attachments"]), 2)
    
    def test_ticket_with_dynamic_data(self):
        """Test ticket with dynamic/custom fields"""
        ticket = WorkflowTicket.objects.create(
            ticket_number="TK-DYN-001",
            ticket_data={
                "subject": "Dynamic Data Ticket",
                "dynamic_data": {
                    "custom_field_1": "value1",
                    "custom_field_2": "value2"
                }
            }
        )
        
        self.assertEqual(
            ticket.ticket_data["dynamic_data"]["custom_field_1"],
            "value1"
        )
    
    def test_ticket_status_values(self):
        """Test creating tickets with different status values"""
        statuses = ["open", "in_progress", "resolved", "closed"]
        
        for status_value in statuses:
            ticket = WorkflowTicket.objects.create(
                ticket_number=f"TK-{status_value}",
                ticket_data={
                    "subject": f"{status_value} ticket",
                    "status": status_value
                }
            )
            self.assertEqual(ticket.ticket_data["status"], status_value)
    
    def test_ticket_department_routing(self):
        """Test ticket department-based routing"""
        ticket = WorkflowTicket.objects.create(
            ticket_number="TK-DEPT-001",
            ticket_data={
                "subject": "Department Routing Test",
                "department": "IT Department",
                "category": "IT",
                "sub_category": "Hardware"
            }
        )
        
        self.assertEqual(ticket.ticket_data["department"], "IT Department")
