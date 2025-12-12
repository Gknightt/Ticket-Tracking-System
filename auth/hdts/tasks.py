"""
Celery tasks for syncing simplified HDTS user information to backend services.
Sends combined user + role data in a single sync operation via the message broker.
"""

from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(name='hdts.tasks.sync_hdts_user')
def sync_hdts_user(user_data):
    """
    Sync combined user + role information to HDTS subscribers via the message broker.
    Handles create, update, and delete actions for total sync.
    
    The user_data includes both user profile and their role in a single object,
    eliminating the need for separate role syncs.
    
    Args:
        user_data (dict): The combined user + role data to sync including action type
    
    Returns:
        dict: Status of the sync operation
    """
    from celery import current_app
    
    try:
        action = user_data.get('action', 'update')
        user_id = user_data.get('user_id')
        
        # For delete action, we have the full data in user_data
        # For create/update, verify user exists (except for deletes)
        if action != 'delete':
            from users.models import User
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.error(f"User {user_id} not found for {action} action")
                return {"status": "error", "error": "User not found"}
        
        logger.info(f"Syncing HDTS user {user_id} ({user_data.get('email')}) with role '{user_data.get('role')}' to subscribers with action: {action}")
        logger.debug(f"User data: {user_data}")
        
        # Send message to HDTS subscribers via Celery task
        # This will be picked up by any service listening to hdts.user.sync queue
        current_app.send_task(
            'hdts.consumer.process_hdts_user_sync',
            args=[user_data],
            queue='hdts.user.sync',
            routing_key='hdts.user.sync',
        )
        
        logger.info(f"HDTS user {user_id} sync message sent to subscribers with action: {action}")
        return {
            "status": "success",
            "user_id": user_id,
            "action": action,
        }
    
    except Exception as e:
        logger.error(f"Error syncing HDTS user: {str(e)}")
        return {"status": "error", "error": str(e)}


@shared_task(name='hdts.tasks.sync_hdts_employee')
def sync_hdts_employee(employee_data):
    """
    Sync employee information to backend external employees table via message broker.
    Handles create, update, and delete actions for employee synchronization.
    
    Args:
        employee_data (dict): The employee data to sync including action type
    
    Returns:
        dict: Status of the sync operation
    """
    from celery import current_app
    
    try:
        action = employee_data.get('action', 'update')
        employee_id = employee_data.get('employee_id')
        
        # For delete action, we have the full data in employee_data
        # For create/update, verify employee exists (except for deletes)
        if action != 'delete':
            from hdts.models import Employees
            try:
                employee = Employees.objects.get(id=employee_id)
            except Employees.DoesNotExist:
                logger.error(f"Employee {employee_id} not found for {action} action")
                return {"status": "error", "error": "Employee not found"}
        
        logger.info(f"Syncing HDTS employee {employee_id} ({employee_data.get('email')}) to backend external employees with action: {action}")
        logger.debug(f"Employee data: {employee_data}")
        
        # Send message to backend via separate employee sync queue
        # This will be picked up by backend service listening to hdts.employee.sync queue
        current_app.send_task(
            'core.tasks.process_hdts_employee_sync',
            args=[employee_data],
            queue='hdts.employee.sync',
            routing_key='hdts.employee.sync',
        )
        
        logger.info(f"HDTS employee {employee_id} sync message sent to backend with action: {action}")
        return {
            "status": "success",
            "employee_id": employee_id,
            "action": action,
        }
    
    except Exception as e:
        logger.error(f"Error syncing HDTS employee: {str(e)}")
        return {"status": "error", "error": str(e)}


# ==================== HDTS to TTS Sync Tasks ====================

# HDTS roles that should also sync to TTS/workflow_api
HDTS_ROLES_TO_SYNC_TO_TTS = ['Ticket Coordinator']


@shared_task(name='hdts.tasks.sync_hdts_role_to_tts')
def sync_hdts_role_to_tts(role_data):
    """
    Sync an HDTS role (like Ticket Coordinator) to TTS/workflow_api.
    Creates a corresponding role in TTS and syncs it to workflow_api.
    
    Args:
        role_data (dict): The role data to sync
            Expected format:
            {
                "role_id": int,
                "name": str,
                "description": str,
                "action": str ("create", "update", or "delete")
            }
    
    Returns:
        dict: Status of the sync operation
    """
    from celery import current_app
    from roles.models import Role
    from systems.models import System
    
    try:
        action = role_data.get('action', 'create')
        role_name = role_data.get('name')
        
        # Only sync roles that are in the list
        if role_name not in HDTS_ROLES_TO_SYNC_TO_TTS:
            logger.info(f"HDTS role '{role_name}' not in sync list, skipping TTS sync")
            return {"status": "skipped", "reason": "not_in_sync_list"}
        
        logger.info(f"Syncing HDTS role '{role_name}' to TTS with action: {action}")
        
        # Get TTS system
        try:
            tts_system = System.objects.get(slug='tts')
        except System.DoesNotExist:
            logger.warning("TTS system not found, cannot sync role to TTS")
            return {"status": "error", "error": "TTS system not found"}
        
        if action == 'delete':
            # Delete the corresponding TTS role
            try:
                tts_role = Role.objects.get(system=tts_system, name=role_name)
                tts_role_id = tts_role.id
                tts_role.delete()
                logger.info(f"Deleted TTS role '{role_name}'")
            except Role.DoesNotExist:
                logger.warning(f"TTS role '{role_name}' not found for deletion")
                return {"status": "success", "action": "delete", "note": "not_found"}
        else:
            # Create or update the TTS role
            tts_role, created = Role.objects.update_or_create(
                system=tts_system,
                name=role_name,
                defaults={
                    'description': f"Synced from HDTS: {role_data.get('description', '')}",
                    'is_custom': False,
                }
            )
            tts_role_id = tts_role.id
            action_str = "created" if created else "updated"
            logger.info(f"TTS role '{role_name}' {action_str}")
        
        # Prepare role data for workflow_api
        tts_role_data = {
            "role_id": tts_role_id if action != 'delete' else role_data.get('role_id'),
            "name": role_name,
            "system": "tts",
            "description": role_data.get('description', ''),
            "is_custom": False,
            "created_at": role_data.get('created_at'),
            "action": action,
            "source_system": "hdts",
        }
        
        # Send to workflow_api
        try:
            current_app.send_task(
                'role.tasks.sync_role',
                args=[tts_role_data],
                queue='tts.role.sync',
                routing_key='tts.role.sync',
                retry=False,
                time_limit=10,
            )
            logger.info(f"HDTS role '{role_name}' synced to workflow_api via TTS queue")
        except Exception as celery_error:
            logger.warning(f"Celery task send failed for HDTS->TTS role sync: {str(celery_error)}")
        
        return {
            "status": "success",
            "role_name": role_name,
            "action": action,
        }
    
    except Exception as e:
        logger.error(f"Error syncing HDTS role to TTS: {str(e)}")
        return {"status": "error", "error": str(e)}


