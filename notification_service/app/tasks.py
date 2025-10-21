from celery import shared_task
from .models import InAppNotification
import logging

logger = logging.getLogger(__name__)

@shared_task(name="notifications.create_inapp_notification")
def create_inapp_notification(user_id, subject, message):
    """
    Create a new in-app notification for a user
    
    Args:
        user_id (int): The ID of the user to receive the notification
        subject (str): The notification subject
        message (str): The notification message content
    
    Returns:
        dict: Status of the operation
    """
    try:
        notification = InAppNotification.objects.create(
            user_id=user_id,
            subject=subject,
            message=message
        )
        
        logger.info(f"Created in-app notification {notification.id} for user {user_id}")
        
        return {
            "status": "success",
            "notification_id": str(notification.id),
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Failed to create in-app notification: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@shared_task(name="notifications.mark_notification_read")
def mark_notification_read(notification_id):
    """
    Mark an in-app notification as read
    
    Args:
        notification_id (str): The UUID of the notification to mark as read
        
    Returns:
        dict: Status of the operation
    """
    try:
        notification = InAppNotification.objects.get(id=notification_id)
        notification.mark_as_read()
        
        logger.info(f"Marked notification {notification_id} as read")
        
        return {
            "status": "success",
            "notification_id": notification_id,
            "user_id": notification.user_id
        }
    except InAppNotification.DoesNotExist:
        logger.warning(f"Notification {notification_id} not found")
        return {
            "status": "error",
            "error": f"Notification {notification_id} not found"
        }
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@shared_task(name="notifications.bulk_create_notifications")
def bulk_create_notifications(notifications_data):
    """
    Create multiple in-app notifications at once
    
    Args:
        notifications_data (list): List of dictionaries with user_id, subject, and message
        
    Returns:
        dict: Status of the operation with count of created notifications
    """
    created_count = 0
    failed_count = 0
    
    try:
        notifications = []
        for data in notifications_data:
            try:
                notifications.append(InAppNotification(
                    user_id=data['user_id'],
                    subject=data['subject'],
                    message=data['message']
                ))
                created_count += 1
            except Exception as e:
                logger.error(f"Failed to prepare notification: {str(e)}")
                failed_count += 1
                
        # Bulk create all prepared notifications
        if notifications:
            InAppNotification.objects.bulk_create(notifications)
            
        return {
            "status": "success",
            "created_count": created_count,
            "failed_count": failed_count
        }
    except Exception as e:
        logger.error(f"Failed in bulk notification creation: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "created_count": created_count,
            "failed_count": failed_count
        }