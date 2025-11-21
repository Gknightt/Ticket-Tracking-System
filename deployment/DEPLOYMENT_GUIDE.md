# Production Deployment Guide for DigitalOcean

Complete guide for deploying the Ticket Tracking System to DigitalOcean with Traefik reverse proxy and automatic SSL certificates via Let's Encrypt.

## 🏗️ Architecture Overview

```
Internet (HTTPS)
    ↓
Traefik Reverse Proxy (Port 80/443)
    ↓
├── mapactive.tech              → Frontend (React)
├── auth.mapactive.tech         → Auth Service
├── workflow.mapactive.tech     → Workflow API
├── ticket.mapactive.tech       → Ticket Service
├── messaging.mapactive.tech    → Messaging Service
├── notification.mapactive.tech → Notification Service
├── rabbitmq.mapactive.tech     → RabbitMQ Management UI
└── traefik.mapactive.tech      → Traefik Dashboard
    ↓
Internal Network
    ├── PostgreSQL (Internal only)
    ├── RabbitMQ (AMQP - Internal)
    └── Celery Workers (Internal)
```

## 📋 Prerequisites

### DigitalOcean Requirements
- Droplet with at least 4GB RAM (recommended: 8GB)
- Ubuntu 22.04 LTS
- Root or sudo access
- Public IP address

### Domain & DNS Requirements
- Domain: `mapactive.tech`
- Cloudflare account with domain added
- DNS records configured (see below)