@shared_task(name='hdts.tasks.sync_hdts_user_to_tts')
def sync_hdts_user_to_tts(user_role_data):
    """
    Sync an HDTS user with Ticket Coordinator role to TTS/workflow_api.
    Creates a corresponding UserSystemRole in TTS and syncs it to workflow_api.
    
    Args:
        user_role_data (dict): The user and role data to sync
            Expected format:
            {
                "user_id": int,
                "user_email": str,
                "user_full_name": str,
                "role_name": str,
                "action": str ("create", "update", or "delete")
            }
    
    Returns:
        dict: Status of the sync operation
    """
    from celery import current_app
    from users.models import User
    from roles.models import Role
    from systems.models import System
    from system_roles.models import UserSystemRole
    
    try:
        action = user_role_data.get('action', 'create')
        user_id = user_role_data.get('user_id')
        role_name = user_role_data.get('role_name')
        
        # Only sync roles that are in the list
        if role_name not in HDTS_ROLES_TO_SYNC_TO_TTS:
            logger.info(f"HDTS role '{role_name}' not in sync list, skipping TTS user sync")
            return {"status": "skipped", "reason": "not_in_sync_list"}
        
        logger.info(f"Syncing HDTS user {user_id} with role '{role_name}' to TTS with action: {action}")
        
        # Get TTS system and role
        try:
            tts_system = System.objects.get(slug='tts')
        except System.DoesNotExist:
            logger.warning("TTS system not found, cannot sync user to TTS")
            return {"status": "error", "error": "TTS system not found"}
        
        # Get or create TTS role
        tts_role, _ = Role.objects.get_or_create(
            system=tts_system,
            name=role_name,
            defaults={
                'description': f"Synced from HDTS",
                'is_custom': False,
            }
        )
        
        # Get the user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            if action != 'delete':
                logger.error(f"User {user_id} not found for {action} action")
                return {"status": "error", "error": "User not found"}
            user = None
        
        user_system_role_id = None
        
        if action == 'delete':
            # Delete the TTS UserSystemRole
            if user:
                deleted_count, _ = UserSystemRole.objects.filter(
                    user=user,
                    system=tts_system,
                    role=tts_role
                ).delete()
                if deleted_count > 0:
                    logger.info(f"Deleted TTS UserSystemRole for user {user_id}")
                else:
                    logger.warning(f"TTS UserSystemRole for user {user_id} not found for deletion")
        else:
            # Create or update the TTS UserSystemRole
            usr, created = UserSystemRole.objects.update_or_create(
                user=user,
                system=tts_system,
                role=tts_role,
                defaults={
                    'is_active': True,
                    'settings': {},
                }
            )
            user_system_role_id = usr.id
            action_str = "created" if created else "updated"
            logger.info(f"TTS UserSystemRole for user {user_id} {action_str}")
        
        # Prepare user_system_role data for workflow_api
        tts_user_data = {
            "user_system_role_id": user_system_role_id,
            "user_id": user_id,
            "user_email": user_role_data.get('user_email'),
            "user_full_name": user_role_data.get('user_full_name'),
            "system": "tts",
            "role_id": tts_role.id,
            "role_name": tts_role.name,
            "assigned_at": user_role_data.get('assigned_at'),
            "is_active": True,
            "settings": {},
            "action": action,
            "source_system": "hdts",
        }
        
        # Send to workflow_api
        try:
            current_app.send_task(
                'role.tasks.sync_user_system_role',
                args=[tts_user_data],
                queue='tts.user_system_role.sync',
                routing_key='tts.user_system_role.sync',
                retry=False,
                time_limit=10,
            )
            logger.info(f"HDTS user {user_id} with role '{role_name}' synced to workflow_api via TTS queue")
        except Exception as celery_error:
            logger.warning(f"Celery task send failed for HDTS->TTS user sync: {str(celery_error)}")
        
        return {
            "status": "success",
            "user_id": user_id,
            "role_name": role_name,
            "action": action,
        }
    
    except Exception as e:
        logger.error(f"Error syncing HDTS user to TTS: {str(e)}")
        return {"status": "error", "error": str(e)}

