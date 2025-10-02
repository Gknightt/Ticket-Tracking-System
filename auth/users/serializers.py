from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from .models import User, UserOTP, PasswordResetToken
import hashlib
import requests


def check_password_pwned(password):
    """
    Check if password has been compromised using HaveIBeenPwned API.
    Returns True if password is compromised, False otherwise.
    """
    try:
        # Create SHA-1 hash of the password
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        
        # Use k-anonymity - only send first 5 characters of hash
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        
        # Query HaveIBeenPwned API
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            # Check if our hash suffix appears in the results
            for line in response.text.splitlines():
                hash_suffix, count = line.split(':')
                if hash_suffix == suffix:
                    return True, int(count)  # Password is compromised
            return False, 0  # Password not found in breach database
        else:
            # If API is unavailable, don't block password creation
            return False, 0
            
    except Exception:
        # If there's any error (network, timeout, etc.), don't block password creation
        return False, 0
import hashlib
import requests

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'first_name', 'last_name', 'phone_number')

    def validate_password(self, value):
        # NIST 800-63B password requirements
        min_length = 8
        max_length = 128
        if len(value) < min_length:
            raise serializers.ValidationError(f"Password must be at least {min_length} characters long.")
        if len(value) > max_length:
            raise serializers.ValidationError(f"Password must be at most {max_length} characters long.")

        # No composition rules (no need to check for digits, uppercase, etc.)

        # Check for username/email in password
        username = self.initial_data.get('username', '').lower()
        email = self.initial_data.get('email', '').lower()
        if username and username in value.lower():
            raise serializers.ValidationError("Password must not contain your username.")
        if email and email.split('@')[0] in value.lower():
            raise serializers.ValidationError("Password must not contain part of your email address.")

        # Check against common passwords (placeholder, replace with real check or API call)
        common_passwords = {"password", "12345678", "qwerty", "letmein", "admin", "welcome", "admin123", "password123"}
        if value.lower() in common_passwords:
            raise serializers.ValidationError("Password is too common.")

        # Check against HaveIBeenPwned API for breached passwords
        is_pwned, breach_count = check_password_pwned(value)
        if is_pwned:
            raise serializers.ValidationError(
                f"This password has been found in {breach_count:,} data breaches. Please choose a different password."
            )

        return value

    def create(self, validated_data):
        # This create method handles the password hashing.
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data.get('username'),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number')
        )
        return user

# Protected Profile endpoint (accessible if provided valid access token in the request header)
# Serializer to safely display user data (without showing password)
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'date_joined', 'otp_enabled')


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile information."""
    email = serializers.EmailField(required=False)
    username = serializers.CharField(max_length=150, required=False)
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'phone_number')

    def validate_email(self, value):
        """Validate that email is unique (excluding current user)."""
        user = self.instance
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        """Validate that username is unique (excluding current user)."""
        user = self.instance
        if User.objects.filter(username=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_phone_number(self, value):
        """Validate that phone number is unique (excluding current user)."""
        if value:  # Only validate if phone number is provided
            user = self.instance
            if User.objects.filter(phone_number=value).exclude(pk=user.pk).exists():
                raise serializers.ValidationError("A user with this phone number already exists.")
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer that supports 2FA with OTP and system-specific roles."""
    otp_code = serializers.CharField(max_length=6, required=False, allow_blank=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['username'] = user.username
        
        # Add system-specific roles using the existing UserSystemRole model
        roles = []
        
        # Get all user roles across different systems
        user_system_roles = user.system_roles.select_related('system', 'role').all()
        for user_role in user_system_roles:
            roles.append({
                'system': user_role.system.slug,  # Using system slug as identifier
                'role': user_role.role.name
            })
        
        token['roles'] = roles
        return token

    def validate(self, attrs):
        from django.utils import timezone
        from datetime import timedelta
        LOCKOUT_THRESHOLD = 5  # Number of allowed failed attempts
        LOCKOUT_TIME = timedelta(minutes=15)  # Lockout duration

        email = attrs.get(self.username_field)
        password = attrs.get('password')
        otp_code = attrs.get('otp_code', '')

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None

            # If user exists, check lockout status
            if user:
                if user.is_locked:
                    # Check if lockout period has expired
                    if user.lockout_time and timezone.now() >= user.lockout_time + LOCKOUT_TIME:
                        user.is_locked = False
                        user.failed_login_attempts = 0
                        user.lockout_time = None
                        user.save(update_fields=["is_locked", "failed_login_attempts", "lockout_time"])
                    else:
                        raise serializers.ValidationError(
                            "Account is locked due to too many failed login attempts. Please try again later.",
                            code="account_locked"
                        )

            user_auth = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user_auth:
                # Increment failed attempts if user exists
                if user:
                    user.failed_login_attempts += 1
                    if user.failed_login_attempts >= LOCKOUT_THRESHOLD:
                        user.is_locked = True
                        user.lockout_time = timezone.now()
                    user.save(update_fields=["failed_login_attempts", "is_locked", "lockout_time"])
                raise serializers.ValidationError(
                    'Invalid email or password.',
                    code='authorization'
                )

            # Reset failed attempts on successful login
            if user:
                user.failed_login_attempts = 0
                user.is_locked = False
                user.lockout_time = None
                user.save(update_fields=["failed_login_attempts", "is_locked", "lockout_time"])

            # Check if 2FA is enabled for this user
            if user_auth.otp_enabled:
                # Check if OTP code is empty or missing
                if not otp_code or otp_code.strip() == '':
                    raise serializers.ValidationError(
                        'OTP code is required for this account. Please provide the OTP code.',
                        code='otp_required'
                    )

                # Get the most recent valid OTP for this user
                otp_instance = UserOTP.get_valid_otp_for_user(user_auth)
                if not otp_instance:
                    raise serializers.ValidationError(
                        'No valid OTP found. Please request a new OTP code.',
                        code='otp_expired'
                    )
                
                # Verify the provided OTP code
                if not otp_instance.verify(otp_code):
                    raise serializers.ValidationError(
                        'Invalid OTP code. Please check your code and try again.',
                        code='otp_invalid'
                    )

            # Standard JWT token generation
            self.user = user_auth
            refresh = self.get_token(user_auth)

            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }

        raise serializers.ValidationError(
            'Must include "email" and "password".',
            code='authorization'
        )


