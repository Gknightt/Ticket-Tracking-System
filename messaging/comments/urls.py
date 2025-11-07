from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommentViewSet, CommentRatingViewSet

router = DefaultRouter()
router.register(r'comments', CommentViewSet)
router.register(r'ratings', CommentRatingViewSet)

urlpatterns = [
    path('', include(router.urls)),
]