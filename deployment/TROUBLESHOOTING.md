# Troubleshooting Guide - Production Deployment

Complete troubleshooting guide for common issues in the production deployment.

## 🔍 Quick Diagnostics

### Run Health Check
```bash
cd /opt/ticket-tracking-system/deployment
./scripts/monitor.sh
```

### View All Logs
```bash
docker-compose -f docker-compose.production.yml logs -f
```

### Check Service Status
```bash
docker-compose -f docker-compose.production.yml ps
```

---

## 🚨 Common Issues & Solutions

### 1. SSL Certificates Not Issuing

**Symptoms:**
- Services accessible via HTTP but not HTTPS
- Browser shows "Connection not secure"
- Traefik logs show ACME errors

**Solutions:**

#### A. Check DNS Configuration
```bash
# Verify DNS records
nslookup auth.mapactive.tech
nslookup workflow.mapactive.tech
nslookup ticket.mapactive.tech

# All should point to your server IP
```

**Fix:** Add/update A records in Cloudflare DNS panel

#### B. Verify Cloudflare API Token
```bash
# Test API token
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
     -H "Authorization: Bearer YOUR_CF_DNS_API_TOKEN" \
     -H "Content-Type: application/json"

# Should return: "status": "active"
```

**Fix:** 
1. Go to Cloudflare → Profile → API Tokens
2. Create new token with "Edit zone DNS" template
3. Ensure it includes `Zone:DNS:Edit` permission
4. Update `CF_DNS_API_TOKEN` in `.env`

#### C. Check Traefik Logs
```bash
docker-compose -f docker-compose.production.yml logs traefik | grep -i acme
docker-compose -f docker-compose.production.yml logs traefik | grep -i error
```

**Common Errors:**

**"acme: error: 429"** - Rate limit exceeded
- Wait 1 hour before retrying
- Let's Encrypt has 5 failures per hour limit

**"DNS problem: NXDOMAIN"** - Domain doesn't resolve
- Check DNS propagation: `dig auth.mapactive.tech`
- Wait 5-10 minutes for DNS to propagate

**"Invalid credentials"** - Wrong API token
- Verify `CF_API_EMAIL` and `CF_DNS_API_TOKEN` in `.env`

#### D. Reset Certificates
```bash
# Stop services
docker-compose -f docker-compose.production.yml down

# Remove old certificates
rm traefik/acme.json

# Recreate with correct permissions
touch traefik/acme.json
chmod 600 traefik/acme.json

# Restart
docker-compose -f docker-compose.production.yml up -d

# Monitor logs
docker-compose -f docker-compose.production.yml logs -f traefik
```

#### E. Disable Cloudflare Proxy
In Cloudflare DNS settings:
- Click the orange cloud next to each A record
- Change to "DNS only" (grey cloud)
- Wait for certificates to be issued
- Can re-enable proxy after successful issuance

---

### 2. Service Won't Start

**Symptoms:**
- Container exits immediately
- Service shows as "Restarting" or "Exit 1"
- `docker-compose ps` shows unhealthy status

**Solutions:**

#### A. Check Service Logs
```bash
# View logs for specific service
docker-compose -f docker-compose.production.yml logs [service-name]

# Follow logs in real-time
docker-compose -f docker-compose.production.yml logs -f [service-name]

# Last 100 lines
docker-compose -f docker-compose.production.yml logs --tail=100 [service-name]
```

#### B. Common Startup Errors

**"django.db.utils.OperationalError: FATAL: database does not exist"**
```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.production.yml ps postgres

# Check if databases were created
docker-compose -f docker-compose.production.yml exec postgres psql -U ticketapp_user -l

# Manually create database if missing
docker-compose -f docker-compose.production.yml exec postgres psql -U ticketapp_user -c "CREATE DATABASE auth_db;"
```

**"ModuleNotFoundError: No module named 'xyz'"**
```bash
# Rebuild service without cache
docker-compose -f docker-compose.production.yml build --no-cache [service-name]

# Recreate container
docker-compose -f docker-compose.production.yml up -d --force-recreate [service-name]
```

**"Port is already allocated"**
```bash
# Find what's using the port
lsof -i :8000

# Kill the process or change port in docker-compose.yml
kill -9 [PID]
```

