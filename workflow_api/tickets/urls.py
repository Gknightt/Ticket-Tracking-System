# workflow_service/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'tickets', WorkflowTicketViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('assign-task/', ManualTaskAssignmentView.as_view(), name='manual-task-assignment'),
]