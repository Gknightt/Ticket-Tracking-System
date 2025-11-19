# A.5 Network Configuration

## Overview

This document describes the network design, connectivity, traffic flow, security configurations, and protocols used in the Ticket Tracking System deployment architecture.

## Network Architecture

### Deployment Network Topology

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Internet / Public Network                      │
│                                   ▲                                     │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │
                         HTTPS (443) / HTTP (80)
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│                     Load Balancer / Reverse Proxy                       │
│                           (Nginx / Traefik)                             │
│                         TLS/SSL Termination                             │
└──────┬─────────────────────┬──────────────────────┬────────────────────┘
       │                     │                      │
       │ HTTP :8000          │ HTTP :8002          │ HTTP :8004
       │                     │                      │
┌──────▼──────────┐   ┌──────▼──────────┐   ┌──────▼──────────┐
│  Auth Service   │   │  Workflow API   │   │ Ticket Service  │
│   Container     │   │   Container     │   │   Container     │
│   :8000         │   │   :8000         │   │   :7000         │
└──────┬──────────┘   └──────┬──────────┘   └──────┬──────────┘
       │                     │                      │
       └──────────┬──────────┴──────────┬───────────┘
                  │                     │
          ┌───────▼─────────┐   ┌───────▼───────────┐
          │   PostgreSQL    │   │    RabbitMQ       │
          │   Container     │   │   Container       │
          │   :5432         │   │   :5672 (AMQP)    │
          │                 │   │   :15672 (Mgmt)   │
          └─────────────────┘   └───────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                       Docker Bridge Network                             │
│                     Name: ticket-tracking-network                       │
│                     Subnet: 172.18.0.0/16                              │
└────────────────────────────────────────────────────────────────────────┘
```

### Docker Network Configuration

**Network Mode**: Bridge (default)

**Network Name**: `ticket-tracking-network` (auto-created by Docker Compose)

**Subnet**: Automatically assigned by Docker (typically 172.x.0.0/16)

**DNS**: Docker's embedded DNS server

**Service Discovery**: Services resolve each other by container/service name

```yaml
# Docker Compose network configuration
networks:
  default:
    name: ticket-tracking-network
    driver: bridge
```

## IP Address Scheme

### Container IP Assignment

Docker automatically assigns IP addresses from the subnet. Services communicate using:

1. **Service Names** (preferred): `http://auth-service:8000`
2. **Container Names**: `http://auth-service-container:8000`
3. **IP Addresses** (not recommended): `http://172.18.0.5:8000`

### Port Mapping

**Format**: `<host_port>:<container_port>`

| Service | Container Port | Host Port | Exposed To |
|---------|---------------|-----------|------------|
| Frontend | 1000 | 1000 | Public (via reverse proxy) |
| Auth Service | 8000 | 8003 | Internal + Load balancer |
| Workflow API | 8000 | 8002 | Internal + Load balancer |
| Ticket Service | 7000 | 8004 | Internal + Load balancer |
| Messaging Service | 8001 | 8005 | Internal + Load balancer |
| Notification Service | 8001 | 8006 | Internal |
| PostgreSQL | 5432 | 5433 | Internal only |
| RabbitMQ AMQP | 5672 | 5672 | Internal only |
| RabbitMQ Management | 15672 | 15672 | Internal/Dev only |

### Network Segregation

**Public Network**:
- Frontend (port 1000)
- Reverse proxy (ports 80, 443)

**Application Network** (Docker bridge):
- All backend services
- Inter-service communication
- Database access
- Message queue access

**Database Network** (isolated):
- PostgreSQL accessible only to application containers
- No direct external access

## Communication Protocols

### HTTP/HTTPS

**Frontend ↔ Backend**:
```
Protocol: HTTP/1.1 (development), HTTPS (production)
Format: JSON (application/json)
Authentication: JWT Bearer tokens
Headers:
  - Authorization: Bearer <token>
  - Content-Type: application/json
  - Accept: application/json
```

**Example Request**:
```http
POST /tickets/ HTTP/1.1
Host: ticket-service:8004
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "subject": "Login issue",
  "category": "Technical Support",
  "priority": "high"
}
```

