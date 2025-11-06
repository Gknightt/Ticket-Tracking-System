# urls.py

from django.urls import path
from .views import *

urlpatterns = [
    path('projects/', ProjectListView.as_view(), name='project-list'),
    path('projects/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('projects/approve/<str:ticket_id>/', ProjectApproveView.as_view(), name='project-approve'),
    path('projects/update-project-status/', UpdateProjectStatusView.as_view(), name='update-project-status'),
]
