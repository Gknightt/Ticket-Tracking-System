"""
Test suite for reporting analytics views
Tests dashboard, ticket, workflow, team, and task item analytics endpoints
"""
import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

# Import models from workflow_api apps
from task.models import Task, TaskItem, TaskItemHistory
from tickets.models import WorkflowTicket
from workflow.models import Workflows
from step.models import Steps
from role.models import Roles, RoleUsers
from audit.models import AuditEvent


class AnalyticsTestDataFactory:
    """Factory for creating test data for analytics testing"""
    
    @staticmethod
    def create_roles(count=3):
        """Create test roles"""
        roles = []
        for i in range(count):
            role = Roles.objects.create(
                name=f"Role {i+1}",
                description=f"Test role {i+1}"
            )
            roles.append(role)
        return roles
    
    @staticmethod
    def create_users(count=5):
        """Create test users"""
        users = []
        for i in range(count):
            user = User.objects.create_user(
                username=f"testuser{i+1}",
                email=f"user{i+1}@test.com",
                password="testpass123"
            )
            users.append(user)
        return users
    
    @staticmethod
    def create_role_users(users, roles):
        """Create role-user associations"""
        role_users = []
        for i, user in enumerate(users):
            role = roles[i % len(roles)]
            role_user = RoleUsers.objects.create(
                user_id=user.id,
                user_full_name=f"Test User {i+1}",
                role=role,
                system_id=1
            )
            role_users.append(role_user)
        return role_users
    
    @staticmethod
    def create_workflows(count=3):
        """Create test workflows"""
        workflows = []
        for i in range(count):
            workflow = Workflows.objects.create(
                name=f"Workflow {i+1}",
                description=f"Test workflow {i+1}",
                department=f"Department {(i % 2) + 1}",
                category=f"Category {(i % 2) + 1}"
            )
            workflows.append(workflow)
        return workflows
    
    @staticmethod
    def create_steps(workflows, roles, count_per_workflow=2):
        """Create test steps for workflows"""
        steps = []
        for workflow in workflows:
            for i in range(count_per_workflow):
                step = Steps.objects.create(
                    name=f"Step {i+1} - {workflow.name}",
                    workflow=workflow,
                    role=roles[i % len(roles)] if roles else None,
                    order=i+1
                )
                steps.append(step)
        return steps
    
    @staticmethod
    def create_tickets(count=10):
        """Create test tickets"""
        tickets = []
        priorities = ['Low', 'Medium', 'High', 'Critical']
        for i in range(count):
            ticket = WorkflowTicket.objects.create(
                title=f"Test Ticket {i+1}",
                description=f"Description for ticket {i+1}",
                priority=priorities[i % len(priorities)]
            )
            tickets.append(ticket)
        return tickets
    
    @staticmethod
    def create_tasks(tickets, workflows, steps, count=None):
        """Create test tasks for tickets"""
        if count is None:
            count = len(tickets)
        
        tasks = []
        statuses = ['pending', 'in progress', 'completed']
        
        now = timezone.now()
        for i in range(count):
            ticket = tickets[i % len(tickets)]
            workflow = workflows[i % len(workflows)]
            step = steps[i % len(steps)] if steps else None
            status_val = statuses[i % len(statuses)]
            
            # Create task with timestamps
            task = Task.objects.create(
                ticket=ticket,
                workflow=workflow,
                current_step=step,
                status=status_val,
                created_at=now - timedelta(days=10-i),
            )
            
            # Set resolution time if completed
            if status_val == 'completed':
                task.resolution_time = now - timedelta(days=5-i)
                task.target_resolution = now - timedelta(days=3)
                task.save()
            elif status_val == 'in progress':
                task.target_resolution = now + timedelta(days=2)
                task.save()
            
            tasks.append(task)
        return tasks
    
    @staticmethod
    def create_task_items(tasks, role_users, count_per_task=1):
        """Create test task items for tasks"""
        task_items = []
        origins = ['System', 'Transfer', 'Escalation']
        
        now = timezone.now()
        for task in tasks:
            for i in range(count_per_task):
                role_user = role_users[i % len(role_users)] if role_users else None
                origin = origins[i % len(origins)]
                
                task_item = TaskItem.objects.create(
                    task=task,
                    role_user=role_user,
                    origin=origin,
                    assigned_on=now - timedelta(days=5),
                    acted_on=now - timedelta(days=4) if i % 2 == 0 else None,
                )
                
                # Create history record
                TaskItemHistory.objects.create(
                    task_item=task_item,
                    status='new' if i % 3 == 0 else ('in progress' if i % 3 == 1 else 'resolved'),
                    created_at=now - timedelta(days=5),
                    changed_by=role_user.user_id if role_user else None
                )
                
                task_items.append(task_item)
        
        return task_items
    
    @staticmethod
    def create_audit_events(user_id, count=20):
        """Create test audit events"""
        events = []
        actions = ['create', 'update', 'delete', 'view', 'assign']
        
        now = timezone.now()
        for i in range(count):
            event = AuditEvent.objects.create(
                user_id=user_id,
                username=f"testuser{user_id}",
                action=actions[i % len(actions)],
                entity_type='task',
                entity_id=i+1,
                timestamp=now - timedelta(hours=count-i)
            )
            events.append(event)
        return events