class OTPRequestSerializer(serializers.Serializer):
    """Serializer for requesting OTP generation."""
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        if not user:
            raise serializers.ValidationError(
                'Invalid credentials',
                code='authorization'
            )

        if not user.otp_enabled:
            raise serializers.ValidationError(
                '2FA is not enabled for this account',
                code='2fa_not_enabled'
            )

        attrs['user'] = user
        return attrs


class Enable2FASerializer(serializers.Serializer):
    """Serializer for enabling 2FA on user account."""
    password = serializers.CharField()

    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Invalid password')
        return value


class Disable2FASerializer(serializers.Serializer):
    """Serializer for disabling 2FA on user account."""
    password = serializers.CharField()
    otp_code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        user = self.context['request'].user
        password = attrs.get('password')
        otp_code = attrs.get('otp_code')

        if not user.check_password(password):
            raise serializers.ValidationError('Invalid password')

        if not user.otp_enabled:
            raise serializers.ValidationError('2FA is not enabled for this account')

        # Get the most recent valid OTP for this user
        otp_instance = UserOTP.get_valid_otp_for_user(user)
        if not otp_instance or not otp_instance.verify(otp_code):
            raise serializers.ValidationError('Invalid or expired OTP code')

        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for requesting password reset."""
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            # Don't reveal whether the email exists or not for security
            # Still return the email to proceed with the flow
            pass
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password with token."""
    token = serializers.CharField()
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        token = attrs.get('token')
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password != password_confirm:
            raise serializers.ValidationError('Passwords do not match')

        # NIST 800-63B password requirements (same as registration)
        min_length = 8
        max_length = 128
        if len(password) < min_length:
            raise serializers.ValidationError(f"Password must be at least {min_length} characters long.")
        if len(password) > max_length:
            raise serializers.ValidationError(f"Password must be at most {max_length} characters long.")

        # No composition rules

        # Check for username/email in password (if user can be determined from token)
        reset_token = PasswordResetToken.get_valid_token(token)
        if not reset_token:
            raise serializers.ValidationError('Invalid or expired reset token')
        user = getattr(reset_token, 'user', None)
        if user:
            username = getattr(user, 'username', '').lower()
            email = getattr(user, 'email', '').lower()
            if username and username in password.lower():
                raise serializers.ValidationError("Password must not contain your username.")
            if email and email.split('@')[0] in password.lower():
                raise serializers.ValidationError("Password must not contain part of your email address.")

        # Check against common passwords (placeholder)
        common_passwords = {"password", "12345678", "qwerty", "letmein", "admin", "welcome", "admin123", "password123"}
        if password.lower() in common_passwords:
            raise serializers.ValidationError("Password is too common.")

        # Check against HaveIBeenPwned API for breached passwords
        is_pwned, breach_count = check_password_pwned(password)
        if is_pwned:
            raise serializers.ValidationError(
                f"This password has been found in {breach_count:,} data breaches. Please choose a different password."
            )

        attrs['reset_token'] = reset_token
        return attrs