#### C. Environment Variable Issues
```bash
# Verify .env file is loaded
docker-compose -f docker-compose.production.yml config

# Check specific service environment
docker-compose -f docker-compose.production.yml exec [service-name] env
```

---

### 3. Database Connection Issues

**Symptoms:**
- Services can't connect to database
- "Connection refused" errors
- "Password authentication failed"

**Solutions:**

#### A. Verify PostgreSQL is Running
```bash
# Check status
docker-compose -f docker-compose.production.yml ps postgres

# Check logs
docker-compose -f docker-compose.production.yml logs postgres

# Test connection
docker-compose -f docker-compose.production.yml exec postgres pg_isready -U ticketapp_user
```

#### B. Test Database Connection
```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.production.yml exec postgres psql -U ticketapp_user -d auth_db

# List databases
\l

# List tables
\dt

# Exit
\q
```

#### C. Check Credentials
Verify in `.env`:
```env
POSTGRES_USER=ticketapp_user
POSTGRES_PASSWORD=your-password
```

Should match in service environment variables:
```env
DATABASE_URL=postgres://ticketapp_user:your-password@postgres:5432/auth_db
```

#### D. Reset Database Password
```bash
# Connect as postgres user
docker-compose -f docker-compose.production.yml exec postgres psql -U postgres

# Change password
ALTER USER ticketapp_user WITH PASSWORD 'new-password';

# Update .env file with new password
```

---

### 4. CORS / CSRF Errors

**Symptoms:**
- Frontend can't reach backend
- "CORS policy: No 'Access-Control-Allow-Origin' header"
- "CSRF verification failed"

**Solutions:**

#### A. Verify CORS Configuration
Check in `.env`:
```env
DJANGO_CORS_ALLOWED_ORIGINS=https://mapactive.tech,https://auth.mapactive.tech,https://workflow.mapactive.tech,https://ticket.mapactive.tech,https://messaging.mapactive.tech,https://notification.mapactive.tech
```

**Important:** 
- No trailing slashes
- Use HTTPS in production
- Include all subdomains

#### B. Verify CSRF Configuration
```env
DJANGO_CSRF_TRUSTED_ORIGINS=https://mapactive.tech,https://auth.mapactive.tech,https://workflow.mapactive.tech,https://ticket.mapactive.tech,https://messaging.mapactive.tech,https://notification.mapactive.tech
```

#### C. Check Cookie Domain
```env
COOKIE_DOMAIN=.mapactive.tech
```

Note the leading dot (`.`) - this allows cookies to work across subdomains.

#### D. Verify Cookie Security Settings
```env
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SESSION_COOKIE_SAMESITE=None
DJANGO_CSRF_COOKIE_SAMESITE=None
DJANGO_CORS_ALLOW_CREDENTIALS=True
```

#### E. Restart Services After Changes
```bash
docker-compose -f docker-compose.production.yml restart auth-service
docker-compose -f docker-compose.production.yml restart workflow-api
# ... etc for all services
```

---

### 5. RabbitMQ Connection Issues

**Symptoms:**
- Celery workers can't connect
- Tasks not processing
- "ConnectionResetError" in logs

**Solutions:**

#### A. Check RabbitMQ Status
```bash
# Check if running
docker-compose -f docker-compose.production.yml ps rabbitmq

# Check logs
docker-compose -f docker-compose.production.yml logs rabbitmq

# Check queues
docker-compose -f docker-compose.production.yml exec rabbitmq rabbitmqctl list_queues
```

#### B. Verify Credentials
In `.env`:
```env
RABBITMQ_USER=ticketapp_rabbitmq
RABBITMQ_PASSWORD=your-rabbitmq-password
```

Should match in Celery broker URL:
```env
CELERY_BROKER_URL=amqp://ticketapp_rabbitmq:your-rabbitmq-password@rabbitmq:5672/
```

#### C. Access RabbitMQ Management UI
- URL: https://rabbitmq.mapactive.tech
- Login with credentials from `.env`
- Check connections, channels, queues

#### D. Clear Stuck Messages
```bash
# Purge a specific queue
docker-compose -f docker-compose.production.yml exec rabbitmq rabbitmqctl purge_queue QUEUE_NAME

# Delete and recreate queue
docker-compose -f docker-compose.production.yml exec rabbitmq rabbitmqctl delete_queue QUEUE_NAME
```

