"""
URL configuration for messaging project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.decorators import api_view
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Import viewsets for the main API router
from comments.views import CommentViewSet, CommentRatingViewSet

# Create main API router for viewset-based endpoints
router = DefaultRouter()
router.register(r'comments', CommentViewSet)
router.register(r'ratings', CommentRatingViewSet)

@api_view(['GET'])
def api_root(request):
    """
    API Root - Messaging Service
    
    This messaging service provides endpoints for:
    - Comments: Create, read, update comments with document attachments
    - Ratings: Rate comments (thumbs up/down)
    - Tickets: Manage ticket information
    - Document Management: Upload, download, and manage file attachments
    
    Key Features:
    - Document deduplication based on file hash
    - Nested comment replies
    - User ownership tracking
    - File attachment support
    """
    return Response({
        'message': 'Welcome to the Messaging Service API',
        'version': '1.0.0',
        'endpoints': {
            'comments': request.build_absolute_uri('/api/comments/'),
            'ratings': request.build_absolute_uri('/api/ratings/'),
            'tickets': request.build_absolute_uri('/api/tickets/'),
            'documentation': request.build_absolute_uri('/api/docs/'),
            'schema': request.build_absolute_uri('/api/schema/'),
        },
        'features': [
            'Document attachment with deduplication',
            'Nested comment replies',
            'Comment rating system',
            'User ownership tracking',
            'File download and management'
        ]
    })

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API Root
    path('api/', api_root, name='api-root'),
    
    # Main API routes (DRF ViewSets)
    path('api/', include(router.urls)),
    
    # Individual app routes
    path('api/tickets/', include('tickets.urls')),
    path('api/comments/', include('comments.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # DRF Auth (for browsable API)
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