def send_otp_email(user, otp_code):
    """Send OTP code to user's email."""
    subject = 'Your Authentication Code'
    message = f'''
Hello {user.get_full_name() or user.email},

Your authentication code is: {otp_code}

This code will expire in 5 minutes. Please do not share this code with anyone.

If you did not request this code, please ignore this email.

Best regards,
Authentication Service Team
    '''
    
    try:
        send_mail(
            subject=subject,
            message=message.strip(),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Log the error in production
        print(f"Failed to send OTP email to {user.email}: {str(e)}")
        return False


def send_password_reset_email(user, reset_token, request=None):
    """Send password reset email to user."""
    # Build the reset URL
    if request:
        base_url = f"{request.scheme}://{request.get_host()}"
    else:
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    
    reset_url = f"{base_url}/reset-password?token={reset_token.token}"
    
    subject = 'Password Reset Request'
    message = f'''
Hello {user.get_full_name() or user.email},

We received a request to reset your password. If you made this request, please click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.

If you did not request a password reset, please ignore this email. Your password will remain unchanged.

Best regards,
Authentication Service Team
    '''
    
    try:
        send_mail(
            subject=subject,
            message=message.strip(),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Log the error in production
        print(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False


class ProfilePasswordResetSerializer(serializers.Serializer):
    """Serializer for resetting password from user profile."""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        current_password = attrs.get('current_password')
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')

        if not user.check_password(current_password):
            raise serializers.ValidationError({'current_password': 'Current password is incorrect.'})
        if new_password != new_password_confirm:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})

        # NIST 800-63B password requirements (same as registration)
        min_length = 8
        max_length = 128
        if len(new_password) < min_length:
            raise serializers.ValidationError({'new_password': f'Password must be at least {min_length} characters long.'})
        if len(new_password) > max_length:
            raise serializers.ValidationError({'new_password': f'Password must be at most {max_length} characters long.'})

        # Check for username/email in password
        username = user.username.lower() if user.username else ''
        email = user.email.lower() if user.email else ''
        if username and username in new_password.lower():
            raise serializers.ValidationError({'new_password': 'Password must not contain your username.'})
        if email and email.split('@')[0] in new_password.lower():
            raise serializers.ValidationError({'new_password': 'Password must not contain part of your email address.'})

        # Check against common passwords (including "admin123" and others)
        common_passwords = {"password", "12345678", "qwerty", "letmein", "admin", "welcome", "admin123", "password123"}
        if new_password.lower() in common_passwords:
            raise serializers.ValidationError({'new_password': 'Password is too common.'})

        # Check against HaveIBeenPwned API for breached passwords
        is_pwned, breach_count = check_password_pwned(new_password)
        if is_pwned:
            raise serializers.ValidationError({
                'new_password': f"This password has been found in {breach_count:,} data breaches. Please choose a different password."
            })

        return attrs


class UserSystemRoleSerializer(serializers.ModelSerializer):
    """Serializer for viewing user's system roles using existing UserSystemRole model."""
    system_name = serializers.CharField(source='system.name', read_only=True)
    system_slug = serializers.CharField(source='system.slug', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        from system_roles.models import UserSystemRole
        model = UserSystemRole
        fields = ('id', 'system_name', 'system_slug', 'role_name', 'assigned_at')
        read_only_fields = ('id', 'assigned_at')


class UserWithSystemRolesSerializer(serializers.ModelSerializer):
    """Serializer for viewing user's system roles."""
    system_roles = UserSystemRoleSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'system_roles')


class AssignSystemRoleSerializer(serializers.Serializer):
    """Serializer for assigning a system role to a user using existing models."""
    user_email = serializers.EmailField()
    system_slug = serializers.CharField(max_length=255)
    role_name = serializers.CharField(max_length=150)

    def validate_user_email(self, value):
        try:
            user = User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist or is inactive.")
        return value

    def validate_system_slug(self, value):
        from systems.models import System
        try:
            system = System.objects.get(slug=value)
        except System.DoesNotExist:
            raise serializers.ValidationError("System with this slug does not exist.")
        return value

    def validate(self, attrs):
        from systems.models import System
        from roles.models import Role
        from system_roles.models import UserSystemRole
        
        user_email = attrs.get('user_email')
        system_slug = attrs.get('system_slug')
        role_name = attrs.get('role_name')
        
        try:
            user = User.objects.get(email=user_email, is_active=True)
            system = System.objects.get(slug=system_slug)
            role = Role.objects.get(system=system, name=role_name)
            
            # Check if this assignment already exists
            if UserSystemRole.objects.filter(
                user=user, 
                system=system, 
                role=role
            ).exists():
                raise serializers.ValidationError(
                    f"User already has the role '{role_name}' in system '{system.name}'"
                )
            
            attrs['user'] = user
            attrs['system'] = system
            attrs['role'] = role
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist or is inactive.")
        except System.DoesNotExist:
            raise serializers.ValidationError("System with this slug does not exist.")
        except Role.DoesNotExist:
            raise serializers.ValidationError(f"Role '{role_name}' does not exist in system '{system_slug}'.")
        
        return attrs

    def create(self, validated_data):
        from system_roles.models import UserSystemRole
        user = validated_data.pop('user')
        system = validated_data.pop('system')
        role = validated_data.pop('role')
        return UserSystemRole.objects.create(user=user, system=system, role=role)