# models.py

from django.db import models

class Project(models.Model):
    ticket_id = models.CharField(max_length=100, default='TK-000')
    title = models.CharField(max_length=255)
    project_summary = models.TextField()
    project_description = models.TextField()
    performance_notes = models.TextField(blank=True)
    
    department = models.IntegerField()
    fiscal_year = models.IntegerField()
    submitted_by_name = models.CharField(max_length=100)
    status = models.CharField(max_length=50)

    performance_start_date = models.DateField()
    performance_end_date = models.DateField()
    external_system_id = models.CharField(max_length=100, blank=True)

    items = models.JSONField(default=list)  # store array of dicts

    is_approved = models.BooleanField(default=False)
