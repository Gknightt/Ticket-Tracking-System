# Test Suite Documentation

## Overview

This document describes the comprehensive test suites for the Ticket Tracking System's workflow management functionality.

## Test Structure

All test files are located in `workflow_api/tests/` and use Django's `TestCase` class with the Django REST Framework's `APIClient` for API testing.

### Test Files

1. **test_roles_management.py** - Role Management Tests
2. **test_workflow_creation.py** - Workflow Creation Tests
3. **test_workflow_editing.py** - Workflow Editing Tests
4. **test_workflow_graph.py** - Workflow Graph Management Tests
5. **test_steps_transitions.py** - Steps and Transitions Tests
6. **test_ticket_generation.py** - Ticket Generation Tests
7. **test_task_assignment.py** - Task Assignment Tests
8. **test_api_endpoints.py** - Comprehensive API Endpoint Tests

## Running Tests

### Run All Tests

```bash
cd workflow_api
python manage.py test tests --verbosity=2
```

### Run Specific Test Suite

```bash
# Roles Management
python manage.py test tests.test_roles_management --verbosity=2

# Workflow Creation
python manage.py test tests.test_workflow_creation --verbosity=2

# Workflow Editing
python manage.py test tests.test_workflow_editing --verbosity=2

# Workflow Graph
python manage.py test tests.test_workflow_graph --verbosity=2

# Steps & Transitions
python manage.py test tests.test_steps_transitions --verbosity=2

# Ticket Generation
python manage.py test tests.test_ticket_generation --verbosity=2

# Task Assignment
python manage.py test tests.test_task_assignment --verbosity=2

# API Endpoints
python manage.py test tests.test_api_endpoints --verbosity=2
```

### Run Specific Test Case

```bash
python manage.py test tests.test_roles_management.RolesManagementTestCase.test_create_role --verbosity=2
```

## Test Coverage

### 1. Roles Management Tests (test_roles_management.py)

**Test Cases:**
- `test_create_role` - Test creating a new role
- `test_list_roles` - Test listing all roles
- `test_retrieve_role` - Test retrieving a specific role
- `test_update_role` - Test updating a role
- `test_delete_role` - Test deleting a role
- `test_role_unique_name` - Test that role names must be unique
- `test_role_user_assignment` - Test assigning users to roles
- `test_role_user_unique_constraint` - Test unique constraint on role-user assignment

**Coverage:**
- ✅ Role CRUD operations
- ✅ Unique name validation
- ✅ Role-user relationship
- ✅ Permission assignments

### 2. Workflow Creation Tests (test_workflow_creation.py)

**Test Cases:**
- `test_create_simple_workflow` - Test creating a simple workflow
- `test_workflow_unique_name` - Test that workflow names must be unique
- `test_workflow_category_validation` - Test workflow category validation
- `test_workflow_sla_ordering` - Test SLA ordering (urgent < high < medium < low)
- `test_workflow_invalid_sla_ordering` - Test invalid SLA ordering rejection
- `test_workflow_status_choices` - Test workflow status field
- `test_workflow_end_logic_choices` - Test workflow end_logic field
- `test_workflow_unique_category_subcategory_per_user` - Test unique constraint
- `test_workflow_different_users_same_category` - Test different users can use same category
- `test_category_hierarchy` - Test category parent-child relationships
- `test_workflow_creation_with_timestamps` - Test automatic timestamp creation

**Coverage:**
- ✅ Workflow creation with all fields
- ✅ Category and subcategory validation
- ✅ SLA validation and ordering
- ✅ Status and end_logic choices
- ✅ Unique constraints
- ✅ Duplicate handling

### 3. Workflow Editing Tests (test_workflow_editing.py)

**Test Cases:**
- `test_update_workflow_description` - Test updating description
- `test_update_workflow_status` - Test updating status
- `test_update_workflow_slas` - Test updating SLA values
- `test_update_workflow_department` - Test updating department
- `test_update_workflow_is_published` - Test updating is_published flag
- `test_update_workflow_end_logic` - Test updating end_logic
- `test_update_workflow_invalid_sla` - Test invalid SLA update rejection
- `test_update_workflow_name_unique` - Test name uniqueness on update
- `test_update_workflow_timestamps` - Test automatic timestamp updates
- `test_update_workflow_category` - Test updating category
- `test_partial_sla_update` - Test updating only some SLA values