class AnalyticsRootViewTestCase(APITestCase):
    """Test analytics root endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_analytics_root_view(self):
        """Test that root view returns all endpoints"""
        response = self.client.get('/api/reporting/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('endpoints', response.data)
        self.assertIn('message', response.data)
        
        # Check key endpoints are listed
        endpoints = response.data['endpoints']
        self.assertIn('dashboard', endpoints)
        self.assertIn('status_summary', endpoints)
        self.assertIn('sla_compliance', endpoints)
        self.assertIn('task_item_status', endpoints)


class DashboardSummaryViewTestCase(APITestCase):
    """Test dashboard summary endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.factory = AnalyticsTestDataFactory()
        self.roles = self.factory.create_roles(2)
        self.users = self.factory.create_users(3)
        self.role_users = self.factory.create_role_users(self.users, self.roles)
        self.workflows = self.factory.create_workflows(2)
        self.steps = self.factory.create_steps(self.workflows, self.roles)
        self.tickets = self.factory.create_tickets(10)
        self.tasks = self.factory.create_tasks(self.tickets, self.workflows, self.steps)
        self.task_items = self.factory.create_task_items(self.tasks, self.role_users)
    
    def test_dashboard_summary_metrics(self):
        """Test dashboard summary returns correct metrics"""
        response = self.client.get('/api/reporting/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('total_tickets', data)
        self.assertIn('completed_tickets', data)
        self.assertIn('pending_tickets', data)
        self.assertIn('in_progress_tickets', data)
        self.assertIn('sla_compliance_rate', data)
        self.assertIn('escalation_rate', data)
        self.assertIn('total_users', data)
        self.assertIn('total_workflows', data)
        
        # Verify counts are reasonable
        self.assertEqual(data['total_tickets'], 10)
        self.assertGreaterEqual(data['completed_tickets'], 0)
        self.assertGreaterEqual(data['sla_compliance_rate'], 0)
        self.assertLessEqual(data['sla_compliance_rate'], 100)


class StatusSummaryViewTestCase(APITestCase):
    """Test status summary endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.factory = AnalyticsTestDataFactory()
        self.roles = self.factory.create_roles(2)
        self.workflows = self.factory.create_workflows(2)
        self.steps = self.factory.create_steps(self.workflows, self.roles)
        self.tickets = self.factory.create_tickets(9)
        self.tasks = self.factory.create_tasks(self.tickets, self.workflows, self.steps, count=9)
    
    def test_status_summary(self):
        """Test status summary returns distribution"""
        response = self.client.get('/api/reporting/status-summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIsInstance(data, list)
        
        # Should have status entries
        self.assertGreater(len(data), 0)
        
        for item in data:
            self.assertIn('status', item)
            self.assertIn('count', item)
            self.assertIn('percentage', item)
            self.assertGreaterEqual(item['percentage'], 0)
            self.assertLessEqual(item['percentage'], 100)


class SLAComplianceViewTestCase(APITestCase):
    """Test SLA compliance endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.factory = AnalyticsTestDataFactory()
        self.roles = self.factory.create_roles(2)
        self.workflows = self.factory.create_workflows(2)
        self.steps = self.factory.create_steps(self.workflows, self.roles)
        self.tickets = self.factory.create_tickets(10)
        self.tasks = self.factory.create_tasks(self.tickets, self.workflows, self.steps)
    
    def test_sla_compliance(self):
        """Test SLA compliance returns metrics by priority"""
        response = self.client.get('/api/reporting/sla-compliance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIsInstance(data, list)
        
        for item in data:
            self.assertIn('priority', item)
            self.assertIn('total_tasks', item)
            self.assertIn('sla_met', item)
            self.assertIn('sla_breached', item)
            self.assertIn('compliance_rate', item)
            
            # Verify compliance rate is valid percentage
            self.assertGreaterEqual(item['compliance_rate'], 0)
            self.assertLessEqual(item['compliance_rate'], 100)


class TeamPerformanceViewTestCase(APITestCase):
    """Test team performance endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.factory = AnalyticsTestDataFactory()
        self.roles = self.factory.create_roles(2)
        self.users = self.factory.create_users(4)
        self.role_users = self.factory.create_role_users(self.users, self.roles)
        self.workflows = self.factory.create_workflows(2)
        self.steps = self.factory.create_steps(self.workflows, self.roles)
        self.tickets = self.factory.create_tickets(12)
        self.tasks = self.factory.create_tasks(self.tickets, self.workflows, self.steps)
        self.task_items = self.factory.create_task_items(self.tasks, self.role_users)
    
    def test_team_performance(self):
        """Test team performance returns user metrics"""
        response = self.client.get('/api/reporting/team-performance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIsInstance(data, list)
        
        # Should have user entries
        self.assertGreater(len(data), 0)
        
        for item in data:
            self.assertIn('user_id', item)
            self.assertIn('user_name', item)
            self.assertIn('total_tasks', item)
            self.assertIn('completed_tasks', item)
            self.assertIn('completion_rate', item)
            
            # Verify completion rate is valid
            self.assertGreaterEqual(item['completion_rate'], 0)
            self.assertLessEqual(item['completion_rate'], 100)


class WorkflowMetricsViewTestCase(APITestCase):
    """Test workflow metrics endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.factory = AnalyticsTestDataFactory()
        self.roles = self.factory.create_roles(2)
        self.workflows = self.factory.create_workflows(3)
        self.steps = self.factory.create_steps(self.workflows, self.roles)
        self.tickets = self.factory.create_tickets(15)
        self.tasks = self.factory.create_tasks(self.tickets, self.workflows, self.steps)
    
    def test_workflow_metrics(self):
        """Test workflow metrics returns workflow performance data"""
        response = self.client.get('/api/reporting/workflow-metrics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIsInstance(data, list)
        
        for item in data:
            self.assertIn('workflow_id', item)
            self.assertIn('workflow_name', item)
            self.assertIn('total_tasks', item)
            self.assertIn('completed_tasks', item)
            self.assertIn('completion_rate', item)
            self.assertIn('department', item)
            
            self.assertGreaterEqual(item['completion_rate'], 0)
            self.assertLessEqual(item['completion_rate'], 100)


class StepPerformanceViewTestCase(APITestCase):
    """Test step performance endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.factory = AnalyticsTestDataFactory()
        self.roles = self.factory.create_roles(2)
        self.workflows = self.factory.create_workflows(2)
        self.steps = self.factory.create_steps(self.workflows, self.roles, count_per_workflow=3)
        self.tickets = self.factory.create_tickets(12)
        self.tasks = self.factory.create_tasks(self.tickets, self.workflows, self.steps)
    
    def test_step_performance(self):
        """Test step performance returns step metrics"""
        response = self.client.get('/api/reporting/step-performance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIsInstance(data, list)
        
        for item in data:
            self.assertIn('step_id', item)
            self.assertIn('step_name', item)
            self.assertIn('workflow_id', item)
            self.assertIn('total_tasks', item)
            self.assertIn('escalated_tasks', item)


class DepartmentAnalyticsViewTestCase(APITestCase):
    """Test department analytics endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.factory = AnalyticsTestDataFactory()
        self.roles = self.factory.create_roles(2)
        self.workflows = self.factory.create_workflows(4)
        self.steps = self.factory.create_steps(self.workflows, self.roles)
        self.tickets = self.factory.create_tickets(16)
        self.tasks = self.factory.create_tasks(self.tickets, self.workflows, self.steps)
    
    def test_department_analytics(self):
        """Test department analytics returns department metrics"""
        response = self.client.get('/api/reporting/department-analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIsInstance(data, list)
        
        for item in data:
            self.assertIn('department', item)
            self.assertIn('total_tickets', item)
            self.assertIn('completed_tickets', item)
            self.assertIn('completion_rate', item)


class PriorityDistributionViewTestCase(APITestCase):
    """Test priority distribution endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.factory = AnalyticsTestDataFactory()
        self.roles = self.factory.create_roles(2)
        self.workflows = self.factory.create_workflows(2)
        self.steps = self.factory.create_steps(self.workflows, self.roles)
        self.tickets = self.factory.create_tickets(20)
        self.tasks = self.factory.create_tasks(self.tickets, self.workflows, self.steps)
    
    def test_priority_distribution(self):
        """Test priority distribution returns priority breakdown"""
        response = self.client.get('/api/reporting/priority-distribution/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIsInstance(data, list)
        
        total_percentage = 0
        for item in data:
            self.assertIn('priority', item)
            self.assertIn('count', item)
            self.assertIn('percentage', item)
            total_percentage += item['percentage']
        
        # Total should be approximately 100%
        self.assertAlmostEqual(total_percentage, 100, delta=0.1)


class TicketAgeAnalyticsViewTestCase(APITestCase):
    """Test ticket age analytics endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.factory = AnalyticsTestDataFactory()
        self.roles = self.factory.create_roles(2)
        self.workflows = self.factory.create_workflows(2)
        self.steps = self.factory.create_steps(self.workflows, self.roles)
        self.tickets = self.factory.create_tickets(20)
        self.tasks = self.factory.create_tasks(self.tickets, self.workflows, self.steps)
    
    def test_ticket_age_analytics(self):
        """Test ticket age analytics returns age bucket distribution"""
        response = self.client.get('/api/reporting/ticket-age/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIsInstance(data, list)
        
        # Should have age buckets
        self.assertEqual(len(data), 5)
        
        age_buckets = ['0-1 days', '1-7 days', '7-30 days', '30-90 days', '90+ days']
        for i, item in enumerate(data):
            self.assertEqual(item['age_bucket'], age_buckets[i])
            self.assertIn('count', item)
            self.assertIn('percentage', item)


class TaskItemAnalyticsViewTestCase(APITestCase):
    """Test task item analytics endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.factory = AnalyticsTestDataFactory()
        self.roles = self.factory.create_roles(2)
        self.users = self.factory.create_users(3)
        self.role_users = self.factory.create_role_users(self.users, self.roles)
        self.workflows = self.factory.create_workflows(2)
        self.steps = self.factory.create_steps(self.workflows, self.roles)
        self.tickets = self.factory.create_tickets(15)
        self.tasks = self.factory.create_tasks(self.tickets, self.workflows, self.steps)
        self.task_items = self.factory.create_task_items(self.tasks, self.role_users, count_per_task=2)
    
    def test_task_item_status_analytics(self):
        """Test task item status analytics"""
        response = self.client.get('/api/reporting/task-item-status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('total_task_items', data)
        self.assertIn('status_distribution', data)
        
        for item in data['status_distribution']:
            self.assertIn('status', item)
            self.assertIn('count', item)
            self.assertIn('percentage', item)
    
    def test_task_item_origin_analytics(self):
        """Test task item origin analytics"""
        response = self.client.get('/api/reporting/task-item-origin/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('total_assignments', data)
        self.assertIn('origin_distribution', data)
        
        for item in data['origin_distribution']:
            self.assertIn('origin', item)
            self.assertIn('count', item)
            self.assertIn('percentage', item)
    
    def test_task_item_performance_analytics(self):
        """Test task item performance analytics"""
        response = self.client.get('/api/reporting/task-item-performance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('time_to_action_hours', data)
        self.assertIn('resolution_time_hours', data)
        self.assertIn('sla_compliance', data)
        self.assertIn('active_items', data)
        self.assertIn('overdue_items', data)


class AssignmentAnalyticsViewTestCase(APITestCase):
    """Test assignment analytics endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.factory = AnalyticsTestDataFactory()
        self.roles = self.factory.create_roles(3)
        self.users = self.factory.create_users(6)
        self.role_users = self.factory.create_role_users(self.users, self.roles)
        self.workflows = self.factory.create_workflows(2)
        self.steps = self.factory.create_steps(self.workflows, self.roles)
        self.tickets = self.factory.create_tickets(18)
        self.tasks = self.factory.create_tasks(self.tickets, self.workflows, self.steps)
        self.task_items = self.factory.create_task_items(self.tasks, self.role_users)
    
    def test_assignment_analytics(self):
        """Test assignment analytics returns role-based metrics"""
        response = self.client.get('/api/reporting/assignment-analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIsInstance(data, list)
        
        for item in data:
            self.assertIn('role_name', item)
            self.assertIn('total_assignments', item)
            self.assertIn('avg_assignments_per_user', item)
            self.assertIn('total_users_in_role', item)


class AuditActivityViewTestCase(APITestCase):
    """Test audit activity endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test audit data
        self.factory = AnalyticsTestDataFactory()
        self.factory.create_audit_events(self.user.id, count=30)
    
    def test_audit_activity(self):
        """Test audit activity returns user and action metrics"""
        response = self.client.get('/api/reporting/audit-activity/?days=30')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('time_period_days', data)
        self.assertIn('total_events', data)
        self.assertIn('user_activity', data)
        self.assertIn('action_activity', data)
        
        self.assertEqual(data['time_period_days'], 30)
        self.assertGreater(data['total_events'], 0)


class AggregatedReportsTestCase(APITestCase):
    """Test aggregated reporting endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create comprehensive test data
        self.factory = AnalyticsTestDataFactory()
        self.roles = self.factory.create_roles(3)
        self.users = self.factory.create_users(5)
        self.role_users = self.factory.create_role_users(self.users, self.roles)
        self.workflows = self.factory.create_workflows(4)
        self.steps = self.factory.create_steps(self.workflows, self.roles)
        self.tickets = self.factory.create_tickets(30)
        self.tasks = self.factory.create_tasks(self.tickets, self.workflows, self.steps)
        self.task_items = self.factory.create_task_items(self.tasks, self.role_users, count_per_task=2)
    
    def test_aggregated_tickets_report(self):
        """Test aggregated tickets report"""
        response = self.client.get('/api/reporting/reports/tickets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('date_range', data)
        self.assertIn('dashboard', data)
        self.assertIn('status_summary', data)
        self.assertIn('sla_compliance', data)
        self.assertIn('priority_distribution', data)
        self.assertIn('ticket_age', data)
        
        dashboard = data['dashboard']
        self.assertIn('total_tickets', dashboard)
        self.assertIn('completion_rate', dashboard)
    
    def test_aggregated_workflows_report(self):
        """Test aggregated workflows report"""
        response = self.client.get('/api/reporting/reports/workflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('date_range', data)
        self.assertIn('workflow_metrics', data)
        self.assertIn('department_analytics', data)
        self.assertIn('step_performance', data)
    
    def test_aggregated_tasks_report(self):
        """Test aggregated tasks report"""
        response = self.client.get('/api/reporting/reports/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('date_range', data)
        self.assertIn('summary', data)
        self.assertIn('status_distribution', data)
        self.assertIn('origin_distribution', data)
        self.assertIn('performance', data)
        self.assertIn('user_performance', data)


class UtilityFunctionTestCase(TestCase):
    """Test utility functions"""
    
    def test_convert_timedelta_to_hours(self):
        """Test timedelta conversion utility"""
        from .utils import convert_timedelta_to_hours
        from datetime import timedelta
        
        # Test conversion
        td = timedelta(hours=5, minutes=30)
        hours = convert_timedelta_to_hours(td)
        self.assertAlmostEqual(hours, 5.5, places=1)
        
        # Test None
        result = convert_timedelta_to_hours(None)
        self.assertIsNone(result)
    
    def test_build_date_range_filters(self):
        """Test date range filter builder"""
        from .utils import build_date_range_filters
        from datetime import datetime
        
        start_display, end_display, filters = build_date_range_filters(
            '2025-01-01', '2025-12-31'
        )
        
        self.assertEqual(start_display, '2025-01-01')
        self.assertEqual(end_display, '2025-12-31')
        self.assertIn('created_at__gte', filters)
        self.assertIn('created_at__lte', filters)
        
        # Test None values
        start_display, end_display, filters = build_date_range_filters(None, None)
        self.assertEqual(start_display, 'all time')
        self.assertEqual(end_display, 'all time')
        self.assertEqual(len(filters), 0)


if __name__ == '__main__':
    import unittest
    unittest.main()
