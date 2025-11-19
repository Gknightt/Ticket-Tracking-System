# A.7 Security Measures

## Overview
The Ticket Tracking System implements comprehensive security measures to protect the system, its data, and users from potential threats. This document outlines authentication mechanisms, authorization rules, data encryption methods, and API security protocols.

## Authentication Mechanism

### JWT (JSON Web Tokens)
The system uses JWT for stateless authentication via the `djangorestframework_simplejwt` package.

**Implementation Details**:
- **Library**: `djangorestframework_simplejwt==5.5.0`
- **Token Types**:
  - **Access Token**: Short-lived (typically 5-15 minutes)
  - **Refresh Token**: Long-lived (typically 1-7 days)
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Secret Key**: Stored in environment variable `SECRET_KEY` or `JWT_SHARED_SECRET_KEY`

### Token Workflow
1. **Login**: User submits credentials to `/api/token/` endpoint
2. **Token Generation**: Server validates credentials and returns access + refresh tokens
3. **API Requests**: Client includes access token in Authorization header: `Bearer <token>`
4. **Token Refresh**: When access token expires, client uses refresh token to get new access token
5. **Logout**: Client discards tokens (server-side token blacklisting can be enabled)

### Custom Token Serializer
Location: `auth/users/serializers.py`

The system uses `CustomTokenObtainPairSerializer` that extends `TokenObtainPairSerializer` to include custom claims:
- User ID
- Username
- Email
- User roles and permissions
- System access information

### Password Security
- **Hashing Algorithm**: Argon2 (via `argon2-cffi>=23.1.0`)
- **Configuration**:
  ```python
  PASSWORD_HASHERS = [
      'django.contrib.auth.hashers.Argon2PasswordHasher',
      'django.contrib.auth.hashers.PBKDF2PasswordHasher',
  ]
  ```
- **Password Requirements**:
  - Minimum length: 8 characters
  - Complexity requirements enforced via Django validators
  - Password history to prevent reuse

### Multi-Factor Authentication (MFA)
- **Current**: Not implemented
- **Planned**: TOTP-based 2FA for admin accounts

## Authorization Rules

### Role-Based Access Control (RBAC)
The system implements RBAC through Django REST Framework's permission classes.

#### User Roles
Defined in `auth/roles/models.py`:
- **SuperUser**: Full system access (Django superuser)
- **Admin**: System-level administrative access
- **Manager**: Team/department management capabilities
- **Agent**: Ticket handling and resolution
- **User**: Basic ticket creation and viewing

#### System-Specific Roles
Users can have different roles in different systems (TTS, HDTS, etc.) via the `UserSystemRole` model:
```python
class UserSystemRole:
    user: User
    system: System
    role: Role
```

### Permission Classes
Location: `auth/permissions.py`

**Built-in Permissions**:
- `IsAuthenticated`: Requires valid JWT token
- `AllowAny`: No authentication required
- `IsAdminUser`: Requires Django staff status

**Custom Permissions**:
- `IsSystemAdminOrSuperUser`: Allows superusers and system admins
- `IsSystemAdminOrSuperUserForSystem`: System-specific admin check
- `filter_queryset_by_system_access`: Filters data based on user's system access

**Example Usage**:
```python
class UserSystemRoleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSystemAdminOrSuperUser]
```

### API Endpoint Security
Each API endpoint defines appropriate permission classes:

| Endpoint Pattern | Permission | Description |
|-----------------|------------|-------------|
| `/api/token/` | AllowAny | Login endpoint |
| `/api/token/refresh/` | AllowAny | Token refresh |
| `/api/users/` | IsAuthenticated | User management |
| `/api/tickets/` | IsAuthenticated | Ticket operations |
| `/api/workflows/` | IsAuthenticated | Workflow management |
| `/api/admin/*` | IsSystemAdminOrSuperUser | Admin operations |

### Row-Level Security
Implemented via queryset filtering in viewsets:
```python
def get_queryset(self):
    queryset = super().get_queryset()
    return filter_queryset_by_system_access(
        queryset, 
        self.request.user, 
        'system_field_name'
    )
```

## Data Encryption

### Data in Transit (TLS/HTTPS)

#### Development Environment
- **Protocol**: HTTP (unencrypted)
- **Reason**: Local development convenience
- **Security**: Not exposed to internet

#### Production Environment
- **Protocol**: HTTPS (TLS 1.3)
- **Certificate Provider**: Railway (automatic SSL/TLS certificate provisioning)
- **Cipher Suites**: Modern, secure cipher suites only
- **HSTS**: HTTP Strict Transport Security enabled
- **Configuration**:
  ```python
  SECURE_SSL_REDIRECT = True
  SECURE_HSTS_SECONDS = 31536000  # 1 year
  SECURE_HSTS_INCLUDE_SUBDOMAINS = True
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  ```

### Data at Rest

#### Database Encryption
- **Development**: Not encrypted (local PostgreSQL)
- **Production**: Railway provides:
  - Encrypted database volumes
  - Encrypted automated backups
  - Encryption key management

#### File Storage Encryption
- **Media Files**: Ticket attachments stored in shared Docker volume
- **Production**: Use cloud storage (S3) with server-side encryption (SSE-S3 or SSE-KMS)
- **Planned**: Client-side encryption for sensitive documents