---

### 6. Frontend Not Loading

**Symptoms:**
- Blank page
- 404 errors
- Assets not loading

**Solutions:**

#### A. Check Frontend Logs
```bash
docker-compose -f docker-compose.production.yml logs frontend
```

#### B. Verify Build Completed
```bash
# Rebuild frontend
docker-compose -f docker-compose.production.yml build --no-cache frontend

# Restart
docker-compose -f docker-compose.production.yml up -d frontend
```

#### C. Check API Endpoints
Frontend build uses these from `docker-compose.production.yml`:
```yaml
args:
  VITE_AUTH_URL: https://auth.mapactive.tech
  VITE_WORKFLOW_API: https://workflow.mapactive.tech/workflow
  VITE_BACKEND_API: https://workflow.mapactive.tech/
  # ... etc
```

#### D. Test Backend Connectivity
```bash
# From inside frontend container
docker-compose -f docker-compose.production.yml exec frontend sh
wget https://auth.mapactive.tech/health/
```

---

### 7. Email Not Sending

**Symptoms:**
- Password resets not received
- Notification emails not delivered
- SMTP errors in logs

**Solutions:**

#### A. Check Email Configuration
In `.env`:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-password
EMAIL_HOST_USE_TLS=True
```

#### B. Gmail-Specific Setup
1. Enable 2-Factor Authentication
2. Generate App Password:
   - Google Account → Security → 2-Step Verification
   - App passwords → Generate
   - Use generated password in `EMAIL_HOST_PASSWORD`

#### C. Test Email Sending
```bash
# Open Django shell
docker-compose -f docker-compose.production.yml exec auth-service python manage.py shell

# Send test email
from django.core.mail import send_mail
send_mail(
    'Test Subject',
    'Test message.',
    'from@mapactive.tech',
    ['to@example.com'],
    fail_silently=False,
)
```

#### D. Check Service Logs
```bash
docker-compose -f docker-compose.production.yml logs auth-service | grep -i email
docker-compose -f docker-compose.production.yml logs notification-service | grep -i email
```

---

### 8. High Memory Usage

**Symptoms:**
- Server running out of memory
- Services being killed (OOM)
- Slow performance

**Solutions:**

#### A. Check Current Usage
```bash
# Docker stats
docker stats

# System memory
free -h

# Container memory limits
docker-compose -f docker-compose.production.yml ps
```

#### B. Add Memory Limits
Edit `docker-compose.production.yml`:
```yaml
services:
  auth-service:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

#### C. Restart Heavy Services
```bash
# Restart Celery workers (often memory hungry)
docker-compose -f docker-compose.production.yml restart workflow-worker
docker-compose -f docker-compose.production.yml restart notification-worker
```

#### D. Optimize Postgres
```bash
# Connect to database
docker-compose -f docker-compose.production.yml exec postgres psql -U ticketapp_user -d auth_db

# Vacuum and analyze
VACUUM ANALYZE;

# Check database sizes
SELECT pg_size_pretty(pg_database_size('auth_db'));
```

---

### 9. Disk Space Issues

**Symptoms:**
- "No space left on device" errors
- Services can't write to disk
- Backup failures

**Solutions:**

#### A. Check Disk Usage
```bash
# System disk
df -h

# Docker disk usage
docker system df -v

# Volume sizes
docker volume ls
docker volume inspect [volume-name]
```

#### B. Clean Up Docker
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused containers
docker container prune

# Remove build cache
docker builder prune

# Clean everything (CAREFUL!)
docker system prune -a --volumes
```

#### C. Clean Up Logs
```bash
# Truncate Docker logs
echo "" > $(docker inspect --format='{{.LogPath}}' container-name)

# Or configure log rotation in /etc/docker/daemon.json:
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

#### D. Move Logs/Data
```bash
# Create new mount point
mkdir /mnt/extra-storage

# Update docker-compose.yml volumes
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/extra-storage/postgres_data
```

---

### 10. Performance Issues

**Symptoms:**
- Slow response times
- High CPU usage
- Requests timing out

**Solutions:**

