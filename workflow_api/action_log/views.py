from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from .models import ActionLog
from .serializers import ActionLogSerializer

class ActionLogViewSet(viewsets.ModelViewSet):
    queryset = ActionLog.objects.all()
    serializer_class = ActionLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['task_id']  # ✅ Enable filtering by task_id
