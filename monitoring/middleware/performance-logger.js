/**
 * Performance Logging Middleware for Express.js
 * Tracks response times, status codes, and request details
 */

const fs = require('fs');
const path = require('path');

class PerformanceLogger {
  constructor(options = {}) {
    this.logDir = options.logDir || path.join(__dirname, '../logs');
    this.logFile = path.join(this.logDir, 'performance.log');
    this.metricsFile = path.join(this.logDir, 'metrics.json');
    this.enableConsole = options.enableConsole !== false;
    
    // Create logs directory if it doesn't exist
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
    
    // Initialize metrics storage
    this.metrics = {
      requests: [],
      summary: {
        totalRequests: 0,
        totalErrors: 0,
        averageResponseTime: 0,
        startTime: new Date().toISOString()
      }
    };
    
    this.loadMetrics();
  }

  loadMetrics() {
    try {
      if (fs.existsSync(this.metricsFile)) {
        const data = fs.readFileSync(this.metricsFile, 'utf8');
        this.metrics = JSON.parse(data);
      }
    } catch (error) {
      console.error('Error loading metrics:', error.message);
    }
  }

  saveMetrics() {
    try {
      fs.writeFileSync(this.metricsFile, JSON.stringify(this.metrics, null, 2));
    } catch (error) {
      console.error('Error saving metrics:', error.message);
    }
  }

  middleware() {
    return (req, res, next) => {
      const startTime = Date.now();
      const startDate = new Date();

      // Capture original end function
      const originalEnd = res.end;

      res.end = (...args) => {
        const duration = Date.now() - startTime;
        
        const logEntry = {
          timestamp: startDate.toISOString(),
          method: req.method,
          path: req.path,
          url: req.originalUrl || req.url,
          statusCode: res.statusCode,
          duration: duration,
          ip: req.ip || req.connection.remoteAddress,
          userAgent: req.get('user-agent') || 'unknown'
        };

        // Log to file
        this.logToFile(logEntry);
        
        // Update metrics
        this.updateMetrics(logEntry);
        
        // Console output
        if (this.enableConsole) {
          const color = this.getColorForStatus(res.statusCode);
          console.log(
            `${logEntry.timestamp} | ${color}${res.statusCode}\x1b[0m | ` +
            `${duration}ms | ${req.method} ${req.path}`
          );
        }

        // Call original end
        originalEnd.apply(res, args);
      };

      next();
    };
  }

  logToFile(entry) {
    const logLine = JSON.stringify(entry) + '\n';
    fs.appendFileSync(this.logFile, logLine);
  }

  updateMetrics(entry) {
    this.metrics.requests.push(entry);
    this.metrics.summary.totalRequests++;
    
    if (entry.statusCode >= 400) {
      this.metrics.summary.totalErrors++;
    }

    // Calculate average response time
    const totalTime = this.metrics.requests.reduce((sum, req) => sum + req.duration, 0);
    this.metrics.summary.averageResponseTime = Math.round(totalTime / this.metrics.requests.length);

    // Keep only last 10000 requests in memory
    if (this.metrics.requests.length > 10000) {
      this.metrics.requests = this.metrics.requests.slice(-10000);
    }

    // Save metrics every 100 requests
    if (this.metrics.summary.totalRequests % 100 === 0) {
      this.saveMetrics();
    }
  }

  getColorForStatus(statusCode) {
    if (statusCode >= 500) return '\x1b[31m'; // Red
    if (statusCode >= 400) return '\x1b[33m'; // Yellow
    if (statusCode >= 300) return '\x1b[36m'; // Cyan
    if (statusCode >= 200) return '\x1b[32m'; // Green
    return '\x1b[0m'; // Reset
  }

  getStats() {
    return {
      ...this.metrics.summary,
      errorRate: ((this.metrics.summary.totalErrors / this.metrics.summary.totalRequests) * 100).toFixed(2) + '%',
      requestsInMemory: this.metrics.requests.length
    };
  }
}

module.exports = PerformanceLogger;
