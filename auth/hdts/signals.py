"""
Django signals for the HDTS app to trigger user syncing (combined with roles).
Listens to post_save and post_delete signals and sends combined user+role data
to the message broker in a single sync task.

Also syncs HDTS Ticket Coordinator role and users to TTS (workflow_api) for
cross-system role synchronization.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging
from threading import Thread

logger = logging.getLogger(__name__)

# HDTS roles that should also sync to TTS/workflow_api
HDTS_ROLES_TO_SYNC_TO_TTS = ['Ticket Coordinator']


def _get_hdts_user_role(user):
    """
    Helper function to get the role name for an HDTS user.
    Returns the role name if the user has a role in HDTS system, None otherwise.
    """
    try:
        from system_roles.models import UserSystemRole
        user_role = UserSystemRole.objects.filter(
            user=user,
            system__slug='hdts'
        ).select_related('role').first()
        return user_role.role.name if user_role else None
    except Exception as e:
        logger.warning(f"Error getting HDTS role for user {user.id}: {str(e)}")
        return None


def _prepare_hdts_user_data(user, action='update'):
    """
    Helper function to prepare combined user + role data for HDTS sync.
    Combines user profile information with their HDTS role in a single object.
    """
    role = _get_hdts_user_role(user)
    
    return {
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "middle_name": getattr(user, 'middle_name', ''),
        "suffix": getattr(user, 'suffix', ''),
        "company_id": user.company_id,
        "department": user.department,
        "role": role,
        "status": user.status,
        "notified": getattr(user, 'notified', False),
        "profile_picture": user.profile_picture.url if user.profile_picture else None,
        "action": action,
    }


def _should_sync_to_tts(role_name):
    """
    Check if an HDTS role should also be synced to TTS.
    Returns True for roles like 'Ticket Coordinator' that need cross-system sync.
    """
    return role_name in HDTS_ROLES_TO_SYNC_TO_TTS


def _get_or_create_tts_role(hdts_role):
    """
    Get or create a corresponding TTS role for an HDTS role.
    Returns the TTS role if it exists or was created, None otherwise.
    """
    from roles.models import Role
    from systems.models import System
    
    try:
        tts_system = System.objects.get(slug='tts')
        # Use same name for the TTS role
        tts_role, created = Role.objects.get_or_create(
            system=tts_system,
            name=hdts_role.name,
            defaults={
                'description': f'Synced from HDTS: {hdts_role.description or ""}',
                'is_custom': False,
            }
        )
        if created:
            logger.info(f"Created TTS role '{tts_role.name}' synced from HDTS")
        return tts_role
    except System.DoesNotExist:
        logger.warning("TTS system not found, cannot sync role to TTS")
        return None
    except Exception as e:
        logger.error(f"Error getting/creating TTS role: {str(e)}")
        return None


def _prepare_tts_user_system_role_data(user, hdts_role, tts_role, action='update'):
    """
    Prepare UserSystemRole data for syncing HDTS user to TTS/workflow_api.
    Uses the TTS role information for the sync.
    """
    from system_roles.models import UserSystemRole
    
    # Get or infer the user_system_role ID - try to find if user has TTS role already
    try:
        tts_system = tts_role.system
        existing_usr = UserSystemRole.objects.filter(
            user=user,
            system=tts_system,
            role=tts_role
        ).first()
        user_system_role_id = existing_usr.id if existing_usr else None
        is_active = existing_usr.is_active if existing_usr else True
        assigned_at = existing_usr.assigned_at.isoformat() if existing_usr else None
        settings = existing_usr.settings if existing_usr else {}
    except Exception:
        user_system_role_id = None
        is_active = True
        assigned_at = None
        settings = {}
    
    return {
        "user_system_role_id": user_system_role_id,
        "user_id": user.id,
        "user_email": user.email,
        "user_full_name": user.get_full_name(),
        "system": "tts",
        "role_id": tts_role.id,
        "role_name": tts_role.name,
        "assigned_at": assigned_at,
        "is_active": is_active,
        "settings": settings,
        "action": action,
        "source_system": "hdts",  # Mark that this came from HDTS
    }


def _sync_hdts_role_to_tts(hdts_role, action='create'):
    """
    Sync an HDTS role to TTS/workflow_api if it's in the list of roles to sync.
    """
    if not _should_sync_to_tts(hdts_role.name):
        return
    
    from celery import current_app
    
    try:
        # Get or create the corresponding TTS role
        tts_role = _get_or_create_tts_role(hdts_role)
        if not tts_role:
            return
        
        # Prepare role data for workflow_api
        role_data = {
            "role_id": tts_role.id,
            "name": tts_role.name,
            "system": "tts",
            "description": tts_role.description,
            "is_custom": tts_role.is_custom,
            "created_at": tts_role.created_at.isoformat(),
            "action": action,
            "source_system": "hdts",  # Mark that this came from HDTS
        }
        
        # Send to workflow_api via TTS role sync queue
        try:
            current_app.send_task(
                'role.tasks.sync_role',
                args=[role_data],
                queue='tts.role.sync',
                routing_key='tts.role.sync',
                retry=False,
                time_limit=10,
            )
            logger.info(f"HDTS role '{hdts_role.name}' synced to TTS/workflow_api with action: {action}")
        except Exception as celery_error:
            logger.warning(f"Celery task send failed for HDTS->TTS role sync (non-blocking): {str(celery_error)}")
    except Exception as e:
        logger.error(f"Error syncing HDTS role to TTS: {str(e)}")


def _sync_hdts_user_to_tts(user, hdts_role, action='create'):
    """
    Sync an HDTS user with a specific role to TTS/workflow_api.
    This creates a corresponding UserSystemRole in TTS.
    """
    if not _should_sync_to_tts(hdts_role.name):
        return
    
    from celery import current_app
    from system_roles.models import UserSystemRole
    from systems.models import System
    
    try:
        # Get or create the corresponding TTS role
        tts_role = _get_or_create_tts_role(hdts_role)
        if not tts_role:
            return
        
        # Get TTS system
        try:
            tts_system = System.objects.get(slug='tts')
        except System.DoesNotExist:
            logger.warning("TTS system not found, cannot sync user to TTS")
            return
        
        # For create/update: ensure the UserSystemRole exists in TTS
        if action != 'delete':
            usr, created = UserSystemRole.objects.get_or_create(
                user=user,
                system=tts_system,
                role=tts_role,
                defaults={
                    'is_active': True,
                    'settings': {},
                }
            )
            if created:
                logger.info(f"Created TTS UserSystemRole for user {user.email} with role {tts_role.name}")
        
        # Prepare user_system_role data for workflow_api
        user_system_role_data = _prepare_tts_user_system_role_data(user, hdts_role, tts_role, action)
        
        # Send to workflow_api via TTS user_system_role sync queue
        try:
            current_app.send_task(
                'role.tasks.sync_user_system_role',
                args=[user_system_role_data],
                queue='tts.user_system_role.sync',
                routing_key='tts.user_system_role.sync',
                retry=False,
                time_limit=10,
            )
            logger.info(f"HDTS user {user.email} with role '{hdts_role.name}' synced to TTS/workflow_api with action: {action}")
        except Exception as celery_error:
            logger.warning(f"Celery task send failed for HDTS->TTS user sync (non-blocking): {str(celery_error)}")
    except Exception as e:
        logger.error(f"Error syncing HDTS user to TTS: {str(e)}")


def _prepare_hdts_employee_data(employee, action='update'):
    """
    Helper function to prepare employee data for HDTS sync.
    Sends employee data as-is with role set to 'employee'.
    """
    return {
        "employee_id": employee.id,
        "user_id": employee.user.id if employee.user else None,
        "email": employee.email,
        "username": employee.username,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "middle_name": employee.middle_name or '',
        "suffix": employee.suffix or '',
        "phone_number": employee.phone_number,
        "company_id": employee.company_id,
        "department": employee.department,
        "status": employee.status,
        "notified": employee.notified,
        "profile_picture": employee.profile_picture.url if employee.profile_picture else None,
        "role": "employee",
        "action": action,
    }


# ==================== HDTS Role Signals for TTS Sync ====================

@receiver(post_save, sender='roles.Role')
def hdts_role_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for when an HDTS Role is created or updated.
    If the role is 'Ticket Coordinator', also sync it to TTS.
    Runs in background thread to prevent blocking.
    """
    def send_sync_task():
        try:
            # Only process HDTS roles
            if instance.system.slug == 'hdts' and _should_sync_to_tts(instance.name):
                action = 'create' if created else 'update'
                logger.info(f"HDTS Role {instance.id} ({instance.name}) {action}d, syncing to TTS")
                _sync_hdts_role_to_tts(instance, action)
        except Exception as e:
            logger.error(f"Error in hdts_role_post_save signal: {str(e)}")
    
    # Send in background thread to prevent blocking the response
    thread = Thread(target=send_sync_task, daemon=True)
    thread.start()


