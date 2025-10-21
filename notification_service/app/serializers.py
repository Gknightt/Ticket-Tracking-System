from rest_framework import serializers
from .models import InAppNotification

class InAppNotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for InAppNotification model
    """
    class Meta:
        model = InAppNotification
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'read_at']

class InAppNotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new InAppNotification
    """
    class Meta:
        model = InAppNotification
        fields = ['user_id', 'subject', 'message']
        
class InAppNotificationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an InAppNotification (primarily marking as read)
    """
    class Meta:
        model = InAppNotification
        fields = ['is_read']

class MarkNotificationAsReadSerializer(serializers.Serializer):
    """
    Serializer for marking a notification as read
    """
    notification_id = serializers.UUIDField(
        required=True,
        help_text="UUID of the notification to mark as read"
    )