**Example Response**:
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": 123,
  "ticket_id": "TKT-2025-001",
  "subject": "Login issue",
  "status": "open"
}
```

### AMQP (Advanced Message Queuing Protocol)

**Protocol Version**: AMQP 0-9-1

**Broker**: RabbitMQ

**Connection String**: `amqp://admin:admin@rabbitmq:5672/`

**Message Format**: JSON (Celery serialization)

**Queues**:
- `TICKET_TASKS_PRODUCTION` - Ticket processing tasks
- `notification-queue-default` - Email/push notifications
- `inapp-notification-queue` - In-app notifications
- `ticket_status-default` - Status update tasks
- `role_send-default` - Role management tasks

**Exchange Types**:
- **Direct Exchange**: Default for task routing
- **Topic Exchange**: For pub/sub patterns (future)

**Message Properties**:
```python
{
    'content_type': 'application/json',
    'content_encoding': 'utf-8',
    'delivery_mode': 2,  # Persistent
    'priority': 0,
    'correlation_id': '<uuid>',
    'reply_to': '<queue_name>',
}
```

### PostgreSQL Protocol

**Protocol**: PostgreSQL Wire Protocol

**Port**: 5432

**Connection String Format**:
```
postgres://username:password@host:port/database
```

**Connection Pooling**:
- Max connections: 100 (PostgreSQL config)
- Connection lifetime: 600s (Django config)
- Health checks: Enabled

**Example Connection** (from Django):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ticketmanagement',
        'USER': 'postgres',
        'PASSWORD': 'postgrespass',
        'HOST': 'db',  # Docker service name
        'PORT': '5432',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

### SSH (Secure Shell)

**Use Case**: Remote server management (production deployments)

**Port**: 22

**Access**: Limited to administrators

**Key-based Authentication**: Required (password auth disabled in production)

**Allowed Operations**:
- Deploy updates
- View logs
- Restart services
- Database backups

## Firewall Rules

### Docker Host Firewall (iptables)

**Incoming Rules**:

```bash
# Allow HTTP (for reverse proxy)
iptables -A INPUT -p tcp --dport 80 -j ACCEPT

# Allow HTTPS (for reverse proxy)
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow SSH (administrators only)
iptables -A INPUT -p tcp --dport 22 -s <admin_ip_range> -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Block all other incoming
iptables -A INPUT -j DROP
```

**Outgoing Rules**:

```bash
# Allow all outgoing (services can make external API calls)
iptables -A OUTPUT -j ACCEPT
```

### Container-Level Network Policies

**Default Policy**: Containers can communicate within Docker network

**Isolation**: Database and RabbitMQ not exposed to host network

```yaml
# docker-compose.yml - No published ports for internal services
services:
  db:
    image: postgres:15
    # No 'ports' directive - only accessible within Docker network
    networks:
      - internal
  
  rabbitmq:
    image: rabbitmq:3-management
    # Only expose management UI in development
    ports:
      - "15672:15672"  # Management UI
    networks:
      - internal
```

### Cloud Provider Firewall (Production)

**AWS Security Groups** / **GCP Firewall Rules**:

| Rule Name | Type | Protocol | Port | Source | Description |
|-----------|------|----------|------|--------|-------------|
| allow-http | Inbound | TCP | 80 | 0.0.0.0/0 | HTTP from internet |
| allow-https | Inbound | TCP | 443 | 0.0.0.0/0 | HTTPS from internet |
| allow-ssh | Inbound | TCP | 22 | <admin_ips> | SSH for admins |
| allow-internal | Inbound | All | All | VPC subnet | Internal communication |
| allow-outbound | Outbound | All | All | 0.0.0.0/0 | Outbound traffic |

## Network Security

### TLS/SSL Configuration