#### Sensitive Configuration
- **Environment Variables**: Never committed to Git
- **Secret Management**:
  - Development: `.env` files (in `.gitignore`)
  - Production: Railway environment variables
  - Future: Integrate with secrets manager (AWS Secrets Manager, HashiCorp Vault)

### Field-Level Encryption
**Current**: Not implemented

**Planned**: Encrypt sensitive fields using `django-encrypted-model-fields`:
- Personal Identifiable Information (PII)
- Payment information (if applicable)
- Confidential ticket content

## API Security Protocols

### Rate Limiting
Location: `RATE_LIMITING_IMPLEMENTATION.md`

Implemented using Django middleware to prevent abuse:
- **Anonymous Users**: 100 requests/hour
- **Authenticated Users**: 1000 requests/hour
- **Admin Users**: 5000 requests/hour

**Configuration**:
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

### CORS (Cross-Origin Resource Sharing)
**Library**: `django-cors-headers==4.7.0`

**Configuration**:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:1000",  # Frontend dev
    "https://yourdomain.com",  # Production
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'x-csrftoken',
]
```

### CSRF Protection
- **Enabled**: For session-based views
- **Exempt**: JWT-authenticated API endpoints
- **Token**: Generated and validated for form submissions

### API Key Authentication
**Library**: `djangorestframework-api-key`

Used for service-to-service communication:
```python
# Notification Service
NOTIFICATION_API_KEYS = "demo-api-key-123,test-api-key-456"
```

### Input Validation and Sanitization

#### Django REST Framework Serializers
All API inputs are validated through serializers:
```python
class TicketSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    
    def validate_title(self, value):
        # Custom validation logic
        if len(value) < 5:
            raise serializers.ValidationError("Title too short")
        return value
```

#### XSS Protection
- **Django Template Engine**: Auto-escapes output
- **Frontend**: React's XSS protection via JSX
- **HTML Sanitization**: `dompurify` library in frontend

#### SQL Injection Prevention
- **ORM**: Django ORM parameterizes all queries
- **Raw Queries**: Avoided; if necessary, parameterized

#### File Upload Security
- **Validation**: File type and size validation
- **Storage**: Isolated from web root
- **Virus Scanning**: Planned integration with ClamAV

### Security Headers
Configured in Django middleware:

```python
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### Logging and Monitoring

#### Security Event Logging
**Logged Events**:
- Failed login attempts
- Unauthorized access attempts
- Permission changes
- Admin actions
- Suspicious activity patterns

**Log Storage**:
- Development: Console output
- Production: Railway logs + external logging service (Sentry, LogDNA)

#### Audit Trail
Location: `workflow_api/test_audit_logging.py`

The system maintains an audit log for:
- Ticket creation, updates, deletion
- Workflow changes
- User permission changes
- System configuration changes

**Implementation**:
```python
AuditLog.objects.create(
    user=request.user,
    action='UPDATE',
    model='Ticket',
    object_id=ticket.id,
    changes=json.dumps(changes)
)
```

## Service-to-Service Security

### Internal Service Communication
- **Authentication**: API keys or shared JWT secret
- **Network Isolation**: Docker network (services not exposed to host)
- **Mutual TLS**: Planned for production

### Message Queue Security
**RabbitMQ**:
- **Authentication**: Username/password (admin/admin in dev)
- **Production**: Strong credentials stored in environment variables
- **Encryption**: TLS for connections in production
- **Access Control**: Queue-level permissions

## Vulnerability Management

### Dependency Scanning
- **GitHub Dependabot**: Automated vulnerability scanning
- **Manual Review**: Regular `pip-audit` and `npm audit` checks

### Security Updates
- **Policy**: Security patches applied within 48 hours of disclosure
- **Testing**: Automated tests run before deployment
- **Rollback Plan**: Automated rollback if health checks fail

### Penetration Testing
- **Frequency**: Annually or after major releases
- **Scope**: Web application, API endpoints, authentication flows
- **Remediation**: Critical issues fixed immediately, others prioritized

## Compliance and Best Practices

### OWASP Top 10 Coverage
| Risk | Mitigation |
|------|------------|
| Broken Access Control | RBAC, permission classes, queryset filtering |
| Cryptographic Failures | TLS, Argon2 passwords, encrypted storage |
| Injection | ORM parameterization, input validation |
| Insecure Design | Security by design, threat modeling |
| Security Misconfiguration | Environment-based config, secure defaults |
| Vulnerable Components | Dependency scanning, regular updates |
| Authentication Failures | JWT, strong passwords, rate limiting |
| Software and Data Integrity | Code signing, checksum verification |
| Security Logging Failures | Comprehensive audit logging |
| SSRF | Input validation, URL whitelisting |

### Future Security Enhancements
- [ ] Implement Web Application Firewall (WAF)
- [ ] Add intrusion detection system (IDS)
- [ ] Implement security information and event management (SIEM)
- [ ] Add honeypots for threat intelligence
- [ ] Implement certificate pinning for mobile apps
- [ ] Add biometric authentication options
- [ ] Implement blockchain for immutable audit logs
