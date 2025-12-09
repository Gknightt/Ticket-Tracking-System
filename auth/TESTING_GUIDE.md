# Authentication Routing Middleware - Testing Guide

## Overview
This guide helps verify that the new middleware-based authentication and routing system works correctly.

## Test Setup

### Prerequisites
1. Ensure both Staff and Employee accounts exist in the database
2. Verify JWT signing key is configured in settings
3. Confirm SYSTEM_TEMPLATE_URLS are set in settings (especially HDTS_SYSTEM_URL)

### Environment Variables to Check
```bash
# In auth/.env
DJANGO_JWT_SIGNING_KEY=<your-signing-key>
HDTS_SYSTEM_URL=http://localhost:3000/hdts
TTS_SYSTEM_URL=http://localhost:1000
```

## Test Scenarios

### 1. Staff User Authentication

#### 1.1 Staff Login
```
POST /api/v1/users/login/api/
Body: {
  "email": "staff@example.com",
  "password": "password123",
  "g_recaptcha_response": "<token>"
}

Expected Response:
{
  "access": "<token>",
  "refresh": "<token>"
}

Token Payload Should Contain:
{
  "user_id": 1,
  "user_type": "staff",  <-- KEY
  "email": "staff@example.com",
  "username": "staff",
  "roles": [...]
}
```

#### 1.2 Staff Access /staff/settings/profile/
```
Request: GET /staff/settings/profile/
Headers: Cookie: access_token=<staff-token>

Expected: 200 OK - Profile settings page rendered

Middleware Flow:
1. Authenticate JWT → request.user_type = 'staff', request.user_id = 1
2. Check if public path → No
3. Check if staff endpoint → Yes
4. Apply staff routing rules → Allow access
5. Render profile_settings_view with request.user set
```

#### 1.3 Staff Access Employee Endpoint
```
Request: GET /profile-settings/
Headers: Cookie: access_token=<staff-token>

Expected: 302 Redirect to /staff/settings/profile/

Middleware Flow:
1. Authenticate JWT → request.user_type = 'staff'
2. Check if employee endpoint → Yes
3. Apply routing rules for staff → Redirect to staff endpoint
```

#### 1.4 Staff Access Invalid Endpoint (404/500)
```
Request: GET /some-invalid-path/
Headers: Cookie: access_token=<staff-token>

Expected: 302 Redirect to http://localhost:3000/hdts (HDTS_SYSTEM_URL)

Middleware Flow:
1. Authenticate JWT → request.user_type = 'staff'
2. Check if endpoint is invalid → Yes (Django will 404)
3. Apply routing rule → Redirect to HDTS system
```

### 2. Employee User Authentication

#### 2.1 Employee Login
```
POST /api/v1/hdts/employees/api/login/
Body: {
  "email": "employee@example.com",
  "password": "password123"
}

Expected Response:
{
  "access": "<token>",
  "refresh": "<token>"
}

Token Payload Should Contain:
{
  "user_id": 456,  <-- Employee ID, also used as user_id
  "employee_id": 456,
  "user_type": "employee",  <-- KEY
  "email": "employee@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### 2.2 Employee Access /profile-settings/
```
Request: GET /profile-settings/
Headers: Cookie: access_token=<employee-token>

Expected: 200 OK - Employee profile settings page rendered

Middleware Flow:
1. Authenticate JWT → request.user_type = 'employee', request.user_id = 456
2. Check if public path → No
3. Check if employee endpoint → Yes
4. Apply employee routing rules → Allow access
5. Render employee profile view
```

#### 2.3 Employee Access Staff Endpoint
```
Request: GET /staff/settings/profile/
Headers: Cookie: access_token=<employee-token>

Expected: 302 Redirect to /profile-settings/

Middleware Flow:
1. Authenticate JWT → request.user_type = 'employee'
2. Check if staff endpoint → Yes
3. Apply routing rules for employee → Redirect to employee endpoint
```

#### 2.4 Employee Access Invalid Endpoint (404/500)
```
Request: GET /some-invalid-path/
Headers: Cookie: access_token=<employee-token>

Expected: 302 Redirect to http://localhost:3000/hdts

Middleware Flow:
1. Authenticate JWT → request.user_type = 'employee'
2. Check if endpoint is invalid → Yes
3. Apply routing rule → Redirect to HDTS system
```

### 3. Unauthenticated User

#### 3.1 No Token Access Protected Endpoint
```
Request: GET /staff/settings/profile/
Headers: (no cookies)

Expected: 302 Redirect to /staff/login/?next=/staff/settings/profile/

