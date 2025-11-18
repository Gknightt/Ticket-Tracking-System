from django.contrib import admin
from .models import Task, TaskItem

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['task_id', 'ticket_id', 'workflow_id', 'current_step', 'status', 'created_at']
    list_filter = ['status', 'workflow_id', 'created_at']
    search_fields = ['task_id', 'ticket_id__subject']
    readonly_fields = ['task_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('task_id', 'ticket_id', 'workflow_id', 'current_step', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'fetched_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TaskItem)
class TaskItemAdmin(admin.ModelAdmin):
    list_display = ['task_item_id', 'task', 'get_user_id', 'get_user_full_name', 'get_role', 'status', 'assigned_on']
    list_filter = ['status', 'role_user__role_id', 'assigned_on']
    search_fields = ['task__task_id', 'role_user__user_id', 'role_user__user_full_name']
    readonly_fields = ['task_item_id', 'assigned_on']
    
    fieldsets = (
        ('Assignment Info', {
            'fields': ('task_item_id', 'task', 'role_user')
        }),
        ('Status', {
            'fields': ('status', 'assigned_on', 'status_updated_on', 'acted_on')
        }),
    )
    
    def get_user_id(self, obj):
        return obj.role_user.user_id if obj.role_user else None
    get_user_id.short_description = 'User ID'
    
    def get_user_full_name(self, obj):
        return obj.role_user.user_full_name if obj.role_user else None
    get_user_full_name.short_description = 'User Full Name'
    
    def get_role(self, obj):
        return obj.role_user.role_id.name if obj.role_user else None
    get_role.short_description = 'Role'
