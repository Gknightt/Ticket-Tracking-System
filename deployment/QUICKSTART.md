# Quick Start Guide - Production Deployment

## 🚀 5-Minute Deployment

### Prerequisites
- DigitalOcean Droplet (Ubuntu 22.04, 4GB+ RAM)
- Domain: `mapactive.tech` pointed to your server IP
- Cloudflare account with API token

### Step 1: DNS Setup (5 minutes)
Add these A records in Cloudflare DNS:
```
@ → YOUR_SERVER_IP
www → YOUR_SERVER_IP
auth → YOUR_SERVER_IP
workflow → YOUR_SERVER_IP
ticket → YOUR_SERVER_IP
messaging → YOUR_SERVER_IP
notification → YOUR_SERVER_IP
rabbitmq → YOUR_SERVER_IP
traefik → YOUR_SERVER_IP
```

### Step 2: Server Setup (10 minutes)
```bash
# SSH into your server
ssh root@YOUR_SERVER_IP

# Download and run deployment script
curl -fsSL https://raw.githubusercontent.com/Gknightt/Ticket-Tracking-System/main/deployment/scripts/deploy.sh -o deploy.sh
chmod +x deploy.sh
sudo ./deploy.sh
```

### Step 3: Configure Environment (5 minutes)
When prompted, edit the `.env` file:
```bash
nano /opt/ticket-tracking-system/deployment/.env
```

**Must change:**
1. `CF_API_EMAIL` - Your Cloudflare email
2. `CF_DNS_API_TOKEN` - Your Cloudflare API token
3. All passwords (generate strong ones)
4. All secret keys (use: `python -c "import secrets; print(secrets.token_urlsafe(50))"`)
5. Email settings (Gmail SMTP or other)

### Step 4: Start Services (10 minutes)
The script will automatically:
- Install Docker & Docker Compose
- Build all services
- Configure SSL certificates
- Run database migrations

### Step 5: Verify Deployment
```bash
cd /opt/ticket-tracking-system/deployment
./scripts/monitor.sh
```

Check services at:
- 🌐 Frontend: https://mapactive.tech
- 🔐 Auth: https://auth.mapactive.tech
- ⚙️ Workflow: https://workflow.mapactive.tech
- 🎫 Tickets: https://ticket.mapactive.tech

## 🔧 Common Commands

### View Logs
```bash
cd /opt/ticket-tracking-system/deployment
docker-compose -f docker-compose.production.yml logs -f [service-name]
```

### Restart Service
```bash
docker-compose -f docker-compose.production.yml restart [service-name]
```

### Check Status
```bash
./scripts/monitor.sh
```

### Backup
```bash
./scripts/backup.sh
```

### Update
```bash
./scripts/update.sh
```

## ⚠️ Troubleshooting

### SSL Certificates Not Working
1. Check DNS propagation: `nslookup auth.mapactive.tech`
2. View Traefik logs: `docker-compose logs -f traefik`
3. Verify Cloudflare API token has DNS edit permissions

### Services Not Starting
1. Check logs: `docker-compose logs [service-name]`
2. Verify .env file is properly configured
3. Ensure ports 80 and 443 are open

### Database Connection Issues
1. Check PostgreSQL is running: `docker-compose ps postgres`
2. Verify database credentials in .env
3. Check database logs: `docker-compose logs postgres`

## 📚 Full Documentation
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete documentation.

## 🆘 Need Help?
- Check logs: `docker-compose logs -f`
- Run health check: `./scripts/monitor.sh`
- Create GitHub issue with error logs

## 📊 Key Metrics

After deployment, monitor:
- SSL Certificate Status (auto-renews every 60 days)
- Database Size (daily)
- RabbitMQ Queue Depth (hourly)
- Container Memory Usage (continuous)
- Disk Space (daily)

## 🔒 Security Checklist

- [ ] Changed all default passwords in .env
- [ ] Generated strong JWT signing key
- [ ] Configured Cloudflare API token with minimum permissions
- [ ] Enabled UFW firewall
- [ ] Configured SSH key authentication
- [ ] Set up automatic backups
- [ ] Reviewed Traefik dashboard credentials

## 🎯 Next Steps

1. **Create Superuser**
   ```bash
   docker-compose exec auth-service python manage.py createsuperuser
   ```

2. **Setup Automatic Backups**
   Add to crontab:
   ```bash
   0 2 * * * /opt/ticket-tracking-system/deployment/scripts/backup.sh
   ```

3. **Monitor Logs**
   Setup log aggregation or use:
   ```bash
   watch -n 10 './scripts/monitor.sh'
   ```

4. **Test Email**
   Send test notification to verify SMTP settings

5. **Load Test**
   Use tools like Apache Bench or k6 to test capacity

## 📞 Support

- Repository: https://github.com/Gknightt/Ticket-Tracking-System
- Issues: Create a GitHub issue
- Docs: /documentation folder

---

**Last Updated:** 2024  
**Target Domain:** mapactive.tech  
**Deployment Method:** Docker Compose + Traefik