Middleware Flow:
1. Try to authenticate JWT → No token found
2. Check if public path → No
3. Not authenticated → Redirect to login
```

#### 3.2 Invalid Token Access Protected Endpoint
```
Request: GET /staff/settings/profile/
Headers: Cookie: access_token=invalid-token

Expected: 302 Redirect to /staff/login/?next=/staff/settings/profile/

Middleware Flow:
1. Try to authenticate JWT → Invalid token
2. Check if public path → No
3. Not authenticated → Redirect to login
```

#### 3.3 Expired Token Access Protected Endpoint
```
Request: GET /staff/settings/profile/
Headers: Cookie: access_token=<expired-token>

Expected: 302 Redirect to /staff/login/?next=/staff/settings/profile/

Middleware Flow:
1. Try to authenticate JWT → Token expired
2. Check if public path → No
3. Not authenticated → Redirect to login
```

### 4. Public Endpoint Access (No Auth Required)

#### 4.1 Staff Login Page
```
Request: GET /staff/login/

Expected: 200 OK - Login form rendered
```

#### 4.2 Employee Login Page
```
Request: GET /login/

Expected: 200 OK - Employee login form rendered
```

#### 4.3 Static Files
```
Request: GET /static/css/style.css

Expected: 200 OK - CSS file served
```

## Automated Testing

### Using curl

#### Test Staff Login and Access
```bash
# Login as staff
STAFF_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/users/login/api/ \
  -H "Content-Type: application/json" \
  -d '{"email":"staff@example.com","password":"password123","g_recaptcha_response":"dummy"}' \
  | jq -r '.access')

# Access staff endpoint
curl -b "access_token=$STAFF_TOKEN" http://localhost:8000/staff/settings/profile/ -i

# Try to access employee endpoint (should redirect)
curl -b "access_token=$STAFF_TOKEN" http://localhost:8000/profile-settings/ -i -L
```

#### Test Employee Login and Access
```bash
# Login as employee
EMP_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/hdts/employees/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"employee@example.com","password":"password123"}' \
  | jq -r '.access')

# Access employee endpoint
curl -b "access_token=$EMP_TOKEN" http://localhost:8000/profile-settings/ -i

# Try to access staff endpoint (should redirect)
curl -b "access_token=$EMP_TOKEN" http://localhost:8000/staff/settings/profile/ -i -L
```

## Debugging

### Enable Logging
Add to settings.py:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'users.authentication_middleware': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### Check JWT Token Claims
```python
# In Django shell
from rest_framework_simplejwt.tokens import AccessToken

token_str = "<your-token>"
token = AccessToken(token_str)
print(token.payload)
```

### Verify Middleware is Loaded
```python
# In Django shell
from django.conf import settings
print(settings.MIDDLEWARE)
# Should include 'users.authentication_middleware.AuthenticationRoutingMiddleware'
```

## Common Issues & Solutions

### Issue: "No user_type claim in token"
**Solution**: Ensure token was generated after code changes. Regenerate by logging in again.

### Issue: "Redirect loop between /staff/login/ and /staff/"
**Solution**: Check if StaffNotAuthenticatedMixin is still active. It should only be on /staff/login/ view.

### Issue: "Employees can't access any pages"
**Solution**: Verify Employee model has id field and token includes user_id claim.

### Issue: "Middleware not routing correctly"
**Solution**: 
1. Enable debug logging
2. Check middleware order in MIDDLEWARE list
3. Verify SYSTEM_TEMPLATE_URLS in settings.py

## Performance Notes

The middleware performs minimal overhead:
- JWT validation is cached by rest_framework_simplejwt
- No database queries on every request (only token validation)
- Path checking is O(1) with set lookups

## Security Considerations

1. **JWT Secret**: Ensure DJANGO_JWT_SIGNING_KEY is strong and unique
2. **Token Expiry**: Configured in SIMPLE_JWT settings (default 8 hours for access)
3. **HTTPS**: Use in production (set CSRF_COOKIE_SECURE and SESSION_COOKIE_SECURE)
4. **CORS**: Verify CORS_ALLOWED_ORIGINS whitelist

## Next Steps After Verification

If all tests pass:
1. Remove old redirect utilities (optional cleanup):
   - get_system_redirect_url()
   - create_system_redirect_response()
   - StaffNotAuthenticatedMixin (if not used elsewhere)
   - StaffSystemRedirectMixin (if not used elsewhere)

2. Add more comprehensive error handling in middleware

3. Add audit logging for security events

4. Create employee-specific profile view for better UX