**Coverage:**
- ✅ Workflow metadata updates
- ✅ SLA updates
- ✅ Status transitions
- ✅ Validation on updates
- ✅ Timestamp tracking

### 4. Workflow Graph Tests (test_workflow_graph.py)

**Test Cases:**
- `test_add_step_to_workflow` - Test adding a step
- `test_remove_step_from_workflow` - Test removing a step
- `test_step_ordering` - Test step ordering
- `test_create_transition_between_steps` - Test creating transitions
- `test_remove_transition` - Test removing transitions
- `test_transition_same_workflow_constraint` - Test workflow constraint
- `test_transition_no_self_loop` - Test self-loop prevention
- `test_step_start_and_end_flags` - Test start/end flags
- `test_step_design_coordinates` - Test design coordinates
- `test_transition_design_handles` - Test transition handles
- `test_multiple_transitions_from_step` - Test multiple outgoing transitions

**Coverage:**
- ✅ Adding/removing steps
- ✅ Creating/removing transitions
- ✅ Graph validation rules
- ✅ Design coordinate storage
- ✅ Step relationships

### 5. Steps & Transitions Tests (test_steps_transitions.py)

**Test Cases:**
- `test_step_role_assignment` - Test assigning roles to steps
- `test_step_escalation_role` - Test escalation role assignment
- `test_step_weight_values` - Test step weight values
- `test_step_weight_default` - Test default weight
- `test_step_order_priority` - Test step ordering for priority
- `test_step_is_initialized_flag` - Test is_initialized flag
- `test_step_instructions` - Test step instructions
- `test_transition_naming` - Test transition names
- `test_step_timestamps` - Test step timestamps
- `test_transition_timestamps` - Test transition timestamps
- `test_step_multiple_weights` - Test different weights
- `test_transition_outgoing_incoming_relationships` - Test relationships

**Coverage:**
- ✅ Step role assignment
- ✅ Weight management
- ✅ Priority ordering
- ✅ Escalation handling
- ✅ Transition relationships

### 6. Ticket Generation Tests (test_ticket_generation.py)

**Test Cases:**
- `test_create_ticket` - Test ticket creation
- `test_ticket_number_generation` - Test unique ticket numbers
- `test_ticket_with_priority` - Test priority levels
- `test_ticket_with_category` - Test category information
- `test_ticket_task_allocation_flag` - Test allocation flag
- `test_ticket_with_employee_info` - Test employee information
- `test_ticket_with_description` - Test descriptions
- `test_ticket_with_attachments` - Test attachment metadata
- `test_ticket_with_dynamic_data` - Test dynamic fields
- `test_ticket_status_values` - Test status values
- `test_ticket_department_routing` - Test department routing

**Coverage:**
- ✅ Ticket creation
- ✅ Priority handling
- ✅ Category routing
- ✅ Attachment support
- ✅ Dynamic fields
- ✅ Status management

### 7. Task Assignment Tests (test_task_assignment.py)

**Test Cases:**
- `test_create_task` - Test task creation
- `test_assign_user_to_task` - Test user assignment
- `test_multiple_users_assignment` - Test multiple users
- `test_task_status_values` - Test task statuses
- `test_task_item_status` - Test task item status
- `test_task_workflow_relationship` - Test workflow relationship
- `test_task_current_step_tracking` - Test step tracking
- `test_task_ticket_relationship` - Test ticket relationship
- `test_round_robin_assignment_setup` - Test round-robin setup
- `test_task_item_unique_assignment` - Test unique assignment
- `test_inactive_user_filtering` - Test inactive user filtering

**Coverage:**
- ✅ Task creation and assignment
- ✅ Multiple user assignments
- ✅ Status tracking
- ✅ Round-robin preparation
- ✅ Active user filtering

### 8. API Endpoints Tests (test_api_endpoints.py)

