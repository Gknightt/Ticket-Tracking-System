# Deployment Checklist

Use this checklist to ensure a successful production deployment.

## 📋 Pre-Deployment Checklist

### Infrastructure Setup
- [ ] DigitalOcean Droplet created (Ubuntu 22.04, minimum 4GB RAM)
- [ ] Server accessible via SSH
- [ ] Root or sudo access available
- [ ] Firewall rules configured (allow ports 22, 80, 443)
- [ ] Domain registered: mapactive.tech
- [ ] Domain added to Cloudflare account
- [ ] Nameservers updated at registrar

### DNS Configuration
- [ ] A record: @ → SERVER_IP
- [ ] A record: www → SERVER_IP
- [ ] A record: auth → SERVER_IP
- [ ] A record: workflow → SERVER_IP
- [ ] A record: ticket → SERVER_IP
- [ ] A record: messaging → SERVER_IP
- [ ] A record: notification → SERVER_IP
- [ ] A record: rabbitmq → SERVER_IP
- [ ] A record: traefik → SERVER_IP
- [ ] All records set to "DNS only" (grey cloud)
- [ ] DNS propagation verified (nslookup/dig)

### Cloudflare API Setup
- [ ] Cloudflare API token created
- [ ] Token has "Edit zone DNS" permission
- [ ] Token tested and verified active
- [ ] API email and token saved securely

### Credentials Prepared
- [ ] Strong PostgreSQL password generated (20+ characters)
- [ ] Strong RabbitMQ password generated (20+ characters)
- [ ] JWT signing key generated (50+ characters)
- [ ] Unique secret key for each service generated
- [ ] Traefik dashboard password hash generated
- [ ] Email SMTP credentials obtained
- [ ] Gmail app password created (if using Gmail)
- [ ] Notification API keys generated

---

## 🚀 Deployment Steps

### Step 1: Server Setup
- [ ] SSH into server: `ssh root@YOUR_SERVER_IP`
- [ ] Update system: `apt-get update && apt-get upgrade -y`
- [ ] Install git: `apt-get install -y git`

### Step 2: Download Deployment Files
- [ ] Clone repository: `git clone https://github.com/Gknightt/Ticket-Tracking-System.git`
- [ ] Navigate to deployment: `cd Ticket-Tracking-System/deployment`
- [ ] Verify all files present: `ls -la`

### Step 3: Run Deployment Script
- [ ] Make script executable: `chmod +x scripts/deploy.sh`
- [ ] Run deployment: `sudo ./scripts/deploy.sh`
- [ ] Script completes without errors

### Step 4: Configure Environment
- [ ] Edit .env file: `nano .env`
- [ ] Set Cloudflare credentials:
  - [ ] CF_API_EMAIL
  - [ ] CF_DNS_API_TOKEN
- [ ] Set database credentials:
  - [ ] POSTGRES_USER
  - [ ] POSTGRES_PASSWORD
- [ ] Set RabbitMQ credentials:
  - [ ] RABBITMQ_USER
  - [ ] RABBITMQ_PASSWORD
- [ ] Set JWT and secret keys:
  - [ ] JWT_SIGNING_KEY
  - [ ] AUTH_SECRET_KEY
  - [ ] WORKFLOW_SECRET_KEY
  - [ ] TICKET_SECRET_KEY
  - [ ] MESSAGING_SECRET_KEY
  - [ ] NOTIFICATION_SECRET_KEY
- [ ] Set email configuration:
  - [ ] EMAIL_HOST
  - [ ] EMAIL_PORT
  - [ ] EMAIL_HOST_USER
  - [ ] EMAIL_HOST_PASSWORD
  - [ ] DEFAULT_FROM_EMAIL
- [ ] Set Traefik dashboard credentials:
  - [ ] TRAEFIK_DASHBOARD_USER
  - [ ] TRAEFIK_DASHBOARD_PASSWORD
- [ ] Set notification API keys:
  - [ ] NOTIFICATION_API_KEYS
  - [ ] NOTIFICATION_INTERNAL_API_KEY
- [ ] Save and exit

### Step 5: SSL Certificate Setup
- [ ] Run SSL setup: `./scripts/setup-ssl.sh`
- [ ] Verify Cloudflare credentials accepted
- [ ] DNS records verified
- [ ] acme.json permissions set to 600

### Step 6: Validate Configuration
- [ ] Run validator: `./scripts/validate.sh`
- [ ] All checks pass
- [ ] No weak passwords detected
- [ ] Docker and Docker Compose installed
- [ ] No port conflicts

