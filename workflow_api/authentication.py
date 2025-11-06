import jwt
from django.conf import settings
from django.http import JsonResponse
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class JWTCookieAuthentication(BaseAuthentication):
    """
    JWT authentication via cookies with system-level authorization
    """
    
    def authenticate(self, request):
        # Get JWT token from cookies
        token = request.COOKIES.get('access_token')
        
        if not token:
            return None
            
        try:
            # Decode JWT token
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=['HS256']
            )
            
            # Extract user information
            user_id = payload.get('user_id')
            email = payload.get('email')
            username = payload.get('username')
            roles = payload.get('roles', [])
            
            if not user_id:
                raise AuthenticationFailed('Invalid token: missing user_id')
            
            # Create a simple user object to store in request
            user_data = {
                'id': user_id,
                'user_id': user_id,
                'email': email,
                'username': username,
                'roles': roles,
                'tts_roles': [role for role in roles if role.get('system') == 'tts']
            }
            
            return (AuthenticatedUser(user_data), token)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationFailed('Authentication failed')


class TTSSystemPermission(BasePermission):
    """
    Permission class to ensure user has access to TTS system
    """
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'roles'):
            return False
        
        # Check if user has access to TTS system
        has_tts_access = any(
            role.get('system') == 'tts' 
            for role in request.user.roles
        )
        
        if not has_tts_access:
            return False
            
        return True
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


def jwt_required(view_func):
    """
    Decorator to require JWT authentication for view functions
    """
    def wrapper(request, *args, **kwargs):
        auth = JWTCookieAuthentication()
        try:
            user_auth = auth.authenticate(request)
            if user_auth is None:
                return JsonResponse(
                    {'error': 'Authentication required'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user_data, token = user_auth
            request.user = user_data
            request.auth = token
            
            return view_func(request, *args, **kwargs)
            
        except AuthenticationFailed as e:
            return JsonResponse(
                {'error': str(e)}, 
                status=status.HTTP_403_FORBIDDEN
            )
    
    return wrapper


class AuthenticatedUser:
    """
    Simple user class to store authenticated user data
    """
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.user_id = user_data.get('user_id')
        self.email = user_data.get('email')
        self.username = user_data.get('username')
        self.roles = user_data.get('roles', [])
        self.tts_roles = user_data.get('tts_roles', [])
        self.is_authenticated = True
    
    def has_tts_role(self, role_name):
        """Check if user has specific TTS role"""
        return any(
            role.get('role') == role_name 
            for role in self.tts_roles
        )