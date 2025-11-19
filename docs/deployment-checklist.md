# Deployment Checklist

This checklist ensures all necessary steps are completed before, during, and after deployment.

## Pre-Deployment

### Code Preparation
- [ ] All tests pass locally
- [ ] Code review completed and approved
- [ ] All GitHub Actions workflows pass
- [ ] Security scans completed (no critical vulnerabilities)
- [ ] Code quality checks pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Database migrations created and tested
- [ ] Environment variables documented

### Testing
- [ ] Unit tests pass (>80% coverage)
- [ ] Integration tests pass
- [ ] Manual testing completed on staging
- [ ] Load testing performed (if applicable)
- [ ] Security testing completed
- [ ] Browser compatibility tested (frontend)
- [ ] Mobile responsiveness verified (frontend)

### Infrastructure
- [ ] Railway services configured
- [ ] Environment variables set in Railway
- [ ] Database backup created
- [ ] SSL/TLS certificates valid
- [ ] DNS records updated (if needed)
- [ ] Monitoring and alerting configured
- [ ] Log aggregation set up

### Communication
- [ ] Deployment scheduled and announced
- [ ] Stakeholders notified
- [ ] Maintenance window communicated (if downtime expected)
- [ ] Rollback plan documented and shared
- [ ] On-call team identified

## During Deployment

### Railway Deployment
- [ ] Push to production branch
- [ ] Monitor Railway build logs
- [ ] Verify all services start successfully
- [ ] Run database migrations
  ```bash
  railway run python manage.py migrate
  ```
- [ ] Verify static files served correctly
- [ ] Check health endpoints
  - [ ] Auth Service: `/api/health/`
  - [ ] Ticket Service: `/api/health/`
  - [ ] Workflow API: `/api/health/`
  - [ ] Notification Service: `/api/health/`

### Docker Deployment (Alternative)
- [ ] Build Docker images
  ```bash
  docker-compose build
  ```
- [ ] Tag images with version
  ```bash
  docker tag service:latest service:v1.2.3
  ```
- [ ] Push to container registry (if applicable)
- [ ] Deploy using docker-compose
  ```bash
  docker-compose up -d
  ```
- [ ] Run migrations
  ```bash
  docker exec -it service_name python manage.py migrate
  ```

### Verification
- [ ] Application accessible via production URL
- [ ] Login functionality works
- [ ] Critical user workflows tested
- [ ] API endpoints responding correctly
- [ ] WebSocket connections working (if applicable)
- [ ] Background jobs processing (Celery)
- [ ] Email notifications sending
- [ ] File uploads working
- [ ] Database connections stable

### Monitoring
- [ ] Check Railway metrics dashboard
- [ ] Monitor error rates
- [ ] Monitor response times
- [ ] Monitor CPU/Memory usage
- [ ] Check application logs for errors
- [ ] Verify RabbitMQ queue processing
- [ ] Database performance normal

## Post-Deployment

### Immediate Actions
- [ ] Smoke test critical features
- [ ] Monitor error tracking (Sentry, if configured)
- [ ] Check for increased error rates
- [ ] Verify performance metrics
- [ ] Test with real user accounts
- [ ] Verify integrations still working
- [ ] Monitor user feedback channels

### First 30 Minutes
- [ ] Monitor application metrics
- [ ] Check for any user-reported issues
- [ ] Verify background job processing
- [ ] Check database performance
- [ ] Monitor API rate limits
- [ ] Verify caching working correctly

### First 24 Hours
- [ ] Review error logs
- [ ] Monitor performance trends
- [ ] Check for memory leaks
- [ ] Verify data integrity
- [ ] Monitor resource usage
- [ ] Review user feedback
- [ ] Update stakeholders on deployment status

### Documentation
- [ ] Update deployment notes
- [ ] Document any issues encountered
- [ ] Update runbook if needed
- [ ] Share deployment report
- [ ] Archive deployment logs

## Rollback Procedure

### When to Rollback
- Critical bugs affecting core functionality
- Security vulnerabilities discovered
- Performance degradation >50%
- Data integrity issues
- System instability

### Rollback Steps
1. **Railway Rollback**
   ```bash
   # In Railway dashboard, click "Rollback" to previous deployment
   # Or redeploy previous version
   railway up --from=<previous-commit-hash>
   ```

2. **Docker Rollback**
   ```bash
   # Stop current containers
   docker-compose down
   
   # Revert to previous image version
   docker-compose pull service:v1.2.2
   
   # Start with previous version
   docker-compose up -d
   ```

3. **Database Rollback**
   ```bash
   # If migrations need to be reversed
   python manage.py migrate app_name <previous_migration>
   ```

4. **Verification**
   - [ ] Application accessible
   - [ ] Core features working
   - [ ] No data loss
   - [ ] Logs showing normal operation

5. **Communication**
   - [ ] Notify stakeholders of rollback
   - [ ] Document reason for rollback
   - [ ] Create incident report
   - [ ] Schedule post-mortem

## Emergency Contacts

### On-Call Team
- **Primary**: [Name, Phone, Email]
- **Secondary**: [Name, Phone, Email]
- **Manager**: [Name, Phone, Email]

### Service Contacts
- **Railway Support**: support@railway.app
- **Database Admin**: [Contact info]
- **DevOps Team**: [Contact info]

## Deployment History

### Template
```markdown
## Deployment: [Version] - [Date]
**Deployed By**: [Name]
**Start Time**: [Time]
**End Time**: [Time]
**Status**: Success/Failure

### Changes
- Change 1
- Change 2

### Issues
- Issue 1 (Resolved)
- Issue 2 (Monitoring)

### Metrics
- Deployment Time: X minutes
- Downtime: X minutes (if any)
- Error Rate: X%
- Response Time: Xms
```

---

## Useful Commands

### Railway CLI
```bash
# Login
railway login

# Link project
railway link

# View logs
railway logs

# Run migrations
railway run python manage.py migrate

# Open shell
railway run python manage.py shell

# Check environment
railway env
```

### Docker Commands
```bash
# View logs
docker logs service_name

# Execute command in container
docker exec -it service_name bash

# Check container status
docker ps

# View container stats
docker stats

# Restart service
docker-compose restart service_name
```

### Database Commands
```bash
# Create backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql $DATABASE_URL < backup.sql

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

---

**Last Updated**: November 2025
**Next Review**: Before each major release
