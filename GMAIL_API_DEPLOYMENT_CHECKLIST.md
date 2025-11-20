# Gmail API Migration Deployment Checklist

## Pre-Deployment

### Google Cloud Setup
- [ ] Create Google Cloud project (or select existing)
- [ ] Enable Gmail API for the project
- [ ] Create service account with Gmail API permissions
- [ ] Download service account credentials as `credentials.json`
- [ ] (G Suite only) Configure domain-wide delegation with Client ID
- [ ] (G Suite only) Add scope: `https://www.googleapis.com/auth/gmail.send`

### Development Environment
- [ ] Place `credentials.json` in `notification_service/` directory
- [ ] Update `notification_service/.env`:
  - [ ] `GMAIL_CREDENTIALS_PATH=credentials.json`
  - [ ] `GMAIL_SENDER_EMAIL=your-email@gmail.com`
  - [ ] `DJANGO_DEFAULT_FROM_EMAIL=noreply@yourdomain.com`
  - [ ] `DJANGO_CELERY_BROKER_URL=amqp://admin:admin@localhost:5672/`
- [ ] Update `auth/.env`:
  - [ ] `DJANGO_CELERY_BROKER_URL=amqp://admin:admin@localhost:5672/`
  - [ ] `NOTIFICATION_SERVICE_URL=http://localhost:8001`
- [ ] Install requirements: `cd notification_service && pip install -r requirements.txt`
- [ ] Verify `.gitignore` includes `credentials.json`

### Testing in Development
- [ ] Start RabbitMQ: `sudo systemctl start rabbitmq-server`
- [ ] Start notification service: `cd notification_service && python manage.py runserver 8001`
- [ ] Start Celery worker: `celery -A notification_service worker --pool=solo --loglevel=info -Q NOTIFICATION_TASKS,inapp-notification-queue`
- [ ] Test Gmail API service (Django shell):
  ```python
  from notifications.gmail_service import get_gmail_service
  gmail = get_gmail_service()
  success, msg_id, error = gmail.send_email('test@example.com', 'Test', 'Test')
  print(f"Success: {success}, ID: {msg_id}")
  ```
- [ ] Test password reset flow from auth service
- [ ] Test user invitation flow
- [ ] Test OTP email flow
- [ ] Test system addition flow
- [ ] Verify NotificationLog entries created with correct status
- [ ] Check email headers contain custom fields

## Staging Deployment

### Infrastructure
- [ ] Deploy updated `notification_service` code
- [ ] Upload `credentials.json` to staging server (secure location)
- [ ] Configure staging environment variables
- [ ] Ensure RabbitMQ is running and accessible
- [ ] Update firewall rules if needed
- [ ] Verify service-to-service network connectivity

### Configuration
- [ ] Set `DJANGO_ENV=production` or appropriate value
- [ ] Set `GMAIL_CREDENTIALS_PATH` to absolute path
- [ ] Set `GMAIL_SENDER_EMAIL` to staging email
- [ ] Configure `DJANGO_CELERY_BROKER_URL` for staging
- [ ] Update `ALLOWED_HOSTS` in settings
- [ ] Configure CORS settings for frontend

### Services
- [ ] Deploy auth service updates
- [ ] Deploy notification_service updates
- [ ] Restart all services
- [ ] Start Celery worker with systemd or supervisor:
  ```bash
  celery -A notification_service worker --pool=solo --loglevel=info -Q NOTIFICATION_TASKS,inapp-notification-queue
  ```
- [ ] Verify worker is running: `celery -A notification_service inspect active_queues`

### Testing
- [ ] Send test email via API
- [ ] Test forgot password flow end-to-end
- [ ] Test user registration with invitation email
- [ ] Test OTP flow with 2FA
- [ ] Test system addition notification
- [ ] Verify emails arrive in inbox
- [ ] Check email headers are present
- [ ] Verify NotificationLog entries
- [ ] Test error handling (invalid credentials, network issues)
- [ ] Monitor Celery logs for errors
- [ ] Check RabbitMQ queue status

## Production Deployment

### Pre-Production
- [ ] Review staging test results
- [ ] Create production service account in Google Cloud
- [ ] Download production `credentials.json`
- [ ] Plan deployment window (low traffic period)
- [ ] Notify team of deployment
- [ ] Prepare rollback plan

