from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, AddServiceView, GetServiceMappingsView

# Create a router and register the ServiceViewSet
router = DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')

urlpatterns = [
    path('', include(router.urls)),
    path('add/', AddServiceView.as_view(), name='add-service'),
    path('mappings/', GetServiceMappingsView.as_view(), name='service-mappings'),
]