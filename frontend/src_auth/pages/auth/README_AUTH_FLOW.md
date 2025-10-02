
## Overview

This authentication system provides secure user login with optional Two-Factor Authentication (2FA) using email-based OTP (One-Time Password). The system uses JWT tokens for session management and implements proper error handling for different authentication scenarios.

## Architecture

### Backend (Django REST Framework)
- **JWT Token Authentication** using `djangorestframework-simplejwt`
- **Custom Token Serializer** with 2FA support
- **OTP Management** with email delivery
- **Account Lockout** protection against brute force attacks
- **Proper HTTP Status Codes** for different authentication states

### Frontend (React)
- **Responsive Login Form** with conditional 2FA input
- **Automatic OTP Request** when 2FA is required
- **Error Handling** with user-friendly messages
- **Token Storage** in localStorage

## Authentication Flow

### 1. Initial Login Attempt

```
User submits email + password
    ↓
POST /api/v1/token/obtain/
    ↓
Backend validates credentials
```

#### Possible Outcomes:

**✅ Success (No 2FA)**
- Status: `200 OK`
- Response: `{ access: "jwt_token", refresh: "refresh_token" }`
- Frontend: Stores tokens and redirects user

**🔐 2FA Required**
- Status: `428 Precondition Required`
- Backend: User has 2FA enabled but no OTP provided
- Frontend: Automatically requests OTP and shows OTP input form

**❌ Invalid Credentials**
- Status: `400 Bad Request`
- Response: `{ detail: "Invalid email or password." }`
- Frontend: Shows error message

**🔒 Account Locked**
- Status: `400 Bad Request`
- Response: `{ detail: "Account locked due to failed attempts." }`
- Frontend: Shows lockout message

### 2. 2FA Flow (When Status 428 is Received)

```
Frontend detects 428 status
    ↓
Automatically calls POST /api/v1/users/2fa/request-otp/
    ↓
Backend generates 6-digit OTP and sends email
    ↓
Frontend shows OTP input form
    ↓
User enters OTP and submits
    ↓
POST /api/v1/token/obtain/ (with otp_code)
    ↓
Backend validates OTP and returns tokens
```

#### OTP Validation Outcomes:

**✅ Valid OTP**
- Status: `200 OK`
- Response: `{ access: "jwt_token", refresh: "refresh_token" }`

**❌ Invalid OTP**
- Status: `403 Forbidden`
- Response: `{ detail: "Invalid OTP code", error_code: "otp_invalid" }`

**⏰ Expired OTP**
- Status: `403 Forbidden`
- Response: `{ detail: "OTP expired", error_code: "otp_expired" }`

## Backend Implementation Details

### Key Files

#### `users/serializers.py` - CustomTokenObtainPairSerializer
```python
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    otp_code = serializers.CharField(max_length=6, required=False, allow_blank=True)
    
    def validate(self, attrs):
        # Authenticate with email/password
        user_auth = authenticate(username=email, password=password)
        
        # Check if 2FA is enabled
        if user_auth.otp_enabled:
            if not otp_code or otp_code.strip() == '':
                raise ValidationError('OTP required', code='otp_required')
            
            # Validate OTP
            otp_instance = UserOTP.get_valid_otp_for_user(user_auth)
            if not otp_instance.verify(otp_code):
                raise ValidationError('Invalid OTP', code='otp_invalid')
```

#### `users/views.py` - CustomTokenObtainPairView
```python
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            # Return 428 for OTP required (triggers 2FA flow)
            if 'otp_required' in error_codes:
                return Response(
                    {'detail': 'OTP required'}, 
                    status=status.HTTP_428_PRECONDITION_REQUIRED
                )
```

#### `users/models.py` - UserOTP Model
```python
class UserOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()  # 5-minute expiry
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    @classmethod
    def generate_for_user(cls, user):
        # Generate 6-digit OTP and send email
        
    def verify(self, provided_otp):
        # Verify OTP with attempt tracking
```

## Frontend Implementation Details

### Key Files

#### `api/useLogin.jsx` - Authentication Hook
```javascript
export function useLogin() {
  const handleLogin = async (e) => {
    try {
      const response = await axios.post(tokenURL, loginData);
      // Store tokens on success
      localStorage.setItem("accessToken", response.data.access);
    } catch (err) {
      if (statusCode === 428) {
        // 2FA required - request OTP and show OTP form
        await requestOTP();
        setShowOTP(true);
      } else {
        // Show error message
        setError(errorMessage);
      }
    }
  };
}
```

#### `pages/auth/Login.jsx` - Login Component
```jsx
function Login() {
  const { showOTP, handleLogin, handleOTPSubmit } = useLogin();
  
  return (
    <form onSubmit={!showOTP ? handleLogin : handleOTPSubmit}>
      {!showOTP ? (
        // Email + Password form
      ) : (
        // OTP input form
      )}
    </form>
  );
}
```