@receiver(post_delete, sender='roles.Role')
def hdts_role_post_delete(sender, instance, **kwargs):
    """
    Signal handler for when an HDTS Role is deleted.
    If the role is 'Ticket Coordinator', also sync deletion to TTS.
    """
    def send_sync_task():
        try:
            # Only process HDTS roles
            if instance.system.slug == 'hdts' and _should_sync_to_tts(instance.name):
                logger.info(f"HDTS Role {instance.id} ({instance.name}) deleted, syncing to TTS")
                _sync_hdts_role_to_tts(instance, 'delete')
        except Exception as e:
            logger.error(f"Error in hdts_role_post_delete signal: {str(e)}")
    
    # Send in background thread to prevent blocking the response
    thread = Thread(target=send_sync_task, daemon=True)
    thread.start()


# ==================== HDTS User Signals ====================

@receiver(post_save, sender='users.User')
def user_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for when a User is created or updated.
    Checks if user belongs to HDTS system and syncs combined user+role information.
    Runs in background thread to prevent blocking.
    """
    def send_sync_task():
        try:
            # Check if this user belongs to HDTS system
            role = _get_hdts_user_role(instance)
            
            if role:
                action = 'create' if created else 'update'
                logger.info(f"User {instance.id} ({instance.email}) {action}d with role {role}, syncing to HDTS subscribers")
                
                from celery import current_app
                
                # Prepare combined user + role data
                user_data = _prepare_hdts_user_data(instance, action=action)
                
                # Send directly to HDTS handlers via Celery task with timeout
                try:
                    current_app.send_task(
                        'hdts.tasks.sync_hdts_user',
                        args=[user_data],
                        queue='hdts.user.sync',
                        routing_key='hdts.user.sync',
                        retry=False,
                        time_limit=10,
                    )
                except Exception as celery_error:
                    logger.warning(f"Celery task send failed (non-blocking): {str(celery_error)}")
        except Exception as e:
            logger.error(f"Error in user_post_save signal: {str(e)}")
    
    # Send in background thread to prevent blocking the response
    thread = Thread(target=send_sync_task, daemon=True)
    thread.start()


@receiver(post_delete, sender='users.User')
def user_post_delete(sender, instance, **kwargs):
    """
    Signal handler for when a User is deleted.
    Only processes users that belonged to the HDTS system.
    """
    def send_sync_task():
        try:
            # We can't query for the role after deletion, but we can still sync the delete action
            # The consumer will need to handle the delete based on email/user_id
            logger.info(f"User {instance.id} ({instance.email}) deleted, syncing to HDTS subscribers")
            
            from celery import current_app
            
            # Prepare user data for deletion (include what we have)
            user_data = {
                "user_id": instance.id,
                "email": instance.email,
                "username": instance.username,
                "first_name": instance.first_name,
                "last_name": instance.last_name,
                "middle_name": getattr(instance, 'middle_name', ''),
                "suffix": getattr(instance, 'suffix', ''),
                "company_id": instance.company_id,
                "department": instance.department,
                "status": instance.status,
                "action": 'delete',
            }
            
            # Send directly to HDTS handlers task
            current_app.send_task(
                'hdts.tasks.sync_hdts_user',
                args=[user_data],
                queue='hdts.user.sync',
                routing_key='hdts.user.sync',
            )
        except Exception as e:
            logger.error(f"Error in user_post_delete signal: {str(e)}")
    
    # Send in background thread to prevent blocking the response
    thread = Thread(target=send_sync_task, daemon=True)
    thread.start()


@receiver(post_save, sender='system_roles.UserSystemRole')
def user_system_role_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for when a UserSystemRole is created or updated.
    Only syncs if the role belongs to the HDTS system.
    Sends combined user + role data in a single sync operation.
    Runs in background thread to prevent blocking.
    
    Also syncs Ticket Coordinator role and users to TTS/workflow_api.
    """
    def send_sync_task():
        try:
            # Check if this user_system_role is for HDTS system
            if instance.role.system.slug == 'hdts':
                action = 'create' if created else 'update'
                logger.info(f"UserSystemRole {instance.id} (user={instance.user.email}, role={instance.role.name}) {action}d, syncing combined user+role to HDTS subscribers")
                
                from celery import current_app
                
                # Prepare combined user + role data with the new role
                user_data = _prepare_hdts_user_data(instance.user, action=action)
                # Override with the current role from the signal instance
                user_data['role'] = instance.role.name
                
                # Send directly to HDTS handlers task with timeout
                try:
                    current_app.send_task(
                        'hdts.tasks.sync_hdts_user',
                        args=[user_data],
                        queue='hdts.user.sync',
                        routing_key='hdts.user.sync',
                        retry=False,
                        time_limit=10,
                    )
                except Exception as celery_error:
                    logger.warning(f"Celery task send failed (non-blocking): {str(celery_error)}")
                
                # Also sync to TTS if role is in the list of roles to sync
                if _should_sync_to_tts(instance.role.name):
                    logger.info(f"HDTS role '{instance.role.name}' should sync to TTS, syncing user {instance.user.email}")
                    _sync_hdts_user_to_tts(instance.user, instance.role, action)
        except Exception as e:
            logger.error(f"Error in user_system_role_post_save signal: {str(e)}")
    
    # Send in background thread to prevent blocking the response
    thread = Thread(target=send_sync_task, daemon=True)
    thread.start()


