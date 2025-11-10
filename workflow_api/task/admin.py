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
    list_display = ['task_item_id', 'task', 'user_id', 'username', 'role', 'status', 'assigned_on']
    list_filter = ['status', 'role', 'assigned_on']
    search_fields = ['task__task_id', 'user_id', 'username', 'email']
    readonly_fields = ['task_item_id', 'assigned_on']
    
    fieldsets = (
        ('Assignment Info', {
            'fields': ('task_item_id', 'task', 'user_id', 'username', 'email', 'role')
        }),
        ('Status', {
            'fields': ('status', 'assigned_on', 'status_updated_on', 'acted_on')
        }),
    )