**Test Cases:**
- `test_workflow_list_endpoint` - Test workflow listing
- `test_workflow_detail_endpoint` - Test workflow details
- `test_workflow_create_data_structure` - Test creation structure
- `test_step_list_for_workflow` - Test step listing
- `test_transition_list_for_workflow` - Test transition listing
- `test_role_list_endpoint` - Test role listing
- `test_category_list_endpoint` - Test category listing
- `test_workflow_graph_structure` - Test graph structure
- `test_workflow_update_details_structure` - Test update structure
- `test_step_create_structure` - Test step creation
- `test_step_update_structure` - Test step update
- `test_transition_create_structure` - Test transition creation
- `test_ticket_create_structure` - Test ticket creation
- `test_task_create_structure` - Test task creation
- `test_workflow_sla_retrieval` - Test SLA retrieval
- `test_workflow_status_transition` - Test status transitions
- `test_step_weight_retrieval` - Test weight retrieval
- `test_workflow_version_tracking` - Test versioning

**Coverage:**
- ✅ All major endpoints
- ✅ Data structures
- ✅ CRUD operations
- ✅ Relationships
- ✅ Versioning

## CI/CD Integration

### GitHub Actions Workflow

The tests are automatically run on:
- Push to `main`, `QA`, `develop` branches
- Pull requests to these branches

### Test Execution

Tests are executed in the following jobs:
1. **auth-service-tests** - Authentication service tests
2. **workflow-api-tests** - All workflow management tests (8 suites)
3. **ticket-service-tests** - Ticket service tests
4. **messaging-service-tests** - Messaging service tests
5. **notification-service-tests** - Notification service tests
6. **frontend-build** - Frontend build and lint

### Workflow Features

- **Parallel Execution** - Most test jobs run in parallel for speed
- **Sequential Suite Execution** - Within workflow-api, tests run sequentially for clarity
- **Fail Fast** - Tests fail the build on errors (no `|| true`)
- **Artifact Upload** - Test results saved for 7 days
- **Test Summary** - Final job aggregates all results
- **Failure Detection** - Summary job exits with error if any test fails

## Best Practices

### Writing Tests

1. **Use descriptive test names** - Test names should clearly state what is being tested
2. **One assertion per test** - Keep tests focused on a single behavior
3. **Use setUp for common data** - Create shared test data in setUp method
4. **Clean up after tests** - Django's TestCase handles this automatically
5. **Test both success and failure cases** - Include negative tests

### Test Data

- Use meaningful names for test data (e.g., "Test Admin", "API Test Workflow")
- Create minimal data needed for each test
- Use factories or fixtures for complex data setup
- Avoid hardcoded IDs when possible

### Assertions

```python
# Good
self.assertEqual(workflow.name, "Expected Name")
self.assertIsNotNone(workflow.created_at)
self.assertTrue(workflow.is_published)

# Avoid
assert workflow.name == "Expected Name"  # Use Django's assertions
```

## Extending Tests

### Adding New Test Cases

1. Create test method in appropriate test file
2. Name method with `test_` prefix
3. Write descriptive docstring
4. Follow existing patterns
5. Run locally before committing

### Adding New Test Suite

1. Create new test file in `workflow_api/tests/`
2. Import necessary models and test classes
3. Create TestCase class with descriptive name
4. Add setUp method for common data
5. Write test methods
6. Update GitHub Actions workflow to include new suite
7. Update this documentation

## Troubleshooting

### Common Issues

**Issue: ImportError for Django**
```bash
# Solution: Install dependencies
pip install -r workflow_api/requirements.txt
```

**Issue: Database errors**
```bash
# Solution: Run migrations
python manage.py migrate
```

**Issue: Test data conflicts**
```bash
# Solution: Django's TestCase uses transactions and rolls back after each test
# No manual cleanup needed
```

## Maintenance

### Regular Updates

- Review and update tests when models change
- Add tests for new features
- Remove tests for deprecated functionality
- Keep documentation in sync with code

### Test Quality Metrics

- Aim for >80% code coverage
- All critical paths should have tests
- Integration points should be well-tested
- API contracts should be verified

## Resources

- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Django REST Framework Testing](https://www.django-rest-framework.org/api-guide/testing/)
- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)
