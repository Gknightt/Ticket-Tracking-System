from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.decorators import api_view, permission_classes
from users.models import User
from roles.models import Role
from systems.models import System
from system_roles.models import UserSystemRole
from django.db.models import Q
from users.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import TTSUserWithRoleSerializer, AssignAgentToRoleSerializer
from users.decorators import jwt_cookie_required, tts_admin_required

# Create your views here.

class IsTTSAdmin(BasePermission):
    """
    Permission class to check if user is a TTS admin or superuser.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow superusers
        if request.user.is_superuser:
            return True
        
        # Check if user has Admin role in TTS system
        return UserSystemRole.objects.filter(
            user=request.user,
            role__name='Admin'
        ).exists()

class UserIDsByRoleView(APIView):
    """
    API endpoint for TTS round-robin user selection.
    Returns users that have the specified role_id or role_name.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        role_id = request.query_params.get('role_id')
        role_name = request.query_params.get('role_name')
        
        if not role_id and not role_name:
            return Response({"error": "Either role_id or role_name parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get TTS system
            try:
                tts_system = System.objects.get(slug='tts')
                
                # Set up filter for UserSystemRole query
                user_system_role_filter = {'system': tts_system}
                
                # If role_id is provided, try to use it
                if role_id:
                    try:
                        # Convert role_id to integer
                        role_id = int(role_id)
                        user_system_role_filter['role__id'] = role_id
                    except ValueError:
                        return Response({"error": "role_id must be a number."}, status=status.HTTP_400_BAD_REQUEST)
                # If role_name is provided, use case-insensitive matching
                elif role_name:
                    # Use iexact for case-insensitive matching
                    user_system_role_filter['role__name__iexact'] = role_name
                
                # Find users with this role in TTS
                user_system_roles = UserSystemRole.objects.filter(**user_system_role_filter)
                
                # Extract the user IDs
                user_ids = user_system_roles.values_list('user__id', flat=True)
                
                return Response(list(user_ids), status=status.HTTP_200_OK)
            
            except System.DoesNotExist:
                return Response([], status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserInfoByIDView(APIView):
    """
    API endpoint for fetching user information by user ID.
    Returns business and non-sensitive user information only.
    Requires JWT authentication for service-to-service communication.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            # Convert user_id to integer
            try:
                user_id = int(user_id)
            except ValueError:
                return Response({"error": "user_id must be a number."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Fetch user by ID
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            
            # Return only business and non-sensitive information
            user_info = {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "department": getattr(user, 'department', None),
                "position": getattr(user, 'position', None),
                "is_active": user.is_active,
                "date_joined": user.date_joined,
                # Add any other business-relevant fields that exist in your User model
            }
            
            return Response(user_info, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UsersInfoBatchView(APIView):
    """
    API endpoint for fetching multiple users' information in a batch request.
    Returns business and non-sensitive user information only.
    Requires JWT authentication for service-to-service communication.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Get employee_cookie_ids from request body
            employee_cookie_ids = request.data.get('employee_cookie_ids', [])
            
            if not employee_cookie_ids:
                return Response({"error": "employee_cookie_ids array is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            if not isinstance(employee_cookie_ids, list):
                return Response({"error": "employee_cookie_ids must be an array."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Convert all IDs to integers and validate
            try:
                employee_cookie_ids = [int(id_val) for id_val in employee_cookie_ids]
            except ValueError:
                return Response({"error": "All employee_cookie_ids must be numbers."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Fetch users by IDs
            users = User.objects.filter(id__in=employee_cookie_ids)
            
            # Build response mapping employee_cookie_id to user info
            user_info_map = {}
            for user in users:
                user_info_map[user.id] = {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "department": getattr(user, 'department', None),
                    "position": getattr(user, 'position', None),
                    "is_active": user.is_active,
                    "date_joined": user.date_joined,
                }
            
            return Response(user_info_map, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssignAgentToRoleView(GenericAPIView):
    """
    API endpoint for assigning existing TTS agents to TTS roles.
    Requires JWT authentication for service-to-service communication.
    
    The browsable API provides dropdown menus for:
    - userID: Select from available users
    - role: Select from available roles
    
    POST body:
    {
        "userID": <int>,
        "role": <int>  # role ID
    }
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = AssignAgentToRoleSerializer
    
    def post(self, request):
        try:
            # Validate input using serializer
            serializer = AssignAgentToRoleSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Extract validated data (both are already objects from PrimaryKeyRelatedField)
            user = serializer.validated_data['user']  # Mapped from userID via source='user'
            role_obj = serializer.validated_data['role']
            
            # Get TTS system
            try:
                tts_system = System.objects.get(slug='tts')
            except System.DoesNotExist:
                return Response(
                    {"error": "TTS system not found in database."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Check if user already has this specific role in TTS system
            existing_assignment = UserSystemRole.objects.filter(
                user=user,
                system=tts_system,
                role=role_obj
            ).first()
            
            if existing_assignment:
                # User already has this exact role in TTS
                return Response(
                    {
                        "message": "User is already assigned to this role in TTS.",
                        "userID": user.id,
                        "role": role_obj.name,
                        "system": tts_system.slug
                    },
                    status=status.HTTP_200_OK
                )
            
            # Get settings from request
            settings = request.data.get('settings', {})
            if not isinstance(settings, dict):
                settings = {}
            
            # Create new role assignment (user can have multiple roles)
            user_system_role = UserSystemRole.objects.create(
                user=user,
                system=tts_system,
                role=role_obj,
                settings=settings
            )
            
            return Response(
                {
                    "message": "User successfully assigned to TTS role.",
                    "userID": user.id,
                    "role": role_obj.name,
                    "system": tts_system.slug,
                    "settings": user_system_role.settings
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """
        Retrieve all TTS users and their assigned roles, plus available TTS roles.
        Returns a list of users with their role information and available roles.
        """
        try:
            # Check if user is authenticated
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {"error": "Authentication required"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Get TTS system
            try:
                tts_system = System.objects.get(slug='tts')
            except System.DoesNotExist:
                return Response(
                    {"error": "TTS system not found in database."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Fetch all user-system-role assignments for TTS
            user_system_roles = UserSystemRole.objects.filter(
                system=tts_system
            ).select_related('user', 'role')
            
            # Get all available TTS roles
            available_roles = Role.objects.filter(system=tts_system).values('id', 'name')
            
            users_data = []
            if user_system_roles.exists():
                # Serialize the data
                serializer = TTSUserWithRoleSerializer(user_system_roles, many=True)
                users_data = serializer.data
            
            return Response(
                {
                    "count": len(users_data),
                    "system": "tts",
                    "users": users_data,
                    "roles": list(available_roles)
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsTTSAdmin])
def assign_agent_to_role_form(request):
    """
    Render the assign agent to role form page for admins and superusers.
    This page allows admins to assign roles to agents.
    
    GET: Returns HTML form (or JSON with assignments/roles if Accept: application/json)
    Requires TTS admin or superuser privileges.
    Authentication: JWT cookie or Authorization header
    """
    # Check if JSON response is requested
    if request.headers.get('Accept') == 'application/json':
        try:
            # Get TTS system
            tts_system = System.objects.get(slug='tts')
            
            # Get all existing role assignments for TTS system
            assignments = UserSystemRole.objects.filter(system=tts_system).select_related('user', 'role')
            
            assignment_data = []
            for assignment in assignments:
                assignment_data.append({
                    'id': assignment.id,
                    'user_id': assignment.user.id,
                    'user_first_name': assignment.user.first_name,
                    'user_last_name': assignment.user.last_name,
                    'user_email': assignment.user.email,
                    'role_id': assignment.role.id,
                    'role_name': assignment.role.name,
                    'is_active': assignment.is_active,
                    'is_deployed': assignment.settings.get('is_deployed', False),
                    'created_at': assignment.assigned_at.isoformat()
                })
            
            # Get all available TTS roles
            all_roles = Role.objects.filter(system=tts_system).values('id', 'name')
            
            return Response({
                'assignments': assignment_data,
                'roles': list(all_roles)
            })
        except System.DoesNotExist:
            return Response(
                {"error": "TTS system not found"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # Return HTML form
    user = request.user
    context = {
        'user': user,
        'unread_count': 0,
    }
    return render(request, 'tts/assign_agent_to_role.html', context)


class CreateRoleView(APIView):
    """
    API endpoint for creating new TTS roles and retrieving roles.
    Requires JWT authentication and admin privileges.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            
            # Check admin privileges (any admin)
            if not user.is_superuser:
                is_admin = UserSystemRole.objects.filter(
                    user=user,
                    role__name='Admin'
                ).exists()
                if not is_admin:
                    return Response(
                        {"error": "You don't have permission to view roles"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Get TTS system
            try:
                tts_system = System.objects.get(slug='tts')
            except System.DoesNotExist:
                return Response(
                    {"error": "TTS system not found"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Get all roles in TTS system
            all_roles = Role.objects.filter(system=tts_system).values('id', 'name', 'description', 'is_custom', 'created_at')
            
            return Response({
                "roles": list(all_roles)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        try:
            user = request.user
            
            # Check admin privileges (any admin)
            if not user.is_superuser:
                is_admin = UserSystemRole.objects.filter(
                    user=user,
                    role__name='Admin'
                ).exists()
                if not is_admin:
                    return Response(
                        {"error": "You don't have permission to create roles"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Get TTS system
            try:
                tts_system = System.objects.get(slug='tts')
            except System.DoesNotExist:
                return Response(
                    {"error": "TTS system not found"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Get data from request
            name = request.data.get('name', '').strip()
            description = request.data.get('description', '').strip()
            
            if not name:
                return Response(
                    {"error": "Role name is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if role already exists in TTS
            existing_role = Role.objects.filter(
                system=tts_system,
                name__iexact=name
            ).first()
            
            if existing_role:
                return Response(
                    {
                        "error": f"Role '{name}' already exists in TTS system",
                        "role": {
                            "id": existing_role.id,
                            "name": existing_role.name
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create new role
            role = Role.objects.create(
                system=tts_system,
                name=name,
                description=description,
                is_custom=True
            )
            
            return Response(
                {
                    "message": f"Role '{name}' created successfully",
                    "role": {
                        "id": role.id,
                        "name": role.name,
                        "description": role.description
                    }
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateAssignmentView(APIView):
    """
    API endpoint for updating role assignment settings.
    Requires JWT authentication and admin privileges.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def put(self, request, assignment_id):
        try:
            user = request.user
            
            # Check admin privileges (any admin)
            if not user.is_superuser:
                is_admin = UserSystemRole.objects.filter(
                    user=user,
                    role__name='Admin'
                ).exists()
                if not is_admin:
                    return Response(
                        {"error": "You don't have permission to update assignments"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Get the assignment
            try:
                assignment = UserSystemRole.objects.get(id=assignment_id)
            except UserSystemRole.DoesNotExist:
                return Response(
                    {"error": "Assignment not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Update is_active if provided
            if 'is_active' in request.data:
                assignment.is_active = request.data['is_active']
            
            # Update settings with is_deployed flag
            if 'settings' in request.data:
                settings = request.data['settings']
                if isinstance(settings, dict):
                    assignment.settings = settings
            
            assignment.save()
            
            return Response(
                {
                    "message": "Assignment updated successfully",
                    "id": assignment.id,
                    "is_active": assignment.is_active,
                    "settings": assignment.settings
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, assignment_id):
        try:
            user = request.user
            
            # Check admin privileges
            if not user.is_superuser:
                is_admin = UserSystemRole.objects.filter(
                    user=user,
                    role__name='Admin'
                ).exists()
                if not is_admin:
                    return Response(
                        {"error": "You don't have permission to delete assignments"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Get and delete the assignment
            try:
                assignment = UserSystemRole.objects.get(id=assignment_id)
                assignment.delete()
            except UserSystemRole.DoesNotExist:
                return Response(
                    {"error": "Assignment not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                {"message": "Assignment deleted successfully"},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@jwt_cookie_required
def role_management_view(request):
    """
    Render the TTS role management page for managing roles (create and view).
    """
    user = request.user
    
    # Check if user has permission to manage roles (any admin or superuser)
    if not user.is_superuser:
        is_admin = UserSystemRole.objects.filter(
            user=user,
            role__name='Admin'
        ).exists()
        
        if not is_admin:
            messages.error(request, 'Access denied. You need admin privileges to manage roles.')
            return redirect('profile-settings')
    
    context = {
        'user': user,
        'unread_count': 0,
    }
    return render(request, 'tts/manage_roles.html', context)


@jwt_cookie_required
@tts_admin_required
def role_assignments_view(request):
    """
    Render the TTS role assignments management page for managing agent role assignments.
    Requires TTS admin privileges.
    """
    user = request.user
    
    context = {
        'user': user,
        'unread_count': 0,
    }
    return render(request, 'tts/role_management_assignments.html', context)