### Production Credentials
- [ ] Upload production `credentials.json` securely
- [ ] Never commit credentials to Git
- [ ] Set restrictive file permissions: `chmod 600 credentials.json`
- [ ] Verify credentials ownership
- [ ] Document credential location in internal wiki/docs

### Production Configuration
- [ ] Set `DJANGO_ENV=production`
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Configure production `GMAIL_SENDER_EMAIL`
- [ ] Set production `DJANGO_CELERY_BROKER_URL`
- [ ] Configure production RabbitMQ with authentication
- [ ] Update `ALLOWED_HOSTS` for production domain
- [ ] Set `SECRET_KEY` to secure random value
- [ ] Configure production CORS origins

### Deployment Steps
- [ ] Deploy notification_service code
- [ ] Deploy auth service code
- [ ] Run database migrations (if any)
- [ ] Upload credentials.json to secure location
- [ ] Update environment variables
- [ ] Restart notification_service
- [ ] Restart auth service
- [ ] Start/restart Celery workers
- [ ] Verify all services are healthy

### Post-Deployment Verification
- [ ] Check service health endpoints
- [ ] Verify Celery worker is connected
- [ ] Send test email to admin address
- [ ] Monitor application logs for errors
- [ ] Check RabbitMQ queues for backlog
- [ ] Verify NotificationLog database entries
- [ ] Test forgot password flow
- [ ] Test user invitation flow
- [ ] Monitor email delivery for first hour
- [ ] Check Gmail API quota usage

## Monitoring

### Logs to Monitor
- [ ] Notification service application logs
- [ ] Celery worker logs
- [ ] RabbitMQ logs
- [ ] Django application logs (auth service)
- [ ] System logs for Celery daemon

### Metrics to Track
- [ ] Email send success rate (NotificationLog.status)
- [ ] Email send latency
- [ ] Celery task queue length
- [ ] Gmail API quota usage
- [ ] Failed email count and reasons
- [ ] RabbitMQ message rate

### Alerts to Configure
- [ ] High rate of failed emails
- [ ] Celery worker down
- [ ] RabbitMQ queue growing
- [ ] Gmail API quota near limit
- [ ] Service account authentication failures

## Rollback Plan

If critical issues occur:

### Immediate Actions
1. [ ] Stop Celery workers
2. [ ] Revert notification_service code
3. [ ] Revert auth service code
4. [ ] Restore SMTP configuration in .env
5. [ ] Restart services
6. [ ] Monitor email sending

### Rollback Steps Detail
- [ ] Switch `EMAIL_BACKEND` back to SMTP in settings
- [ ] Comment out Gmail task routes
- [ ] Restore old `send_mail()` functions
- [ ] Update environment variables
- [ ] Restart Django services
- [ ] Verify SMTP email sending works
- [ ] Document rollback reason

## Post-Deployment

### Documentation
- [ ] Update internal wiki with production setup
- [ ] Document credential locations (securely)
- [ ] Update runbooks for Celery worker restart
- [ ] Document monitoring dashboards
- [ ] Update troubleshooting guides

### Team Communication
- [ ] Announce successful deployment
- [ ] Share monitoring dashboard links
- [ ] Provide quick reference for team
- [ ] Schedule post-deployment review

### Optimization
- [ ] Review email send performance
- [ ] Optimize Celery worker count if needed
- [ ] Tune RabbitMQ settings for load
- [ ] Review Gmail API quota and adjust if needed
- [ ] Implement email rate limiting if needed

## Success Criteria

Deployment is successful when:
- [ ] All email types send successfully
- [ ] Email delivery time < 30 seconds
- [ ] Zero errors in logs for 24 hours
- [ ] NotificationLog shows 100% sent status
- [ ] Celery worker processes tasks continuously
- [ ] No customer complaints about email delivery
- [ ] Gmail API quota well within limits

## Emergency Contacts

Document the following:
- [ ] Google Cloud project admin contact
- [ ] DevOps/Infrastructure team contact
- [ ] RabbitMQ administrator contact
- [ ] Email deliverability specialist contact

## Notes

- Gmail API daily send limit: 1 billion messages/day per project
- Service account send limit: 20,000 messages/day per delegated user
- Monitor quota in Google Cloud Console
- Consider implementing email rate limiting
- Keep credentials.json backup in secure vault
- Rotate service account keys periodically (90 days recommended)

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Approved By**: _______________
**Rollback Tested**: ☐ Yes ☐ No
