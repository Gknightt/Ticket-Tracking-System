# A.5 Network Configuration Documentation

## Table of Contents
1. [Network Overview](#network-overview)
2. [Network Topology](#network-topology)
3. [IP Address Scheme](#ip-address-scheme)
4. [Port Allocations](#port-allocations)
5. [Communication Protocols](#communication-protocols)
6. [Firewall Rules](#firewall-rules)
7. [Security Configuration](#security-configuration)
8. [Network Monitoring](#network-monitoring)

---

## Network Overview

The Ticket Tracking System operates on a microservices architecture using Docker networking in development and cloud-based networking in production.

**Network Design Principles**:
- Service isolation through Docker networks
- Internal service communication via Docker DNS
- Minimal external port exposure
- Secure inter-service communication
- Load balancing for production deployments

---

## Network Topology

### Development Environment (Docker Compose)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Host Machine                              │
│                      (localhost)                                 │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Docker Bridge Network                          │ │
│  │              (ticket-tracking-network)                      │ │
│  │                                                              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │
│  │  │ Auth Service │  │ Workflow API │  │  Messaging   │     │ │
│  │  │    :8000     │  │    :8000     │  │   :8001      │     │ │
│  │  │ Internal IP  │  │ Internal IP  │  │ Internal IP  │     │ │
│  │  └───────┬──────┘  └───────┬──────┘  └───────┬──────┘     │ │
│  │          │                  │                  │             │ │
│  │  ┌───────▼────────┬─────────▼────────┬─────────▼─────────┐ │ │
│  │  │    RabbitMQ    │    PostgreSQL    │   Notification    │ │ │
│  │  │   :5672,:15672 │      :5432       │      :8001        │ │ │
│  │  └────────────────┴──────────────────┴───────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│         │                  │                 │                   │
│    ┌────▼────┐        ┌────▼────┐      ┌────▼────┐             │
│    │Port 8003│        │Port 8002│      │Port 8005│             │
│    └─────────┘        └─────────┘      └─────────┘             │
└────────────────────────────────────────────────────────────────┘
         │                  │                 │
         └──────────────────┼─────────────────┘
                            │
                   ┌────────▼─────────┐
                   │  Frontend (React) │
                   │  Port 1000        │
                   └───────────────────┘
```

---

### Production Environment (Cloud Deployment)

```
                  ┌─────────────────────┐
                  │   Internet / Users   │
                  └──────────┬──────────┘
                             │ HTTPS (443)
                             │
                  ┌──────────▼──────────┐
                  │   Load Balancer     │
                  │   (NGINX/Cloud LB)  │
                  └──────────┬──────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
     ┌──────▼──────┐  ┌──────▼──────┐  ┌─────▼───────┐
     │Auth Service │  │Workflow API │  │ Messaging   │
     │  VPC:        │  │  VPC:        │  │  VPC:        │
     │10.0.1.0/24  │  │10.0.2.0/24  │  │10.0.3.0/24  │
     └──────┬──────┘  └──────┬──────┘  └─────┬───────┘
            │                │                │
            └────────────────┼────────────────┘
                             │
           ┌─────────────────┴─────────────────┐
           │                                   │
  ┌────────▼────────┐           ┌─────────────▼────────┐
  │  RabbitMQ       │           │  PostgreSQL          │
  │  (Managed)      │           │  (Managed DB)        │
  │  Private VPC    │           │  Private VPC         │
  └─────────────────┘           └──────────────────────┘
```

---

## IP Address Scheme

### Development (Docker Compose)

| Service | Internal IP | Host Port | Internal Port |
|---------|------------|-----------|---------------|
| Auth Service | Dynamic (Docker) | 8003 | 8000 |
| Workflow API | Dynamic (Docker) | 8002 | 8000 |
| Messaging Service | Dynamic (Docker) | 8005 | 8001 |
| Notification Service | Dynamic (Docker) | 8006 | 8001 |
| Ticket Service (Mock) | Dynamic (Docker) | 8004 | 7000 |
| PostgreSQL | Dynamic (Docker) | 5433 | 5432 |
| RabbitMQ | Dynamic (Docker) | 5672, 15672 | 5672, 15672 |
| Frontend | Dynamic (Docker) | 1000 | 1000 |

**Note**: Docker assigns dynamic IPs from the bridge network subnet (typically 172.x.x.x).  
Services communicate using service names (e.g., `http://auth-service:8000`).

---

### Production (Cloud / Railway)

**VPC Subnets**:
- Public Subnet: 10.0.0.0/24 (Load Balancer, NAT Gateway)
- Private Subnet 1: 10.0.1.0/24 (Auth, Notification services)
- Private Subnet 2: 10.0.2.0/24 (Workflow API, Messaging)
- Private Subnet 3: 10.0.3.0/24 (Ticket Service - Mock)
- Database Subnet: 10.0.10.0/24 (PostgreSQL, RabbitMQ)

**Public IPs**:
- Load Balancer: Elastic IP / Cloud Provider Assigned
- Outbound Traffic: NAT Gateway IP

**Private IPs**:
- Assigned dynamically within subnet ranges
- Service discovery via DNS (Kubernetes/Cloud Provider)

---

## Port Allocations

### External Ports (Exposed to Host/Internet)

| Port | Service | Protocol | Purpose | Access |
|------|---------|----------|---------|--------|
| 1000 | Frontend | HTTP/HTTPS | Web UI | Public |
| 8002 | Workflow API | HTTP | API Endpoints | Public (Auth required) |
| 8003 | Auth Service | HTTP | Authentication API | Public |
| 8004 | Ticket Service | HTTP | Mock HDTS API | Internal/Testing |
| 8005 | Messaging Service | HTTP/WS | WebSocket Comments | Public (Auth required) |
| 8006 | Notification Service | HTTP | Notification API | Internal |
| 5433 | PostgreSQL | TCP | Database | Internal (Dev only) |
| 5672 | RabbitMQ | AMQP | Message Broker | Internal |
| 15672 | RabbitMQ Management | HTTP | Admin UI | Internal (Dev only) |

---

### Internal Ports (Docker Network Only)

| Port | Service | Protocol | Purpose |
|------|---------|----------|---------|
| 8000 | Auth Service (internal) | HTTP | Service-to-service |
| 8000 | Workflow API (internal) | HTTP | Service-to-service |
| 8001 | Messaging Service (internal) | HTTP/WS | Service-to-service |
| 8001 | Notification Service (internal) | HTTP | Service-to-service |
| 7000 | Ticket Service (internal) | HTTP | Service-to-service |
| 5432 | PostgreSQL (internal) | TCP | Database connections |
| 5672 | RabbitMQ (internal) | AMQP | Message queue |

---

## Communication Protocols

### HTTP/HTTPS

**Protocol**: HTTP/1.1 (dev), HTTP/2 (production with HTTPS)  
**Port**: 80 (HTTP), 443 (HTTPS)  
**Usage**: RESTful API communication

**Request Headers**:
```
GET /api/v1/users/ HTTP/1.1
Host: auth-service:8000
Authorization: Bearer <jwt_token>
Content-Type: application/json
Accept: application/json
```

**Response Headers**:
```
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: http://localhost:1000
Access-Control-Allow-Credentials: true
```

---

### WebSocket (WS/WSS)

**Protocol**: WebSocket (RFC 6455)  
**Port**: Same as HTTP (8005 for messaging)  
**Upgrade**: HTTP → WebSocket

**Connection Handshake**:
```
GET /ws/comments/123/ HTTP/1.1
Host: messaging-service:8001
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: <key>
Sec-WebSocket-Version: 13
```

**Response**:
```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: <accept-key>
```

---

### AMQP (Advanced Message Queuing Protocol)

**Protocol**: AMQP 0-9-1  
**Port**: 5672  
**Broker**: RabbitMQ  
**Connection String**: `amqp://admin:admin@rabbitmq:5672/`

**Message Format**:
```python
{
  "task": "tickets.tasks.receive_ticket",
  "id": "uuid",
  "args": [],
  "kwargs": {"ticket_data": {...}},
  "retries": 0,
  "eta": null
}
```

---

### PostgreSQL Protocol

**Protocol**: PostgreSQL Wire Protocol  
**Port**: 5432  
**Connection**: TCP with SSL in production

**Connection String**:
```
postgres://user:password@host:port/database?sslmode=require
```

---

## Firewall Rules

### Development Environment

**No Firewall** (Docker networking handles isolation)

All services accessible on localhost:
- Inbound: Allow all from 127.0.0.1
- Outbound: Allow all

---

### Production Environment

#### Public Subnet (Load Balancer)

**Inbound Rules**:
| Source | Port | Protocol | Purpose | Action |
|--------|------|----------|---------|--------|
| 0.0.0.0/0 | 443 | TCP | HTTPS Traffic | ALLOW |
| 0.0.0.0/0 | 80 | TCP | HTTP (Redirect to HTTPS) | ALLOW |
| Admin IPs | 22 | TCP | SSH Access | ALLOW |
| All Other | * | * | Other Traffic | DENY |

**Outbound Rules**:
| Destination | Port | Protocol | Purpose | Action |
|-------------|------|----------|---------|--------|
| 10.0.0.0/16 | All | All | Internal VPC | ALLOW |
| 0.0.0.0/0 | 443 | TCP | External HTTPS | ALLOW |
| All Other | * | * | Other Traffic | DENY |

---

#### Private Subnet (Application Services)

**Inbound Rules**:
| Source | Port | Protocol | Purpose | Action |
|--------|------|----------|---------|--------|
| Load Balancer | 8000-8006 | TCP | API Traffic | ALLOW |
| 10.0.0.0/16 | All | All | Internal VPC | ALLOW |
| All Other | * | * | Other Traffic | DENY |

**Outbound Rules**:
| Destination | Port | Protocol | Purpose | Action |
|-------------|------|----------|---------|--------|
| 10.0.10.0/24 | 5432 | TCP | Database | ALLOW |
| 10.0.10.0/24 | 5672 | TCP | RabbitMQ | ALLOW |
| 0.0.0.0/0 | 443 | TCP | External APIs | ALLOW |
| All Other | * | * | Other Traffic | DENY |

---

#### Database Subnet

**Inbound Rules**:
| Source | Port | Protocol | Purpose | Action |
|--------|------|----------|---------|--------|
| 10.0.1.0/24 | 5432 | TCP | PostgreSQL from App | ALLOW |
| 10.0.2.0/24 | 5432 | TCP | PostgreSQL from App | ALLOW |
| 10.0.3.0/24 | 5432 | TCP | PostgreSQL from App | ALLOW |
| 10.0.1.0/24 | 5672 | TCP | RabbitMQ from App | ALLOW |
| 10.0.2.0/24 | 5672 | TCP | RabbitMQ from App | ALLOW |
| All Other | * | * | Other Traffic | DENY |

**Outbound Rules**:
| Destination | Port | Protocol | Purpose | Action |
|-------------|------|----------|---------|--------|
| 0.0.0.0/0 | All | All | Allow all (default for managed DB) | ALLOW |

---

## Security Configuration

### SSL/TLS Configuration

**Production Requirements**:
- TLS 1.2 or higher
- Strong cipher suites only
- HSTS (HTTP Strict Transport Security) enabled
- Certificate from trusted CA (Let's Encrypt / Cloud Provider)

**NGINX Configuration**:
```nginx
server {
    listen 443 ssl http2;
    server_name api.ticketing.com;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    location / {
        proxy_pass http://upstream_services;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
    }
}
```

---

### Network Segmentation

**Purpose**: Isolate services based on security requirements

**Segments**:
1. **Public Segment**: Load Balancer only
2. **Application Segment**: API services
3. **Data Segment**: Database, message broker
4. **Management Segment**: Admin tools, monitoring

**Traffic Flow**:
- Public → Load Balancer → Application Segment
- Application Segment ← → Data Segment
- Management Segment → All Segments (monitoring)

---

### DDoS Protection

**Measures**:
1. **Rate Limiting**: 
   - Per IP: 100 requests/minute
   - Per User: 1000 requests/minute
   
2. **Connection Limits**:
   - Max connections per IP: 10
   - Total concurrent connections: 1000

3. **Request Size Limits**:
   - Max request body: 10 MB
   - Max headers: 8 KB

4. **Cloud Provider DDoS Protection**:
   - AWS Shield / Cloudflare / Other CDN

---

### VPN Access (Optional)

**For**: Admin access to internal services

**Configuration**:
- WireGuard or OpenVPN
- MFA required
- Access logged
- Time-based access

---

## Network Monitoring

### Metrics to Monitor

1. **Network Traffic**:
   - Inbound/outbound bandwidth
   - Connection rate
   - Packet loss

2. **Service Availability**:
   - Health check response time
   - Service uptime
   - Failed connection attempts

3. **Security Events**:
   - Failed authentication attempts
   - Unusual traffic patterns
   - Blocked requests (firewall)

---

### Monitoring Tools

**Development**:
- Docker logs: `docker logs <container>`
- Docker stats: `docker stats`
- RabbitMQ Management UI: http://localhost:15672

**Production**:
- Prometheus + Grafana
- Cloud provider monitoring (CloudWatch / GCP Monitoring)
- Log aggregation (ELK Stack)
- APM (Application Performance Monitoring)

---

### Health Check Endpoints

**Purpose**: Monitor service availability

**Endpoints**:
- Auth Service: `GET /health/` → `{"status": "healthy"}`
- Workflow API: `GET /health/` → `{"status": "healthy", "db": "connected"}`
- Messaging: `GET /health/` → `{"status": "healthy"}`
- Notification: `GET /health/` → `{"status": "healthy"}`

**Health Check Frequency**: Every 30 seconds

**Health Check Criteria**:
- Service responds within 2 seconds
- Database connection active
- Message broker connection active

---

## Network Troubleshooting

### Common Issues

**1. Cannot Connect to Service**
```bash
# Check if container is running
docker ps | grep <service-name>

# Check container logs
docker logs <container-name>

# Check network connectivity
docker exec <container> ping <other-service>

# Check DNS resolution
docker exec <container> nslookup <service-name>
```

**2. Inter-Service Communication Failure**
```bash
# Verify both services on same network
docker network inspect ticket-tracking-network

# Test service URL
docker exec <container> curl http://<service-name>:<port>/health/
```

**3. RabbitMQ Connection Issues**
```bash
# Check RabbitMQ is running
docker ps | grep rabbitmq

# Check RabbitMQ logs
docker logs rabbitmq

# Verify connection from service
docker exec workflow-worker celery -A workflow_api inspect active
```

**4. Database Connection Issues**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test database connection
docker exec auth-service python manage.py dbshell

# Check DATABASE_URL environment variable
docker exec auth-service env | grep DATABASE
```

---

## Network Diagram Tools

**Used For Documentation**:
- PlantUML (text-based diagrams)
- Draw.io / Diagrams.net
- Lucidchart

**Example PlantUML**:
```plantuml
@startuml
cloud "Internet" as internet
node "Load Balancer" as lb
node "Auth Service" as auth
node "Workflow API" as workflow
database "PostgreSQL" as db
queue "RabbitMQ" as mq

internet --> lb
lb --> auth
lb --> workflow
auth --> db
workflow --> db
workflow --> mq
@enduml
```

---

## Appendix

### Port Mapping Reference

**Docker Compose Port Mapping Format**:
```yaml
ports:
  - "HOST_PORT:CONTAINER_PORT"
```

**Example**:
```yaml
auth-service:
  ports:
    - "8003:8000"  # Host port 8003 maps to container port 8000
```

---

### DNS Resolution

**Development (Docker)**:
- Service names resolve to container IPs
- Example: `http://auth-service:8000` resolves to `172.18.0.5:8000`

**Production (Kubernetes/Cloud)**:
- Service names resolve via cloud DNS
- Example: `http://auth-service.default.svc.cluster.local:8000`

---

### Network Security Checklist

- [ ] All external services use HTTPS
- [ ] Database not exposed to public internet
- [ ] RabbitMQ management UI protected
- [ ] Firewall rules configured
- [ ] SSL certificates valid and up-to-date
- [ ] Rate limiting enabled
- [ ] DDoS protection active
- [ ] VPN access configured for admins
- [ ] Security groups/firewall rules tested
- [ ] Monitoring and alerting configured

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Maintained By**: Network Infrastructure Team
