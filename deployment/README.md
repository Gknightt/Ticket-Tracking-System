# Production Deployment - Ticket Tracking System

Complete production deployment setup using Docker Compose, Traefik reverse proxy, and automatic Let's Encrypt SSL certificates for the domain `mapactive.tech`.

## 📁 Folder Structure

```
deployment/
├── docker-compose.production.yml    # Main production compose file
├── .env.production.example          # Environment variables template
├── .env                             # Your actual environment (not committed)
├── DEPLOYMENT_GUIDE.md              # Complete deployment guide
├── QUICKSTART.md                    # Quick start instructions
├── README.md                        # This file
│
├── traefik/                         # Traefik configuration
│   ├── traefik.yml                  # Main Traefik config
│   ├── config.yml                   # Middleware & TLS settings
│   └── acme.json                    # SSL certificates storage
│
├── db-init/                         # Database initialization
│   └── init-databases.sh            # Creates all databases
│
├── scripts/                         # Utility scripts
│   ├── deploy.sh                    # Full deployment script
│   ├── setup-ssl.sh                 # SSL setup script
│   ├── backup.sh                    # Backup script
│   ├── restore.sh                   # Restore script
│   ├── monitor.sh                   # Health monitoring
│   └── update.sh                    # Update script
│
├── .env-examples/                   # Individual service env examples
│   ├── auth-service.env.example
│   ├── workflow-api.env.example
│   └── frontend.env.example
│
└── Dockerfile.frontend.production   # Production frontend Dockerfile
```

## 🚀 Quick Start

### For First-Time Deployment

```bash
# 1. Clone repository
git clone https://github.com/Gknightt/Ticket-Tracking-System.git
cd Ticket-Tracking-System/deployment

# 2. Run deployment script
sudo ./scripts/deploy.sh

# 3. Edit .env file when prompted
nano .env

# 4. The script handles the rest!
```

See [QUICKSTART.md](QUICKSTART.md) for detailed quick start guide.

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment documentation
  - Prerequisites
  - DNS configuration
  - Manual deployment steps
  - Service management
  - Troubleshooting
  - Security considerations

- **[QUICKSTART.md](QUICKSTART.md)** - Fast deployment guide
  - 5-minute deployment
  - Common commands
  - Quick troubleshooting

## 🌐 Service URLs

After deployment, services are available at:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | https://mapactive.tech | Main application UI |
| Auth Service | https://auth.mapactive.tech | Authentication & user management |
| Workflow API | https://workflow.mapactive.tech | Workflow orchestration |
| Ticket Service | https://ticket.mapactive.tech | Ticket management |
| Messaging | https://messaging.mapactive.tech | Real-time messaging |
| Notification | https://notification.mapactive.tech | Notification delivery |
| RabbitMQ UI | https://rabbitmq.mapactive.tech | Message queue management |
| Traefik Dashboard | https://traefik.mapactive.tech | Proxy & SSL management |

## 🔧 Utility Scripts

All scripts are located in the `scripts/` directory:

### Deploy Script
```bash
sudo ./scripts/deploy.sh
```
- Installs Docker & Docker Compose
- Clones/updates repository
- Configures environment
- Builds and starts all services
- Runs database migrations

### SSL Setup
```bash
./scripts/setup-ssl.sh
```
- Verifies Cloudflare credentials
- Checks DNS configuration
- Configures SSL certificate storage
- Tests DNS resolution

### Backup & Restore
```bash
# Create backup
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh TIMESTAMP
```
- Backs up databases, volumes, and configs
- Stores in `/opt/backups/`
- Retains last 7 days by default

### Health Monitoring
```bash
./scripts/monitor.sh
```
- Checks all service status
- Verifies HTTP endpoints
- Monitors SSL certificates
- Shows disk usage
- Checks database & queue status

### Update Application
```bash
sudo ./scripts/update.sh
```
- Creates backup before update
- Pulls latest code
- Rebuilds images
- Runs migrations
- Restarts services

## ⚙️ Configuration

### Environment Variables

The main `.env` file controls all services. Key sections:

**Cloudflare (for SSL):**
```env
CF_API_EMAIL=your-email@example.com
CF_DNS_API_TOKEN=your-api-token
```

**Database:**
```env
POSTGRES_USER=ticketapp_user
POSTGRES_PASSWORD=strong-password
```

**Security Keys:**
```env
JWT_SIGNING_KEY=random-key
AUTH_SECRET_KEY=random-key
WORKFLOW_SECRET_KEY=random-key
# ... etc
```