### Cloudflare Setup
1. Add your domain to Cloudflare
2. Update nameservers at your registrar
3. Create API Token:
   - Go to: Profile → API Tokens → Create Token
   - Use template: "Edit zone DNS"
   - Permissions: `Zone:DNS:Edit`
   - Zone Resources: `Include → Specific zone → mapactive.tech`
   - Copy the token (you'll need it later)

## 🌐 DNS Configuration

Add the following A records in Cloudflare (replace `YOUR_SERVER_IP` with your DigitalOcean droplet IP):

| Type | Name         | Content         | Proxy Status | TTL  |
|------|--------------|-----------------|--------------|------|
| A    | @            | YOUR_SERVER_IP  | DNS only     | Auto |
| A    | www          | YOUR_SERVER_IP  | DNS only     | Auto |
| A    | auth         | YOUR_SERVER_IP  | DNS only     | Auto |
| A    | workflow     | YOUR_SERVER_IP  | DNS only     | Auto |
| A    | ticket       | YOUR_SERVER_IP  | DNS only     | Auto |
| A    | messaging    | YOUR_SERVER_IP  | DNS only     | Auto |
| A    | notification | YOUR_SERVER_IP  | DNS only     | Auto |
| A    | rabbitmq     | YOUR_SERVER_IP  | DNS only     | Auto |
| A    | traefik      | YOUR_SERVER_IP  | DNS only     | Auto |

**Important:** Set Proxy status to "DNS only" (grey cloud) during initial setup to allow Let's Encrypt to verify domain ownership.

## 🚀 Quick Start Deployment

### Step 1: Connect to Your Server

```bash
ssh root@YOUR_SERVER_IP
```

### Step 2: Download and Run Deployment Script

```bash
# Download the repository
git clone https://github.com/Gknightt/Ticket-Tracking-System.git
cd Ticket-Tracking-System/deployment

# Make scripts executable
chmod +x scripts/*.sh

# Run the deployment script
sudo ./scripts/deploy.sh
```

### Step 3: Configure Environment Variables

The script will create a `.env` file from the example. Edit it with your actual values:

```bash
nano .env
```

**Required Changes:**

1. **Cloudflare Credentials:**
   ```env
   CF_API_EMAIL=your-cloudflare-email@example.com
   CF_DNS_API_TOKEN=your-cloudflare-api-token
   ```

2. **Database Password:**
   ```env
   POSTGRES_USER=ticketapp_user
   POSTGRES_PASSWORD=CHANGE_THIS_STRONG_PASSWORD
   ```

3. **RabbitMQ Password:**
   ```env
   RABBITMQ_USER=ticketapp_rabbitmq
   RABBITMQ_PASSWORD=CHANGE_THIS_STRONG_PASSWORD
   ```

4. **JWT & Secret Keys** (generate with: `python -c "import secrets; print(secrets.token_urlsafe(50))"`):
   ```env
   JWT_SIGNING_KEY=your-random-jwt-key
   AUTH_SECRET_KEY=your-random-auth-key
   WORKFLOW_SECRET_KEY=your-random-workflow-key
   TICKET_SECRET_KEY=your-random-ticket-key
   MESSAGING_SECRET_KEY=your-random-messaging-key
   NOTIFICATION_SECRET_KEY=your-random-notification-key
   ```

5. **Email Configuration** (for Gmail, use App Password):
   ```env
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   DEFAULT_FROM_EMAIL=noreply@mapactive.tech
   ```

6. **Traefik Dashboard Password** (generate with: `htpasswd -nb admin password`):
   ```env
   TRAEFIK_DASHBOARD_USER=admin
   TRAEFIK_DASHBOARD_PASSWORD=$$apr1$$...hashed...
   ```

### Step 4: Setup SSL Certificates

```bash
./scripts/setup-ssl.sh
```

This script will:
- Verify Cloudflare credentials
- Check DNS configuration
- Configure Traefik for Let's Encrypt
- Prepare certificate storage

### Step 5: Start Services

The deploy script will automatically:
- Pull and build Docker images
- Start all services
- Run database migrations
- Prompt to create a superuser

### Step 6: Verify Deployment

Check service status:
```bash
docker-compose -f docker-compose.production.yml ps
```

View logs:
```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f traefik
docker-compose -f docker-compose.production.yml logs -f auth-service
```

Check SSL certificate status:
```bash
docker-compose -f docker-compose.production.yml logs traefik | grep acme
```

## 🔧 Manual Deployment Steps

If you prefer to deploy manually:

### 1. Install Docker & Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 2. Clone Repository

```bash
git clone https://github.com/Gknightt/Ticket-Tracking-System.git
cd Ticket-Tracking-System/deployment
```

### 3. Configure Environment

```bash
cp .env.production.example .env
nano .env  # Edit with your values
```

### 4. Setup SSL Storage

```bash
touch traefik/acme.json
chmod 600 traefik/acme.json
```

### 5. Create Docker Network

```bash
docker network create traefik-public
```

### 6. Build and Start Services

```bash
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
```

### 7. Run Migrations

```bash
docker-compose -f docker-compose.production.yml exec auth-service python manage.py migrate
docker-compose -f docker-compose.production.yml exec workflow-api python manage.py migrate
docker-compose -f docker-compose.production.yml exec ticket-service python manage.py migrate
docker-compose -f docker-compose.production.yml exec messaging-service python manage.py migrate
docker-compose -f docker-compose.production.yml exec notification-service python manage.py migrate
```

### 8. Create Superuser

```bash
docker-compose -f docker-compose.production.yml exec auth-service python manage.py createsuperuser
```

## 📊 Service Management

### Start Services
```bash
docker-compose -f docker-compose.production.yml up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.production.yml down
```

### Restart a Service
```bash
docker-compose -f docker-compose.production.yml restart auth-service
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f [service-name]

# Last 100 lines
docker-compose -f docker-compose.production.yml logs --tail=100 [service-name]
```

### Scale Services
```bash
docker-compose -f docker-compose.production.yml up -d --scale workflow-worker=3
```

### Update Services
```bash
git pull
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
```

## 🔒 Security Considerations

### Firewall Configuration

```bash
# Install UFW
apt-get install ufw

# Allow SSH
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable
```

### SSL/TLS Settings

The deployment uses:
- Automatic HTTPS redirect
- TLS 1.2+ only
- Strong cipher suites
- HSTS headers
- Secure cookie settings

### Environment Security

1. **Never commit `.env` files** - they contain secrets
2. **Use strong passwords** - minimum 20 characters
3. **Rotate secrets regularly** - especially JWT keys
4. **Limit SSH access** - use SSH keys, disable password auth
5. **Keep system updated** - `apt-get update && apt-get upgrade`

## 🐛 Troubleshooting

### SSL Certificate Issues

**Problem:** Certificates not issued

**Solutions:**
```bash
# Check Traefik logs
docker-compose -f docker-compose.production.yml logs traefik | grep -i error

# Verify DNS propagation
nslookup auth.mapactive.tech

# Check Cloudflare API token
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
     -H "Authorization: Bearer YOUR_CF_DNS_API_TOKEN"

# Clear acme.json and retry
docker-compose -f docker-compose.production.yml down
rm traefik/acme.json
touch traefik/acme.json
chmod 600 traefik/acme.json
docker-compose -f docker-compose.production.yml up -d
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.production.yml ps postgres

# View database logs
docker-compose -f docker-compose.production.yml logs postgres

# Connect to database
docker-compose -f docker-compose.production.yml exec postgres psql -U ticketapp_user -d auth_db
```

### Service Won't Start

```bash
# Check service logs
docker-compose -f docker-compose.production.yml logs [service-name]

# Check if port is already in use
netstat -tulpn | grep [port-number]

# Rebuild service
docker-compose -f docker-compose.production.yml build --no-cache [service-name]
docker-compose -f docker-compose.production.yml up -d [service-name]
```

### CORS Errors

Verify environment variables in `.env`:
```env
DJANGO_CORS_ALLOWED_ORIGINS=https://mapactive.tech,https://auth.mapactive.tech,...
DJANGO_CSRF_TRUSTED_ORIGINS=https://mapactive.tech,https://auth.mapactive.tech,...
COOKIE_DOMAIN=.mapactive.tech
```

### RabbitMQ Connection Issues

```bash
# Check RabbitMQ logs
docker-compose -f docker-compose.production.yml logs rabbitmq

# Access RabbitMQ management UI
# Open: https://rabbitmq.mapactive.tech
# Login with credentials from .env

# Check queue status
docker-compose -f docker-compose.production.yml exec rabbitmq rabbitmqctl list_queues
```

## 📈 Monitoring & Maintenance

### Health Checks

```bash
# Check all services
docker-compose -f docker-compose.production.yml ps

# Check specific service health
docker inspect --format='{{.State.Health.Status}}' [container-name]
```

### Backup Database

```bash
# Backup all databases
docker-compose -f docker-compose.production.yml exec postgres pg_dumpall -U ticketapp_user > backup_$(date +%Y%m%d).sql

# Backup specific database
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U ticketapp_user auth_db > auth_backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
# Restore from backup
docker-compose -f docker-compose.production.yml exec -T postgres psql -U ticketapp_user < backup_20240101.sql
```

### Log Rotation

Configure log rotation in `/etc/docker/daemon.json`:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Then restart Docker:
```bash
systemctl restart docker
```

## 🔄 Updating the Application

### Standard Update Process

```bash
cd /opt/ticket-tracking-system/deployment

# Pull latest changes
git pull

# Rebuild services
docker-compose -f docker-compose.production.yml build

# Stop services
docker-compose -f docker-compose.production.yml down

# Start with new images
docker-compose -f docker-compose.production.yml up -d

# Run migrations
docker-compose -f docker-compose.production.yml exec auth-service python manage.py migrate
docker-compose -f docker-compose.production.yml exec workflow-api python manage.py migrate
docker-compose -f docker-compose.production.yml exec ticket-service python manage.py migrate
docker-compose -f docker-compose.production.yml exec messaging-service python manage.py migrate
docker-compose -f docker-compose.production.yml exec notification-service python manage.py migrate
```

### Zero-Downtime Updates

For critical services, use rolling updates:
```bash
# Update one service at a time
docker-compose -f docker-compose.production.yml up -d --no-deps --build auth-service
docker-compose -f docker-compose.production.yml up -d --no-deps --build workflow-api
# ... etc
```

## 📞 Support

- **Repository:** https://github.com/Gknightt/Ticket-Tracking-System
- **Issues:** Create an issue on GitHub
- **Documentation:** See `/documentation` folder

## 📝 Additional Resources

- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Cloudflare API Documentation](https://developers.cloudflare.com/api/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)

## 🔐 Security Checklist

- [ ] Strong passwords set for all services
- [ ] JWT signing keys are random and secure
- [ ] Cloudflare API token has minimum required permissions
- [ ] SSH key-based authentication configured
- [ ] Firewall (UFW) enabled and configured
- [ ] Regular backups scheduled
- [ ] SSL certificates auto-renew (check every 60 days)
- [ ] Traefik dashboard protected with basic auth
- [ ] Database exposed only to internal network
- [ ] Environment variables never committed to git
- [ ] CORS configured for production domains only
- [ ] Django DEBUG mode disabled in production
- [ ] Secure cookies enabled (HTTPS only)

## 📊 Performance Optimization

### Resource Limits

Add resource limits in `docker-compose.production.yml`:
```yaml
services:
  auth-service:
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Database Optimization

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.production.yml exec postgres psql -U ticketapp_user

# Check database size
\l+

# Check table sizes
\dt+

# Vacuum and analyze
VACUUM ANALYZE;
```

### Cache Configuration

Consider adding Redis for caching:
```yaml
redis:
  image: redis:alpine
  restart: unless-stopped
  volumes:
    - redis_data:/data
```

## 🎯 Production Checklist

Before going live:

- [ ] DNS records configured and propagated
- [ ] SSL certificates issued successfully
- [ ] All services running and healthy
- [ ] Database migrations completed
- [ ] Superuser created
- [ ] Email sending tested
- [ ] CORS configuration verified
- [ ] File uploads tested
- [ ] Background tasks working (check Celery logs)
- [ ] RabbitMQ queues processing messages
- [ ] Frontend can communicate with all services
- [ ] API endpoints responding correctly
- [ ] Monitoring/logging configured
- [ ] Backup strategy implemented
- [ ] Security checklist completed
- [ ] Load testing performed (optional but recommended)

---

**Deployment Date:** _____________  
**Deployed By:** _____________  
**Server IP:** _____________  
**Domain:** mapactive.tech
