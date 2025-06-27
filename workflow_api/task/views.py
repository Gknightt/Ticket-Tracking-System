from django.shortcuts import render
from rest_framework import generics
from .serializers import TaskSerializer
from .models import Task

class TaskListView(generics.ListAPIView):
    """
    API view to list all tasks.
    """
    serializer_class = TaskSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned tasks to a given user,
        by filtering against a `task_id` query parameter in the URL.
        """
        queryset = Task.objects.all()  # Use `.all()` to avoid caching issues
        task_id = self.request.query_params.get('task_id', None)
        if task_id is not None:
            queryset = queryset.filter(task_id=task_id)
        return queryset