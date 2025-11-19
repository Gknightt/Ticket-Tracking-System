# A.6 Deployment and Infrastructure

## Overview
The Ticket Tracking System is deployed using a containerized microservices architecture with Docker Compose for local/development environments and Railway for production deployments. GitHub Actions automates the CI/CD pipeline.

## Deployment Strategy

### Development Environment
- **Method**: Docker Compose
- **Location**: Local development machines
- **Access**: `http://localhost:<port>` for each service
- **Database**: PostgreSQL running in Docker container
- **Message Queue**: RabbitMQ running in Docker container

### Production Environment
- **Platform**: Railway (Cloud Platform)
- **Strategy**: Rolling deployment with zero-downtime updates
- **Database**: Managed PostgreSQL on Railway
- **Message Queue**: RabbitMQ (self-hosted or managed)
- **CDN/Proxy**: Railway's built-in load balancing and TLS termination

### Deployment Process
1. **Code Commit**: Developer pushes code to GitHub repository
2. **CI Pipeline**: GitHub Actions runs automated tests
3. **Build Phase**: Docker images are built for each microservice
4. **Deploy Phase**: Railway automatically deploys from connected GitHub branch
5. **Health Checks**: Railway monitors service health and rolls back if needed

## Infrastructure as Code

### Docker Compose Configuration
Location: `Docker/docker-compose.yml`

The system uses a single `docker-compose.yml` file that orchestrates all services:

#### Services Overview
| Service | Port | Container | Dependencies |
|---------|------|-----------|--------------|
| **RabbitMQ** | 5672 (AMQP), 15672 (UI) | rabbitmq | None |
| **PostgreSQL** | 5433 (host) → 5432 (container) | postgres_db | None |
| **Auth Service** | 8003 | auth-service | db, rabbitmq |
| **Ticket Service** | 8004 | ticket-service | db, rabbitmq |
| **Workflow API** | 8002 | workflow-api | db, rabbitmq, auth-service |
| **Messaging Service** | 8005 | messaging-service | db |
| **Notification Service** | 8006 | notification-service | db, rabbitmq |
| **Workflow Worker** | - | workflow-worker | db, rabbitmq, auth-service |
| **Notification Worker** | - | notification-worker | db, rabbitmq, notification-service |

#### Startup Sequence
Services start with coordinated delays to ensure dependencies are ready:
- **Immediate**: RabbitMQ, PostgreSQL (no sleep)
- **10 seconds**: Auth, Ticket, Workflow API, Messaging, Notification services
- **15-20 seconds**: Celery workers (workflow-worker, notification-worker)

### Dockerfiles
Each service has its own `Dockerfile` with best practices:

**Base Image**: `python:3.11-slim` (Auth, Ticket, Workflow, Messaging, Notification services)

**Key Features**:
- Multi-stage builds for optimized image size
- Non-root user execution for security
- Layer caching optimization
- Build-time dependency installation
- Runtime environment configuration

**Example Dockerfile Structure** (from `auth/Dockerfile`):
```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libpq-dev
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x /app/entrypoint.sh
EXPOSE 8000
CMD ["/app/entrypoint.sh"]
```

## Server Specifications

### Minimum Requirements (Development)
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 20 GB SSD
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows with WSL2

### Recommended Requirements (Production)
- **CPU**: 8+ cores (distributed across services)
- **RAM**: 16+ GB
- **Storage**: 50+ GB SSD with automatic backups
- **Network**: 100+ Mbps with low latency to database
- **Load Balancer**: Railway's built-in or external (e.g., Nginx)

### Service Resource Allocation (Production)
| Service | CPU | Memory | Scaling |
|---------|-----|--------|---------|
| Auth Service | 0.5 vCPU | 512 MB | Horizontal (2-4 instances) |
| Ticket Service | 1 vCPU | 1 GB | Horizontal (2-5 instances) |
| Workflow API | 1 vCPU | 1 GB | Horizontal (2-5 instances) |
| Workflow Worker | 1 vCPU | 1 GB | Horizontal (3-6 instances) |
| Notification Service | 0.5 vCPU | 512 MB | Horizontal (2-3 instances) |
| Notification Worker | 0.5 vCPU | 512 MB | Horizontal (2-4 instances) |
| Messaging Service | 0.5 vCPU | 512 MB | Horizontal (2-3 instances) |
| PostgreSQL | 2 vCPU | 4 GB | Vertical (managed service) |
| RabbitMQ | 1 vCPU | 2 GB | Vertical with clustering |