**Email:**
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-password
```

See `.env.production.example` for complete list.

### Traefik Configuration

**traefik.yml** - Main configuration:
- Entry points (HTTP/HTTPS)
- Let's Encrypt settings
- Cloudflare DNS challenge

**config.yml** - Additional settings:
- Security headers
- Rate limiting
- TLS options

### Django Settings

All Django services are configured for production:
- `DEBUG=False`
- Secure cookies enabled
- HTTPS enforcement
- CORS configured for subdomains
- CSRF protection with trusted origins

## 🔒 Security Features

✅ **Automatic HTTPS** - Let's Encrypt SSL via Traefik  
✅ **Secure Cookies** - SameSite=None, Secure, HttpOnly  
✅ **CORS Protection** - Whitelist-based origins  
✅ **Strong TLS** - TLS 1.2+ with secure ciphers  
✅ **Security Headers** - HSTS, XSS protection, etc.  
✅ **Network Isolation** - Internal Docker network  
✅ **Password Protection** - Traefik dashboard  
✅ **Database Access** - PostgreSQL not exposed externally  

## 📊 System Requirements

### Minimum
- **CPU:** 2 cores
- **RAM:** 4GB
- **Disk:** 20GB SSD
- **OS:** Ubuntu 22.04 LTS

### Recommended
- **CPU:** 4 cores
- **RAM:** 8GB
- **Disk:** 50GB SSD
- **OS:** Ubuntu 22.04 LTS

## 🐛 Troubleshooting

### Common Issues

**SSL certificates not issuing:**
```bash
# Check Traefik logs
docker-compose -f docker-compose.production.yml logs traefik

# Verify DNS
nslookup auth.mapactive.tech

# Reset certificates
rm traefik/acme.json
touch traefik/acme.json
chmod 600 traefik/acme.json
docker-compose -f docker-compose.production.yml restart traefik
```

**Service won't start:**
```bash
# Check logs
docker-compose -f docker-compose.production.yml logs [service-name]

# Rebuild
docker-compose -f docker-compose.production.yml build --no-cache [service-name]
docker-compose -f docker-compose.production.yml up -d [service-name]
```

**Database connection issues:**
```bash
# Check PostgreSQL
docker-compose -f docker-compose.production.yml ps postgres
docker-compose -f docker-compose.production.yml logs postgres

# Test connection
docker-compose -f docker-compose.production.yml exec postgres psql -U ticketapp_user -d auth_db
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting) for more.

## 📈 Monitoring

### View Logs
```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f auth-service

# Last 100 lines
docker-compose -f docker-compose.production.yml logs --tail=100 auth-service
```

### Health Check
```bash
./scripts/monitor.sh
```

### Container Stats
```bash
docker stats
```

## 🔄 Maintenance

### Regular Tasks

**Daily:**
- Monitor service health
- Check error logs
- Verify SSL certificates

**Weekly:**
- Review disk space
- Check queue depths
- Update system packages

**Monthly:**
- Test backup/restore
- Review security updates
- Optimize databases

### Automated Backups

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /opt/ticket-tracking-system/deployment/scripts/backup.sh

# Weekly health check report
0 8 * * 1 /opt/ticket-tracking-system/deployment/scripts/monitor.sh > /var/log/health-report.log
```

## 🆘 Support

- **GitHub Issues:** https://github.com/Gknightt/Ticket-Tracking-System/issues
- **Documentation:** See `/documentation` folder
- **Logs:** `docker-compose logs -f`

## 📝 Change Log

### Version 1.0 (Current)
- Initial production deployment setup
- Traefik reverse proxy with Let's Encrypt
- Subdomain routing for all services
- Automated SSL certificate management
- Complete deployment scripts
- Backup & restore functionality
- Health monitoring
- Production-ready Django configuration

## 🤝 Contributing

When contributing deployment improvements:

1. Test in a staging environment first
2. Update relevant documentation
3. Add/update example configurations
4. Test backup/restore procedures
5. Verify SSL certificate renewal

## 📄 License

This deployment configuration is part of the Ticket Tracking System project.

## 🎯 Deployment Checklist

Before going live:

- [ ] DNS records configured in Cloudflare
- [ ] `.env` file configured with strong passwords
- [ ] Cloudflare API token created with DNS permissions
- [ ] Email SMTP settings configured and tested
- [ ] All services start successfully
- [ ] SSL certificates issued for all domains
- [ ] Database migrations completed
- [ ] Superuser account created
- [ ] Firewall (UFW) configured
- [ ] Backup script tested
- [ ] Health monitoring working
- [ ] All service endpoints responding
- [ ] Frontend can reach all backend services
- [ ] CORS/CSRF configuration verified
- [ ] Security checklist completed

---

**Domain:** mapactive.tech  
**Deployment Method:** Docker Compose + Traefik  
**SSL Provider:** Let's Encrypt (via Cloudflare DNS)  
**Reverse Proxy:** Traefik v2.10  
**Last Updated:** 2024
