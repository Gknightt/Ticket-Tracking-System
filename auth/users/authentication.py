from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads tokens from cookies (non-HTTP-only)
    Falls back to standard Authorization header if cookie is not present
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Explicitly set these attributes from settings or use defaults
        self.user_id_field = getattr(settings, 'SIMPLE_JWT', {}).get('USER_ID_FIELD', 'id')
        self.user_id_claim = getattr(settings, 'SIMPLE_JWT', {}).get('USER_ID_CLAIM', 'user_id')
    
    def authenticate(self, request):
        # First try to get token from cookie
        raw_token = request.COOKIES.get('access_token')
        
        # If no cookie token, fall back to standard header authentication
        if raw_token is None:
            return super().authenticate(request)
        
        # Validate the token from cookie
        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        
        return (user, validated_token)
        
    def get_user(self, validated_token):
        """
        Attempt to find and return a user using the given validated token.
        Override to ensure proper ID type handling.
        """
        try:
            user_id = validated_token[self.user_id_claim]
            
            # Ensure the user_id is treated as an integer
            user_id = int(user_id) if not isinstance(user_id, int) else user_id
            
            user = self.user_model.objects.get(**{self.user_id_field: user_id})
            return user
        except (self.user_model.DoesNotExist, ValueError) as e:
            raise self.user_model.DoesNotExist(f'No user found with the given ID: {str(e)}')