@receiver(post_delete, sender='system_roles.UserSystemRole')
def user_system_role_post_delete(sender, instance, **kwargs):
    """
    Signal handler for when a UserSystemRole is deleted.
    Sends the combined user+role data before deletion for sync purposes.
    Also syncs Ticket Coordinator deletion to TTS/workflow_api.
    """
    def send_sync_task():
        try:
            # Check if this user_system_role belonged to HDTS system
            if instance.role.system.slug == 'hdts':
                logger.info(f"UserSystemRole {instance.id} (user={instance.user.email}, role={instance.role.name}) deleted, syncing to HDTS subscribers")
                
                from celery import current_app
                
                # Prepare the combined user data before it's deleted
                user_data = _prepare_hdts_user_data(instance.user, action='delete')
                # Override with the deleted role
                user_data['role'] = instance.role.name
                
                # Send directly to HDTS handlers task
                current_app.send_task(
                    'hdts.tasks.sync_hdts_user',
                    args=[user_data],
                    queue='hdts.user.sync',
                    routing_key='hdts.user.sync',
                )
                
                # Also sync to TTS if role is in the list of roles to sync
                if _should_sync_to_tts(instance.role.name):
                    logger.info(f"HDTS role '{instance.role.name}' deletion should sync to TTS, syncing user {instance.user.email}")
                    _sync_hdts_user_to_tts(instance.user, instance.role, 'delete')
        except Exception as e:
            logger.error(f"Error in user_system_role_post_delete signal: {str(e)}")
    
    # Send in background thread to prevent blocking the response
    thread = Thread(target=send_sync_task, daemon=True)
    thread.start()