### Step 7: Start Services
- [ ] Build images: `docker-compose -f docker-compose.production.yml build`
- [ ] Create network: `docker network create traefik-public`
- [ ] Start services: `docker-compose -f docker-compose.production.yml up -d`
- [ ] Wait 2-3 minutes for services to start

### Step 8: Database Migrations
- [ ] Auth service: `docker-compose -f docker-compose.production.yml exec auth-service python manage.py migrate`
- [ ] Workflow API: `docker-compose -f docker-compose.production.yml exec workflow-api python manage.py migrate`
- [ ] Ticket service: `docker-compose -f docker-compose.production.yml exec ticket-service python manage.py migrate`
- [ ] Messaging service: `docker-compose -f docker-compose.production.yml exec messaging-service python manage.py migrate`
- [ ] Notification service: `docker-compose -f docker-compose.production.yml exec notification-service python manage.py migrate`
- [ ] All migrations complete without errors

### Step 9: Create Superuser
- [ ] Run command: `docker-compose -f docker-compose.production.yml exec auth-service python manage.py createsuperuser`
- [ ] Enter username, email, and password
- [ ] Superuser created successfully

---

## ✅ Post-Deployment Verification

### Service Health Checks
- [ ] Run monitor: `./scripts/monitor.sh`
- [ ] All services show as "UP"
- [ ] No errors in recent logs
- [ ] PostgreSQL shows as "Ready"
- [ ] RabbitMQ connected successfully

### SSL Certificate Verification
- [ ] Check Traefik logs: `docker-compose logs traefik | grep -i acme`
- [ ] Certificates issued for all domains
- [ ] No ACME errors in logs
- [ ] acme.json file populated (size > 0)

### HTTP Endpoint Tests
- [ ] Frontend loads: https://mapactive.tech
- [ ] Auth service responds: https://auth.mapactive.tech/health/
- [ ] Workflow API responds: https://workflow.mapactive.tech/health/
- [ ] Ticket service responds: https://ticket.mapactive.tech/health/
- [ ] Messaging responds: https://messaging.mapactive.tech/health/
- [ ] Notification responds: https://notification.mapactive.tech/health/
- [ ] RabbitMQ UI loads: https://rabbitmq.mapactive.tech
- [ ] Traefik dashboard loads: https://traefik.mapactive.tech
- [ ] All endpoints use HTTPS (no certificate warnings)

### Functional Tests
- [ ] Frontend application loads completely
- [ ] Can access login page
- [ ] Can submit login form (test credentials)
- [ ] API requests complete successfully
- [ ] No CORS errors in browser console
- [ ] No CSRF errors in browser console
- [ ] File uploads work (if applicable)
- [ ] WebSocket connections work (messaging)

### Database Verification
- [ ] Connect to PostgreSQL: `docker-compose exec postgres psql -U ticketapp_user -l`
- [ ] All databases exist (auth_db, workflow_db, ticket_db, etc.)
- [ ] Tables created in each database
- [ ] Can query data successfully

### Message Queue Verification
- [ ] Access RabbitMQ UI: https://rabbitmq.mapactive.tech
- [ ] Login with credentials from .env
- [ ] All expected queues visible
- [ ] Celery workers connected
- [ ] Test messages can be sent and received

### Email Verification
- [ ] Trigger password reset email
- [ ] Email received successfully
- [ ] Links in email work correctly
- [ ] No email errors in service logs

---

## 🔒 Security Verification

### SSL/TLS
- [ ] All services accessible via HTTPS
- [ ] HTTP automatically redirects to HTTPS
- [ ] SSL Labs test: Grade A or higher
- [ ] Certificate valid and trusted
- [ ] TLS 1.2+ enforced

### Access Control
- [ ] Traefik dashboard requires authentication
- [ ] RabbitMQ UI requires authentication
- [ ] PostgreSQL not accessible externally
- [ ] Only ports 80, 443, and 22 open
- [ ] SSH key authentication configured
- [ ] Root SSH login disabled (recommended)

### Cookie & Session Security
- [ ] Cookies set with Secure flag
- [ ] Cookies set with HttpOnly flag
- [ ] SameSite attribute configured
- [ ] Session timeout configured
- [ ] CSRF protection enabled

### CORS Configuration
- [ ] Only production domains allowed
- [ ] No wildcard origins
- [ ] Credentials allowed only for trusted domains
- [ ] Preflight requests handled correctly