## API Endpoints

### Authentication Endpoints

| Endpoint | Method | Purpose | Required Fields |
|----------|--------|---------|----------------|
| `/api/v1/token/obtain/` | POST | Get JWT tokens | `email`, `password`, `otp_code` (optional) |
| `/api/v1/token/refresh/` | POST | Refresh access token | `refresh` |
| `/api/v1/token/verify/` | POST | Verify token validity | `token` |

### 2FA Endpoints

| Endpoint | Method | Purpose | Required Fields |
|----------|--------|---------|----------------|
| `/api/v1/users/2fa/request-otp/` | POST | Request OTP code | `email`, `password` |
| `/api/v1/users/2fa/enable/` | POST | Enable 2FA | `password` |
| `/api/v1/users/2fa/disable/` | POST | Disable 2FA | `password`, `otp_code` |

### Password Reset Endpoints

| Endpoint | Method | Purpose | Required Fields |
|----------|--------|---------|----------------|
| `/api/v1/users/password/reset/` | POST | Request reset link | `email` |
| `/api/v1/users/password/reset/confirm/` | POST | Reset with token | `token`, `password`, `password_confirm` |

## Security Features

### Account Protection
- **Failed Login Tracking**: Tracks failed attempts per user
- **Account Lockout**: Locks account after 5 failed attempts for 15 minutes
- **Rate Limiting**: Prevents brute force attacks

### OTP Security
- **Time-Limited**: OTPs expire after 5 minutes
- **Single Use**: OTPs are invalidated after successful use
- **Attempt Limiting**: Maximum 3 verification attempts per OTP
- **Secure Generation**: Cryptographically secure random 6-digit codes

### Token Security
- **JWT Tokens**: Stateless authentication with expiration
- **Refresh Tokens**: Secure token renewal mechanism
- **Token Rotation**: Refresh tokens are rotated on use

## Environment Variables

### Backend (.env)
```env
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourapp.com

# JWT Configuration
SECRET_KEY=your-secret-key
```

### Frontend (.env)
```env
VITE_USER_SERVER_API=http://127.0.0.1:8000/api/v1/
```

## User Experience Flow

### Login Without 2FA
1. User enters email/password
2. Clicks "Log In"
3. Immediately redirected to dashboard

### Login With 2FA
1. User enters email/password
2. Clicks "Log In"
3. System automatically sends OTP to email
4. Form switches to OTP input
5. User enters 6-digit code from email
6. Clicks "Verify OTP"
7. Redirected to dashboard

### Error Scenarios
- **Wrong credentials**: Clear error message
- **Account locked**: Informative lockout message
- **Invalid OTP**: Specific OTP error with retry option
- **Expired OTP**: Option to request new OTP

## Status Code Reference

| Status Code | Meaning | Frontend Action |
|-------------|---------|----------------|
| `200` | Success | Store tokens, redirect |
| `400` | Bad Request | Show error message |
| `403` | Forbidden | Show specific error (OTP issues) |
| `428` | Precondition Required | Trigger 2FA flow |
| `500` | Server Error | Show generic error |

## Testing the System

### Test User Accounts
```
Email: admin@example.com
Password: admin123
2FA: Enabled (check email for OTP)

Email: user@example.com  
Password: password123
2FA: Disabled (direct login)
```

### Test Scenarios
1. **Normal Login**: Use user without 2FA
2. **2FA Login**: Use admin account, check email for OTP
3. **Wrong Password**: Test account lockout after 5 attempts
4. **Expired OTP**: Wait 5+ minutes and try old OTP
5. **Invalid OTP**: Enter wrong code multiple times

## Troubleshooting

### Common Issues

**OTP Email Not Received**
- Check email configuration in backend settings
- Verify SMTP credentials
- Check spam/junk folder

**428 Status Not Triggering 2FA**
- Ensure backend returns 428 for `otp_required` error
- Check browser network tab for actual status code
- Verify frontend status code checking logic

**Tokens Not Stored**
- Check browser localStorage in dev tools
- Verify successful 200 response contains tokens
- Check for JavaScript errors in console

### Debug Tips
- Use browser network tab to inspect API calls
- Check Django server logs for backend errors
- Use `console.log` to debug frontend state changes
- Test API endpoints directly with Postman/curl

## Future Enhancements

- **SMS OTP**: Alternative to email-based OTP
- **TOTP Support**: Google Authenticator integration
- **Remember Device**: Skip 2FA for trusted devices
- **Social Login**: OAuth integration
- **Password Strength**: Real-time password validation
- **Session Management**: Active session monitoring