@receiver(post_save, sender='hdts.Employees')
def employee_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for when an Employee is created or updated.
    Syncs employee data with role set to 'employee' to separate queue.
    Runs in background thread to prevent blocking.
    """
    def send_sync_task():
        try:
            action = 'create' if created else 'update'
            logger.info(f"Employee {instance.id} ({instance.email}) {action}d, syncing to external employee subscribers")
            
            from celery import current_app
            
            # Prepare employee data with role set to 'employee'
            employee_data = _prepare_hdts_employee_data(instance, action=action)
            
            # Send to SEPARATE queue for employees (hdts.employee.sync)
            # Task will be processed by backend Celery worker
            try:
                current_app.send_task(
                    'core.tasks.process_hdts_employee_sync',
                    args=[employee_data],
                    queue='hdts.employee.sync',
                    routing_key='hdts.employee.sync',
                    retry=False,
                    time_limit=10,
                )
            except Exception as celery_error:
                logger.warning(f"Celery task send failed (non-blocking): {str(celery_error)}")
        except Exception as e:
            logger.error(f"Error in employee_post_save signal: {str(e)}")
    
    # Send in background thread to prevent blocking the response
    thread = Thread(target=send_sync_task, daemon=True)
    thread.start()


@receiver(post_delete, sender='hdts.Employees')
def employee_post_delete(sender, instance, **kwargs):
    """
    Signal handler for when an Employee is deleted.
    Syncs employee deletion to separate queue for external employee subscribers.
    """
    def send_sync_task():
        try:
            logger.info(f"Employee {instance.id} ({instance.email}) deleted, syncing to external employee subscribers")
            
            from celery import current_app
            
            # Prepare employee data for deletion
            employee_data = _prepare_hdts_employee_data(instance, action='delete')
            
            # Send to SEPARATE queue for employees (hdts.employee.sync)
            # Task will be processed by backend Celery worker
            current_app.send_task(
                'core.tasks.process_hdts_employee_sync',
                args=[employee_data],
                queue='hdts.employee.sync',
                routing_key='hdts.employee.sync',
            )
        except Exception as e:
            logger.error(f"Error in employee_post_delete signal: {str(e)}")
    
    # Send in background thread to prevent blocking the response
    thread = Thread(target=send_sync_task, daemon=True)
    thread.start()
