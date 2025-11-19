# Performance Monitoring - Integration Guide

This guide shows you how to integrate the performance monitoring tools into your Ticket Tracking System.

## Prerequisites

```bash
cd monitoring
npm install
pip install -r requirements.txt
```

## 1. Integration Steps

### For Express.js Applications

Add to your main server file (e.g., `app.js` or `server.js`):

```javascript
const PerformanceLogger = require('./monitoring/middleware/performance-logger');

// Initialize performance logger
const performanceLogger = new PerformanceLogger({
  logDir: './monitoring/logs',
  enableConsole: true
});

// Add middleware (before your routes)
app.use(performanceLogger.middleware());

// Optional: Add stats endpoint
app.get('/api/stats', (req, res) => {
  res.json(performanceLogger.getStats());
});
```

### For Django Applications

Add to your `settings.py`:

```python
MIDDLEWARE = [
    # ... other middleware
    'monitoring.middleware.performance_logger.PerformanceLoggingMiddleware',
    # ... rest of middleware
]
```

## 2. Usage Examples

### Run Load Tests

```bash
# Quick smoke test
cd monitoring
npm run load-test:smoke

# Standard load test
npm run load-test

# Stress test
npm run load-test:stress

# Run all tests
./load-tests/run-all-tests.sh
```

### Monitor Real-time Performance

```bash
# Collect and display metrics
npm run metrics:collect

# Real-time monitoring (updates every 5s)
node metrics/collector.js --monitor

# Generate comprehensive report
npm run report:generate
```

### Monitor Docker Containers

```bash
# Continuous monitoring (updates every 5s)
./docker/monitor.sh

# Single snapshot
./docker/monitor.sh --snapshot

# Analyze collected data
./docker/analyze.sh

# Collect container logs
./docker/collect-logs.sh
```

### Database Performance Analysis

```bash
# PostgreSQL analysis
python database/analyze.py

# Or run SQL queries directly
psql -U postgres -d ticketdb -f database/performance-queries.sql
```

## 3. Automated Monitoring Setup

### Create a Monitoring Cron Job

```bash
# Add to crontab (crontab -e)

# Run load test daily at 2 AM
0 2 * * * cd /path/to/monitoring && npm run load-test >> logs/cron.log 2>&1

# Generate report daily at 3 AM
0 3 * * * cd /path/to/monitoring && npm run report:generate >> logs/cron.log 2>&1

# Database analysis weekly on Sunday at 4 AM
0 4 * * 0 cd /path/to/monitoring && python database/analyze.py >> logs/cron.log 2>&1
```

## 4. Reading Reports

### Performance Metrics Report

After running `npm run report:generate`, check:
- `monitoring/reports/performance-report-TIMESTAMP.md` - Human-readable Markdown report
- `monitoring/reports/performance-report-TIMESTAMP.json` - Machine-readable JSON data

### Key Metrics to Monitor

**Response Time:**
- ✅ Good: P95 < 500ms
- ⚠️ Acceptable: P95 < 1000ms
- ❌ Poor: P95 > 1000ms

**Error Rate:**
- ✅ Excellent: < 1%
- ⚠️ Acceptable: < 5%
- ❌ High: > 5%

**Resource Usage (Docker):**
- ✅ Normal: CPU < 70%, Memory < 70%
- ⚠️ Warning: CPU > 80%, Memory > 80%
- ❌ Critical: CPU > 90%, Memory > 90%

## 5. Troubleshooting

### No logs being generated?

Make sure the middleware is properly integrated and receiving requests:

```bash
# Check if logs directory exists
ls -la monitoring/logs/

# Test with a simple request
curl http://localhost:8000/api/health
```

### Artillery not working?

```bash
# Install artillery globally
npm install -g artillery

# Or use npx
npx artillery run load-tests/artillery-config.yml
```

### Docker monitoring shows no containers?

```bash
# Check if containers are running
docker ps

# Check if you have Docker permissions
docker stats
```

## 6. CI/CD Integration

### GitHub Actions Example

```yaml
name: Performance Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  performance-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd monitoring
          npm install
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Wait for services
        run: sleep 30
      
      - name: Run load tests
        run: |
          cd monitoring
          npm run load-test:smoke
      
      - name: Generate report
        run: |
          cd monitoring
          npm run report:generate
      
      - name: Upload reports
        uses: actions/upload-artifact@v2
        with:
          name: performance-reports
          path: monitoring/reports/
```

## 7. Next Steps

1. **Establish Baselines**: Run tests for a week to establish performance baselines
2. **Set Alerts**: Configure alerts for when metrics exceed thresholds
3. **Regular Reviews**: Review reports weekly to identify trends
4. **Optimize**: Address slow endpoints and high error rates
5. **Scale Testing**: Gradually increase load to find system limits

## Support

For issues or questions:
1. Check the logs in `monitoring/logs/`
2. Review the README in each subdirectory
3. Run tools with `--help` flag for usage information