#### A. Monitor Performance
```bash
# CPU and memory
docker stats

# Request times (check Traefik logs)
docker-compose -f docker-compose.production.yml logs traefik | grep "request"

# Database queries
docker-compose -f docker-compose.production.yml exec postgres psql -U ticketapp_user -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

#### B. Optimize Database
```bash
# Add indexes (example)
docker-compose -f docker-compose.production.yml exec auth-service python manage.py dbshell

CREATE INDEX idx_user_email ON users(email);
VACUUM ANALYZE;
```

#### C. Scale Workers
```bash
# Add more Celery workers
docker-compose -f docker-compose.production.yml up -d --scale workflow-worker=3
```

#### D. Enable Caching
Add Redis to `docker-compose.production.yml`:
```yaml
redis:
  image: redis:alpine
  restart: unless-stopped
  volumes:
    - redis_data:/data
```

Update Django settings to use Redis cache.

---

## 🛠️ Useful Commands

### Logs & Debugging
```bash
# All logs
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f auth-service

# Search logs
docker-compose -f docker-compose.production.yml logs | grep -i error

# Last 100 lines
docker-compose -f docker-compose.production.yml logs --tail=100 auth-service
```

### Service Management
```bash
# Restart service
docker-compose -f docker-compose.production.yml restart [service-name]

# Rebuild service
docker-compose -f docker-compose.production.yml build --no-cache [service-name]
docker-compose -f docker-compose.production.yml up -d [service-name]

# Stop all
docker-compose -f docker-compose.production.yml down

# Start all
docker-compose -f docker-compose.production.yml up -d
```

### Database Operations
```bash
# Connect to database
docker-compose -f docker-compose.production.yml exec postgres psql -U ticketapp_user -d auth_db

# Run migrations
docker-compose -f docker-compose.production.yml exec auth-service python manage.py migrate

# Create superuser
docker-compose -f docker-compose.production.yml exec auth-service python manage.py createsuperuser

# Django shell
docker-compose -f docker-compose.production.yml exec auth-service python manage.py shell
```

### Container Access
```bash
# Execute command in container
docker-compose -f docker-compose.production.yml exec [service-name] [command]

# Get shell access
docker-compose -f docker-compose.production.yml exec [service-name] sh

# Run as root
docker-compose -f docker-compose.production.yml exec -u root [service-name] sh
```

---

## 📞 Getting Help

### Check Documentation
1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. [QUICKSTART.md](QUICKSTART.md)
3. [README.md](README.md)

### Run Diagnostics
```bash
./scripts/monitor.sh
./scripts/validate.sh
```

### Collect Information for Issue Report
```bash
# System info
uname -a
docker --version
docker-compose --version

# Service status
docker-compose -f docker-compose.production.yml ps

# Recent logs
docker-compose -f docker-compose.production.yml logs --tail=100 > logs.txt

# Environment (remove sensitive data before sharing!)
docker-compose -f docker-compose.production.yml config > config.txt
```

### Create GitHub Issue
Include:
- Description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Relevant log outputs
- System information

---

## 🔄 Recovery Procedures

### Full System Recovery
```bash
# 1. Stop all services
docker-compose -f docker-compose.production.yml down

# 2. Restore from backup
./scripts/restore.sh TIMESTAMP

# 3. Verify services
./scripts/monitor.sh
```

### Individual Service Recovery
```bash
# 1. Stop service
docker-compose -f docker-compose.production.yml stop [service-name]

# 2. Remove container
docker-compose -f docker-compose.production.yml rm -f [service-name]

# 3. Rebuild and start
docker-compose -f docker-compose.production.yml build --no-cache [service-name]
docker-compose -f docker-compose.production.yml up -d [service-name]
```

### Database Recovery
```bash
# 1. Create backup of current state
./scripts/backup.sh

# 2. Stop services
docker-compose -f docker-compose.production.yml down

# 3. Restore database
gunzip -c /opt/backups/ticket-tracking-system/postgres_all_TIMESTAMP.sql.gz | \
  docker-compose -f docker-compose.production.yml exec -T postgres psql -U ticketapp_user

# 4. Start services
docker-compose -f docker-compose.production.yml up -d
```

---

**Last Updated:** 2024  
**Domain:** mapactive.tech  
**Support:** https://github.com/Gknightt/Ticket-Tracking-System/issues
