"""
Utility functions for user assignment and round-robin logic.
These functions are used across tasks, steps, and transitions.
"""

from django.utils import timezone
from tickets.models import RoundRobin
from task.models import TaskItem
from task.utils.target_resolution import calculate_target_resolution
from role.models import Roles, RoleUsers
from task.tasks import send_assignment_notification as notify_task
import logging

logger = logging.getLogger(__name__)


def fetch_users_for_role(role_name):
    """
    Fetch users for a role from the RoleUsers model.
    
    Args:
        role_name: Name of the role
    
    Returns:
        List of user IDs: [3, 6, 7, ...]
    """
    try:
        role = Roles.objects.get(name=role_name)
        user_ids = list(RoleUsers.objects.filter(
            role_id=role,
            is_active=True
        ).values_list('user_id', flat=True))
        logger.info(f"✅ Found {len(user_ids)} users for role '{role_name}'")
        return user_ids
    except Roles.DoesNotExist:
        logger.warning(f"❌ Role '{role_name}' not found")
        return []
    except Exception as e:
        logger.error(f"❌ Error fetching users: {e}")
        return []


def apply_round_robin_assignment(task, user_ids, role_name):
    """
    Apply round-robin logic to assign users to tasks.
    
    Args:
        task: Task instance
        user_ids: List of user IDs to assign
        role_name: Role name for tracking
    
    Returns:
        List of created TaskItem instances
    """
    if not user_ids:
        logger.warning(f"No users for role '{role_name}'")
        return []

    round_robin_state, _ = RoundRobin.objects.get_or_create(
        role_name=role_name,
        defaults={"current_index": 0}
    )

    current_index = round_robin_state.current_index
    user_index = current_index % len(user_ids)
    user_id = user_ids[user_index]

    # Calculate target resolution
    target_resolution = None
    try:
        if task.ticket_id and task.current_step and task.workflow_id:
            target_resolution = calculate_target_resolution(
                ticket=task.ticket_id,
                step=task.current_step,
                workflow=task.workflow_id
            )
    except Exception as e:
        logger.error(f"Failed to calculate target resolution: {e}")

    # Get RoleUsers record for this user and role
    try:
        role_users = RoleUsers.objects.select_related('role_id').get(
            user_id=user_id,
            role_id__name=role_name,
            is_active=True
        )
    except RoleUsers.DoesNotExist:
        logger.error(f"❌ RoleUsers record not found for user {user_id} and role '{role_name}'")
        return []

    # Create TaskItem for the assigned user
    task_item, created = TaskItem.objects.get_or_create(
        task=task,
        role_user=role_users,
        defaults={
            'status': 'assigned',
            'assigned_on': timezone.now(),
            'target_resolution': target_resolution
        }
    )
    
    if created:
        logger.info(f"👤 Created TaskItem: User {user_id} assigned to Task {task.task_id}")
        # Send assignment notification via Celery
        notify_task.delay(
            user_id=user_id,
            task_id=str(task.task_id),
            task_title=str(task.ticket_id.subject) if hasattr(task, 'ticket_id') else f"Task {task.task_id}",
            role_name=role_name
        )
    else:
        logger.info(f"⚠️ TaskItem already exists: User {user_id} for Task {task.task_id}")

    # Update round-robin state for next assignment
    round_robin_state.current_index = (current_index + 1) % len(user_ids)
    round_robin_state.save()
    
    logger.info(f"👤 Assigned user {user_id} from role '{role_name}' (round-robin index: {user_index})")

    return [task_item]


def assign_users_for_step(task, step, role_name):
    """
    Fetch users for a role and apply round-robin assignment.
    
    Args:
        task: Task instance
        step: Steps instance
        role_name: Role name
    
    Returns:
        List of TaskItem instances
    """
    user_ids = fetch_users_for_role(role_name)
    if not user_ids:
        logger.warning(f"No users for role '{role_name}'")
        return []
    return apply_round_robin_assignment(task, user_ids, role_name)