---

## 📊 Monitoring Setup

### Logging
- [ ] Log rotation configured
- [ ] Logs accessible: `docker-compose logs -f`
- [ ] Error logs monitored
- [ ] Access logs available

### Health Monitoring
- [ ] Health check script works: `./scripts/monitor.sh`
- [ ] All services report healthy
- [ ] Database connections verified
- [ ] Queue depths monitored

### Backup Configuration
- [ ] Backup script tested: `./scripts/backup.sh`
- [ ] Backup directory created: `/opt/backups/`
- [ ] Backups completing successfully
- [ ] Backup retention configured (7 days)
- [ ] Cron job for automated backups:
  ```bash
  crontab -e
  # Add: 0 2 * * * /opt/ticket-tracking-system/deployment/scripts/backup.sh
  ```

### Monitoring Cron Jobs (Optional)
- [ ] Daily health check reports
- [ ] Weekly disk space alerts
- [ ] Certificate expiry monitoring

---

## 📝 Documentation

### User Documentation
- [ ] Deployment guide reviewed
- [ ] Quick start guide available
- [ ] Troubleshooting guide accessible
- [ ] README.md up to date

### Admin Documentation
- [ ] .env file documented (without secrets)
- [ ] Service URLs documented
- [ ] Admin credentials stored securely
- [ ] Recovery procedures documented
- [ ] Backup/restore tested and documented

### Credentials Management
- [ ] All credentials stored in password manager
- [ ] .env file backed up securely (offline)
- [ ] Emergency access procedures defined
- [ ] Credential rotation schedule defined

---

## 🎯 Final Checks

### Performance
- [ ] Page load times acceptable (< 3 seconds)
- [ ] API response times acceptable (< 500ms)
- [ ] No memory leaks detected
- [ ] CPU usage within normal limits
- [ ] Database query performance optimized

### Capacity
- [ ] Disk space sufficient (> 50% free)
- [ ] Memory usage reasonable (< 80%)
- [ ] Bandwidth adequate
- [ ] Connection limits appropriate
- [ ] Worker capacity sufficient

### Disaster Recovery
- [ ] Backup tested and verified
- [ ] Restore procedure tested
- [ ] Recovery time objective (RTO) defined
- [ ] Recovery point objective (RPO) defined
- [ ] Emergency contact list created

### Go-Live
- [ ] Stakeholders notified
- [ ] Maintenance window scheduled (if needed)
- [ ] Rollback plan defined
- [ ] Support team ready
- [ ] Post-deployment monitoring plan active

---

## ✨ Optional Enhancements

### Performance Optimization
- [ ] Redis caching implemented
- [ ] CDN configured for static assets
- [ ] Database indexes optimized
- [ ] Query performance tuned
- [ ] Resource limits configured

### Monitoring & Alerting
- [ ] Uptime monitoring (UptimeRobot, etc.)
- [ ] Error tracking (Sentry, etc.)
- [ ] Log aggregation (ELK, etc.)
- [ ] APM tool configured
- [ ] Alert notifications set up

### CI/CD
- [ ] GitHub Actions workflow created
- [ ] Automated testing configured
- [ ] Automated deployments set up
- [ ] Staging environment created
- [ ] Blue-green deployment ready

### High Availability
- [ ] Load balancer configured
- [ ] Multiple server instances
- [ ] Database replication
- [ ] Geo-redundancy
- [ ] Automated failover

---

## 📞 Support Contacts

### Internal Team
- **DevOps Lead:** _____________
- **Backend Lead:** _____________
- **Frontend Lead:** _____________
- **Database Admin:** _____________

### External Vendors
- **DigitalOcean Support:** https://www.digitalocean.com/support/
- **Cloudflare Support:** https://support.cloudflare.com/
- **GitHub Issues:** https://github.com/Gknightt/Ticket-Tracking-System/issues

---

## 📅 Deployment Record

- **Deployment Date:** _____________
- **Deployed By:** _____________
- **Server IP:** _____________
- **Domain:** mapactive.tech
- **Git Commit:** _____________
- **Version:** 1.0.0

### Sign-Off

- [ ] Technical Lead: _____________ Date: _______
- [ ] Project Manager: _____________ Date: _______
- [ ] Security Officer: _____________ Date: _______
- [ ] Operations Manager: _____________ Date: _______

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Next Review:** 3 months after deployment
