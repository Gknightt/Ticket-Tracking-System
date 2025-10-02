import uuid
import secrets
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

# Custom manager for handling user creation and superuser creation
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a regular User with the given email and password.
        ensures email is provided and normalizes it
        If username is not provided, uses the part before '@' in the email
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        
        username = extra_fields.pop('username', None)
        if not username:
            username = email.split('@')[0]

        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and saves a SuperUser with the given email and password.
        Ensures is_staff and is_superuser are set to True
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

# Custom User model for authentication
class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)  # Integer primary key
    email = models.EmailField(unique=True)  # Used for login
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)  # Optional username
    first_name = models.CharField(max_length=100, blank=True)  # Optional first name
    last_name = models.CharField(max_length=100, blank=True)  # Optional last name
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Optional phone number
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)  # Optional profile image

    is_active = models.BooleanField(default=True)  # Can login
    is_staff = models.BooleanField(default=False)  # Admin site access
    is_superuser = models.BooleanField(default=False)  # All permissions

    # 2FA settings
    otp_enabled = models.BooleanField(default=False)  # Whether 2FA is enabled for this user

    # Account lockout mechanism
    failed_login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    lockout_time = models.DateTimeField(null=True, blank=True)

    last_login = models.DateTimeField(null=True, blank=True)  # Last login timestamp
    date_joined = models.DateTimeField(auto_now_add=True)  # Account creation timestamp

    objects = CustomUserManager()  # Use custom manager

    USERNAME_FIELD = 'email'  # Field used for authentication
    REQUIRED_FIELDS = ['username']  # Required when creating superuser

    def get_full_name(self):
        """Returns the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        """String representation of the user (email)."""
        return self.email


class UserOTP(models.Model):
    """Model to store OTP codes for 2FA authentication."""
    
    OTP_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPE_CHOICES, default='email')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_used', 'expires_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if OTP has expired."""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if OTP is valid (not used, not expired, attempts not exceeded)."""
        return (
            not self.is_used and 
            not self.is_expired() and 
            self.attempts < self.max_attempts
        )
    
    def verify(self, provided_otp):
        """Verify the provided OTP code."""
        self.attempts += 1
        self.save(update_fields=['attempts'])
        
        if not self.is_valid():
            return False
        
        if self.otp_code == provided_otp:
            self.is_used = True
            self.save(update_fields=['is_used'])
            return True
        
        return False
    
    @classmethod
    def generate_for_user(cls, user, otp_type='email'):
        """Generate a new OTP for the user and invalidate old ones."""
        # Invalidate old unused OTPs
        cls.objects.filter(
            user=user, 
            is_used=False, 
            otp_type=otp_type
        ).update(is_used=True)
        
        # Generate new OTP
        otp_code = f"{secrets.randbelow(1000000):06d}"
        otp = cls.objects.create(
            user=user,
            otp_code=otp_code,
            otp_type=otp_type
        )
        return otp
    
    @classmethod
    def get_valid_otp_for_user(cls, user, otp_type='email'):
        """Get the most recent valid OTP for a user."""
        return cls.objects.filter(
            user=user,
            otp_type=otp_type,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp_type} - {'Used' if self.is_used else 'Active'}"


class PasswordResetToken(models.Model):
    """Model to store password reset tokens."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token', 'is_used', 'expires_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Password reset tokens expire in 1 hour
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if token has expired."""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired()
    
    @classmethod
    def generate_for_user(cls, user):
        """Generate a new password reset token for the user and invalidate old ones."""
        # Invalidate old unused tokens
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate new token
        token = secrets.token_urlsafe(48)
        reset_token = cls.objects.create(
            user=user,
            token=token
        )
        return reset_token
    
    @classmethod
    def get_valid_token(cls, token):
        """Get a valid token instance."""
        try:
            token_instance = cls.objects.get(
                token=token,
                is_used=False,
                expires_at__gt=timezone.now()
            )
            return token_instance
        except cls.DoesNotExist:
            return None
    
    def use_token(self):
        """Mark token as used."""
        self.is_used = True
        self.save(update_fields=['is_used'])
    
    def __str__(self):
        return f"Password reset token for {self.user.email} - {'Used' if self.is_used else 'Active'}"


# check AbstractUser documentation for more details
# class User(AbstractUser):
#     middle_name = models.CharField(max_length=50, blank=True)
#     email = models.EmailField(unique=True)
#     phone_number = models.CharField(max_length=20, blank=False)

#     USERNAME_FIELD = "email"
#     REQUIRED_FIELDS = ["username"]

#     def __str__(self) -> str:
#         return self.email


# Manager to handle user creation (e.g., 'create_user', 'create_superuser')
# auth_service/users/models.py