**Production Requirements**:
- TLS 1.2 minimum (TLS 1.3 preferred)
- Valid SSL certificate (Let's Encrypt or commercial CA)
- HSTS (HTTP Strict Transport Security) enabled
- Certificate auto-renewal

**Nginx TLS Configuration** (reverse proxy):

```nginx
server {
    listen 443 ssl http2;
    server_name ticketsystem.example.com;
    
    # SSL certificate
    ssl_certificate /etc/letsencrypt/live/ticketsystem.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ticketsystem.example.com/privkey.pem;
    
    # SSL protocols and ciphers
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Proxy to backend services
    location /api/auth/ {
        proxy_pass http://auth-service:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name ticketsystem.example.com;
    return 301 https://$host$request_uri;
}
```

### CORS (Cross-Origin Resource Sharing)

**Configuration** (Django):

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    'https://ticketsystem.example.com',
    'https://admin.ticketsystem.example.com',
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

### Rate Limiting

**Implementation**: Multiple layers

1. **Nginx Rate Limiting**:
```nginx
# Limit requests per IP
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://backend;
    }
}
```

2. **Application Rate Limiting** (Django):
```python
# Auth service - login endpoint
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    # Login logic
    pass
```

3. **Database-backed Rate Limiting**:
```python
# Custom rate limiting in auth/rate_limiting.py
# Tracks failed login attempts per IP and device
# See A3 documentation for details
```

## Network Traffic Flow

### Request Flow: User Login

```
1. User Browser
   │
   ├─► HTTPS (443) ────► Nginx Reverse Proxy
                          │
                          ├─► TLS Termination
                          │
                          └─► HTTP (8000) ────► Auth Service Container
                                                  │
                                                  ├─► Rate Limit Check
                                                  ├─► PostgreSQL (5432)
                                                  └─► JWT Generation
                          
   Response ◄──────────────────────────────────────┘
```

### Request Flow: Ticket Creation

```
1. Frontend
   │
   ├─► POST /tickets/ (JWT in header)
   │
   └─► HTTP (8004) ────► Ticket Service Container
                          │
                          ├─► JWT Validation
                          ├─► PostgreSQL (5432) - Save ticket
                          │
                          └─► RabbitMQ (5672) ────► Enqueue workflow task
                                                     │
                                                     ▼
                                                   Workflow Worker
                                                     │
                                                     ├─► RabbitMQ (consume)
                                                     ├─► PostgreSQL (5432)
                                                     └─► HTTP (8000) ────► Auth Service
                                                                           (get users by role)
```

### Background Task Flow: Notification Delivery

```
Workflow API
   │
   ├─► Enqueue notification task
   │
   └─► RabbitMQ (5672)
        │
        └─► Queue: notification-queue-default
             │
             ▼
        Notification Worker (Celery)
             │
             ├─► Consume task
             ├─► SMTP (587) ────► External Email Server (Gmail, SendGrid)
             └─► HTTP (8000) ────► Auth Service (get user email)
```

## DNS Configuration

### Internal DNS (Docker)

**DNS Server**: Docker embedded DNS (127.0.0.11)

**Resolution**:
- Service names resolve to container IPs
- Container names resolve to container IPs
- Network aliases supported

**Example**:
```bash
# Inside a container
ping auth-service
# Resolves to: 172.18.0.5

nslookup auth-service
# Server: 127.0.0.11
# Address: 172.18.0.5
```

### External DNS (Production)

**Domain**: `ticketsystem.example.com`

**DNS Records**:

```
; A Records
ticketsystem.example.com.       300    IN    A       <server_ip>
www.ticketsystem.example.com.   300    IN    A       <server_ip>
api.ticketsystem.example.com.   300    IN    A       <server_ip>

; CNAME Records
admin.ticketsystem.example.com. 300    IN    CNAME   ticketsystem.example.com.

; MX Records (for email)
ticketsystem.example.com.       300    IN    MX      10 mail.ticketsystem.example.com.

; TXT Records (SPF, DKIM, etc.)
ticketsystem.example.com.       300    IN    TXT     "v=spf1 include:_spf.google.com ~all"
```

## Load Balancing

### Nginx Load Balancer Configuration

```nginx
upstream backend_auth {
    least_conn;  # Load balancing method
    server auth-service-1:8000 max_fails=3 fail_timeout=30s;
    server auth-service-2:8000 max_fails=3 fail_timeout=30s;
    server auth-service-3:8000 max_fails=3 fail_timeout=30s;
}

upstream backend_workflow {
    least_conn;
    server workflow-api-1:8000 max_fails=3 fail_timeout=30s;
    server workflow-api-2:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name api.ticketsystem.example.com;
    
    location /api/auth/ {
        proxy_pass http://backend_auth;
        proxy_next_upstream error timeout http_502 http_503 http_504;
        
        # Headers for proxying
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /api/workflow/ {
        proxy_pass http://backend_workflow;
        proxy_next_upstream error timeout http_502 http_503 http_504;
    }
}
```

### Health Checks

```nginx
upstream backend_auth {
    server auth-service-1:8000;
    server auth-service-2:8000;
    
    # Health check configuration
    check interval=3000 rise=2 fall=5 timeout=1000 type=http;
    check_http_send "GET /health/ HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx;
}
```

## Network Monitoring

### Metrics to Monitor

1. **Connection Metrics**:
   - Active connections per service
   - Connection pool utilization (database)
   - Failed connection attempts

2. **Latency Metrics**:
   - Request/response time
   - Database query time
   - Message queue latency

3. **Throughput Metrics**:
   - Requests per second (RPS)
   - Bytes transferred
   - Messages processed

4. **Error Metrics**:
   - HTTP error rates (4xx, 5xx)
   - Connection timeouts
   - Message delivery failures

### Monitoring Tools

**Docker Stats**:
```bash
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
```

**Network Traffic**:
```bash
# Monitor traffic on Docker network
docker network inspect ticket-tracking-network

# Monitor container network
docker exec <container> netstat -tuln
```

**RabbitMQ Management UI**:
- URL: `http://localhost:15672`
- View queue depths, message rates
- Monitor connections and channels

## Network Troubleshooting

### Common Issues & Solutions

**1. Service Cannot Reach Another Service**

```bash
# Check if services are on same network
docker network inspect ticket-tracking-network

# Test connectivity
docker exec auth-service ping ticket-service

# Check DNS resolution
docker exec auth-service nslookup ticket-service
```

**2. Port Already in Use**

```bash
# Find process using port
sudo lsof -i :8004

# Kill process or change port mapping in docker-compose.yml
```

**3. Database Connection Refused**

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs postgres_db

# Verify connection string
docker exec ticket-service env | grep DATABASE_URL
```

**4. RabbitMQ Connection Issues**

```bash
# Check RabbitMQ status
docker exec rabbitmq rabbitmqctl status

# View connections
docker exec rabbitmq rabbitmqctl list_connections

# Check queues
docker exec rabbitmq rabbitmqctl list_queues
```

## Security Best Practices

### Network Security Checklist

- [ ] TLS/SSL enabled for all external traffic
- [ ] Database not directly accessible from internet
- [ ] RabbitMQ management UI password-protected
- [ ] Firewall configured to block unnecessary ports
- [ ] Rate limiting enabled on all public endpoints
- [ ] CORS properly configured
- [ ] Security headers set (HSTS, X-Frame-Options, etc.)
- [ ] SSH key-based authentication only
- [ ] VPN required for administrative access (production)
- [ ] Regular security patches applied
- [ ] Network segmentation between environments (dev/staging/prod)

### Encryption in Transit

- **External Traffic**: TLS 1.2+ (HTTPS)
- **Internal Traffic**: HTTP within Docker network (trusted environment)
- **Database**: SSL optional (within Docker network)
- **Message Queue**: AMQP over TLS (production)

### Encryption at Rest

- **Database**: PostgreSQL encryption (optional, via LUKS/dm-crypt)
- **Volumes**: Docker volume encryption (host-level)
- **Backups**: Encrypted with GPG or cloud provider encryption

## References

- **System Architecture**: `/docs/A1_SYSTEM_ARCHITECTURE.md`
- **Docker Networking**: https://docs.docker.com/network/
- **Nginx Documentation**: https://nginx.org/en/docs/
- **PostgreSQL Network Security**: https://www.postgresql.org/docs/current/ssl-tcp.html
- **RabbitMQ Networking**: https://www.rabbitmq.com/networking.html

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Authors**: Network Infrastructure Team
