# Quick Reference Card

Common commands and operations for managing the production deployment.

## 🚀 Service Management

```bash
# Navigate to deployment directory
cd /opt/ticket-tracking-system/deployment

# Start all services
docker-compose -f docker-compose.production.yml up -d

# Stop all services
docker-compose -f docker-compose.production.yml down

# Restart all services
docker-compose -f docker-compose.production.yml restart

# Restart specific service
docker-compose -f docker-compose.production.yml restart auth-service

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f

# View specific service logs
docker-compose -f docker-compose.production.yml logs -f auth-service
```

## 🔍 Health & Monitoring

```bash
# Run health check
./scripts/monitor.sh

# Validate configuration
./scripts/validate.sh

# Check SSL certificates
docker-compose -f docker-compose.production.yml logs traefik | grep -i acme

# View container stats
docker stats

# Check disk space
df -h
docker system df
```

## 🗄️ Database Operations

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.production.yml exec postgres psql -U ticketapp_user -d auth_db

# List databases
docker-compose -f docker-compose.production.yml exec postgres psql -U ticketapp_user -c "\l"

# Run migrations
docker-compose -f docker-compose.production.yml exec auth-service python manage.py migrate
docker-compose -f docker-compose.production.yml exec workflow-api python manage.py migrate
docker-compose -f docker-compose.production.yml exec ticket-service python manage.py migrate

# Create superuser
docker-compose -f docker-compose.production.yml exec auth-service python manage.py createsuperuser

# Django shell
docker-compose -f docker-compose.production.yml exec auth-service python manage.py shell
```

## 💾 Backup & Restore

```bash
# Create backup
./scripts/backup.sh

# List available backups
ls -lh /opt/backups/ticket-tracking-system/

# Restore from backup
./scripts/restore.sh TIMESTAMP
```

## 🔄 Updates

```bash
# Update application
sudo ./scripts/update.sh

# Manual update process
git pull
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

## 🐰 RabbitMQ Management

```bash
# Access web UI
# https://rabbitmq.mapactive.tech

# List queues
docker-compose -f docker-compose.production.yml exec rabbitmq rabbitmqctl list_queues

# Purge queue
docker-compose -f docker-compose.production.yml exec rabbitmq rabbitmqctl purge_queue QUEUE_NAME

# Check connections
docker-compose -f docker-compose.production.yml exec rabbitmq rabbitmqctl list_connections
```

## 🐛 Troubleshooting

```bash
# View service logs with errors
docker-compose -f docker-compose.production.yml logs | grep -i error

# Rebuild service
docker-compose -f docker-compose.production.yml build --no-cache auth-service
docker-compose -f docker-compose.production.yml up -d auth-service

# Reset SSL certificates
rm traefik/acme.json
touch traefik/acme.json
chmod 600 traefik/acme.json
docker-compose -f docker-compose.production.yml restart traefik

# Check DNS
nslookup auth.mapactive.tech
dig auth.mapactive.tech

# Test service endpoint
curl -I https://auth.mapactive.tech/health/
```

## 🧹 Cleanup

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused containers
docker container prune

# Clean everything (CAREFUL!)
docker system prune -a --volumes
```

## 🔐 Security

```bash
# Check firewall status
ufw status

# View fail2ban logs
tail -f /var/log/fail2ban.log

# List Docker networks
docker network ls

# Check who's logged in
who
last
```

## 📊 Service URLs

| Service | URL |
|---------|-----|
| Frontend | https://mapactive.tech |
| Auth | https://auth.mapactive.tech |
| Workflow | https://workflow.mapactive.tech |
| Tickets | https://ticket.mapactive.tech |
| Messaging | https://messaging.mapactive.tech |
| Notifications | https://notification.mapactive.tech |
| RabbitMQ | https://rabbitmq.mapactive.tech |
| Traefik | https://traefik.mapactive.tech |

## 🆘 Emergency Procedures

### Service Down
```bash
# Check logs
docker-compose -f docker-compose.production.yml logs [service-name]

# Restart service
docker-compose -f docker-compose.production.yml restart [service-name]

# If restart fails, rebuild
docker-compose -f docker-compose.production.yml build --no-cache [service-name]
docker-compose -f docker-compose.production.yml up -d [service-name]
```

### Database Issues
```bash
# Check PostgreSQL status
docker-compose -f docker-compose.production.yml ps postgres

# Restart PostgreSQL
docker-compose -f docker-compose.production.yml restart postgres

# Emergency restore
./scripts/restore.sh LAST_GOOD_TIMESTAMP
```

### Out of Disk Space
```bash
# Check usage
df -h
docker system df

# Clean up
docker system prune -a
docker volume prune
```

### SSL Certificate Issues
```bash
# View Traefik logs
docker-compose -f docker-compose.production.yml logs traefik

# Reset certificates
rm traefik/acme.json
touch traefik/acme.json
chmod 600 traefik/acme.json
docker-compose -f docker-compose.production.yml restart traefik
```

## 📝 Important Files

```
/opt/ticket-tracking-system/deployment/
├── .env                          # Environment variables (SENSITIVE!)
├── docker-compose.production.yml # Main compose file
├── traefik/acme.json            # SSL certificates (SENSITIVE!)
└── scripts/                     # Utility scripts
    ├── deploy.sh
    ├── backup.sh
    ├── restore.sh
    ├── monitor.sh
    └── update.sh

/opt/backups/ticket-tracking-system/
└── postgres_all_TIMESTAMP.sql.gz  # Database backups
```

## 🔑 Default Credentials Location

**NEVER store credentials in plain text!**

Credentials are in:
- `.env` file (production environment)
- Password manager (recommended)
- Secure vault (recommended)

## 📞 Support

- **Documentation:** `/opt/ticket-tracking-system/deployment/`
- **GitHub Issues:** https://github.com/Gknightt/Ticket-Tracking-System/issues
- **Logs:** `docker-compose -f docker-compose.production.yml logs -f`

---

**Print this page and keep it handy!**

**Domain:** mapactive.tech  
**Location:** `/opt/ticket-tracking-system/deployment/`
