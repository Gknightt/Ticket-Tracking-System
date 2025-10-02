from django.urls import path, include
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import serializers
from rest_framework.routers import DefaultRouter
from drf_spectacular.utils import extend_schema
from .views import (
    RegisterView, 
    ProfileView, 
    CustomTokenObtainPairView,
    CookieTokenRefreshView,
    CookieLogoutView,
    RequestOTPView, 
    Enable2FAView, 
    Disable2FAView,
    ForgotPasswordView,
    ResetPasswordView,
    UserViewSet,
    ProfilePasswordResetView
)

class PasswordResetSerializer(serializers.Serializer):
    forgot = serializers.URLField()
    reset = serializers.URLField()

class TwoFASerializer(serializers.Serializer):
    request_otp = serializers.URLField()
    enable = serializers.URLField()
    disable = serializers.URLField()

class UsersRootSerializer(serializers.Serializer):
    register = serializers.URLField()
    profile = serializers.URLField()
    list_users = serializers.URLField()
    password_reset = PasswordResetSerializer()
    two_fa = TwoFASerializer(source='2fa')

@extend_schema(responses=UsersRootSerializer)
@api_view(['GET'])
def users_root(request):
    return Response({
        "register": request.build_absolute_uri("register/"),
        "profile": request.build_absolute_uri("profile/"),
        "list_users": request.build_absolute_uri("users/"),
        "password_reset": {
            "forgot": request.build_absolute_uri("password/forgot/"),
            "reset": request.build_absolute_uri("password/reset/"),
        },
        "2fa": {
            "request_otp": request.build_absolute_uri("2fa/request-otp/"),
            "enable": request.build_absolute_uri("2fa/enable/"),
            "disable": request.build_absolute_uri("2fa/disable/"),
        }
    })

# Create router for UserViewSet
router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    # Root endpoint for users API discovery
    path('', users_root, name='users-root'),
    
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='user-register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='cookie-token-refresh'),
    path('logout/', CookieLogoutView.as_view(), name='cookie-logout'),
    
    # User profile endpoints
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('profile/reset-password/', ProfilePasswordResetView.as_view(), name='profile-password-reset'),
    
    # 2FA endpoints
    path('2fa/request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('2fa/enable/', Enable2FAView.as_view(), name='enable-2fa'),
    path('2fa/disable/', Disable2FAView.as_view(), name='disable-2fa'),
    
    # Password reset endpoints
    path('password/forgot/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('password/reset/', ResetPasswordView.as_view(), name='reset-password'),
    
    # User management endpoints (for admins) - include router URLs
    path('', include(router.urls)),
]