## Containerization Details

### Docker Networking
- **Network Mode**: Bridge (default)
- **Service Discovery**: Docker DNS resolution
- **Internal Communication**: Service names (e.g., `http://auth-service:8000`)
- **External Access**: Port mapping to host machine

### Volume Management
```yaml
volumes:
  rabbitmq_data:        # Persists RabbitMQ messages and configuration
  postgres_data:        # Persists database data
  media_files:          # Shared volume for ticket attachments
```

### Database Provisioning
The PostgreSQL container uses initialization scripts in `Docker/db-init/` to create separate logical databases:
- `authservice` - Auth service data
- `ticketmanagement` - Ticket service data
- `workflowmanagement` - Workflow API data
- `messagingservice` - Messaging service data
- `notificationservice` - Notification service data

## Environment Configuration

### Environment Variables
Each service reads from `.env` files in its directory (created from `.env.example`).

**Key Environment Variables**:
- `DJANGO_ENV`: `development` or `production`
- `DATABASE_URL`: PostgreSQL connection URI (preferred for Railway)
- `DJANGO_CELERY_BROKER_URL`: RabbitMQ connection string
- `DJANGO_AUTH_SERVICE`: URL for auth service
- `DJANGO_DEBUG`: Enable/disable debug mode
- `SECRET_KEY`: Django secret key for cryptographic signing
- `ALLOWED_HOSTS`: Comma-separated list of allowed hostnames
- `EMAIL_HOST`: SMTP server for email notifications
- `EMAIL_PORT`: SMTP port
- `EMAIL_USE_TLS`: Enable TLS for email

### Configuration Management
- **Development**: `.env` files in each service directory
- **Production**: Railway environment variables (UI or `railway.json`)
- **Secrets**: Stored in Railway environment variables (not in code)

## Deployment Scripts

### Initial Setup
```bash
# Location: Scripts/docker.sh
bash ./Scripts/docker.sh
```

This script:
1. Creates `.env` files from `.env.example` templates
2. Builds Docker images for all services
3. Starts containers with docker-compose
4. Runs database migrations
5. Seeds initial data (optional)

### Service Startup Scripts
Each service has an `entrypoint.sh` or `start.sh` script:

**Example** (`auth/entrypoint.sh`):
```bash
#!/bin/bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_systems --force
python manage.py seed_tts --force
python manage.py seed_accounts --force
python manage.py runserver 0.0.0.0:8000
```

## Monitoring and Health Checks

### Health Check Endpoints
Each service exposes a health check endpoint:
- Auth Service: `http://localhost:8003/api/health/`
- Ticket Service: `http://localhost:8004/api/health/`
- Workflow API: `http://localhost:8002/api/health/`

### Logging
- **Container Logs**: `docker logs <container_name>`
- **Service Logs**: Stored in container stdout/stderr
- **Production Logs**: Aggregated in Railway dashboard

### Monitoring Tools
- **RabbitMQ Management UI**: `http://localhost:15672` (admin/admin)
- **Database Admin**: PgAdmin or Railway dashboard
- **Container Stats**: `docker stats`

## Scaling Strategy

### Horizontal Scaling
- **Stateless Services**: Auth, Ticket, Workflow, Notification services can scale horizontally
- **Load Balancing**: Railway handles load balancing automatically
- **Session Management**: JWT tokens are stateless, enabling seamless scaling

### Vertical Scaling
- **Database**: Increase PostgreSQL instance size on Railway
- **Message Queue**: Upgrade RabbitMQ instance or enable clustering

## Disaster Recovery

### Backup Strategy
- **Database**: Automated daily backups via Railway
- **Media Files**: Cloud storage with versioning (S3 or equivalent)
- **Configuration**: Version controlled in Git repository

### Recovery Procedures
1. **Database Restoration**: Use Railway backup restoration
2. **Service Redeployment**: Redeploy from last known good commit
3. **Configuration Recovery**: Pull from Git repository

## Future Improvements
- Kubernetes deployment for advanced orchestration
- Service mesh (Istio) for improved observability
- Multi-region deployment for global availability
- Blue-Green deployment strategy for zero-downtime updates
