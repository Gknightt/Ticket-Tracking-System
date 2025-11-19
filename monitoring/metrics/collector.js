/**
 * Metrics Collector
 * Aggregates performance data from logs and generates statistics
 */

const fs = require('fs');
const path = require('path');

class MetricsCollector {
  constructor() {
    this.logsDir = path.join(__dirname, '../logs');
    this.performanceLog = path.join(this.logsDir, 'performance.log');
    this.metricsFile = path.join(this.logsDir, 'metrics.json');
  }

  readPerformanceLogs() {
    try {
      if (!fs.existsSync(this.performanceLog)) {
        console.log('No performance logs found');
        return [];
      }

      const data = fs.readFileSync(this.performanceLog, 'utf8');
      const lines = data.trim().split('\n').filter(line => line);
      
      return lines.map(line => {
        try {
          return JSON.parse(line);
        } catch {
          return null;
        }
      }).filter(entry => entry !== null);
    } catch (error) {
      console.error('Error reading performance logs:', error.message);
      return [];
    }
  }

  calculateStatistics(entries) {
    if (entries.length === 0) {
      return null;
    }

    // Group by endpoint
    const byEndpoint = {};
    const byStatusCode = {};
    const durations = [];

    entries.forEach(entry => {
      // By endpoint
      const endpoint = `${entry.method} ${entry.path}`;
      if (!byEndpoint[endpoint]) {
        byEndpoint[endpoint] = {
          count: 0,
          totalDuration: 0,
          durations: [],
          errors: 0
        };
      }
      byEndpoint[endpoint].count++;
      byEndpoint[endpoint].totalDuration += entry.duration;
      byEndpoint[endpoint].durations.push(entry.duration);
      if (entry.statusCode >= 400) {
        byEndpoint[endpoint].errors++;
      }

      // By status code
      const statusCode = entry.statusCode;
      byStatusCode[statusCode] = (byStatusCode[statusCode] || 0) + 1;

      // All durations
      durations.push(entry.duration);
    });

    // Calculate percentiles
    const sortedDurations = durations.sort((a, b) => a - b);
    const p50 = sortedDurations[Math.floor(sortedDurations.length * 0.50)];
    const p95 = sortedDurations[Math.floor(sortedDurations.length * 0.95)];
    const p99 = sortedDurations[Math.floor(sortedDurations.length * 0.99)];

    // Process endpoint statistics
    const endpointStats = Object.entries(byEndpoint).map(([endpoint, data]) => {
      const sortedDurations = data.durations.sort((a, b) => a - b);
      return {
        endpoint,
        requests: data.count,
        avgDuration: Math.round(data.totalDuration / data.count),
        minDuration: Math.round(Math.min(...data.durations)),
        maxDuration: Math.round(Math.max(...data.durations)),
        p95: Math.round(sortedDurations[Math.floor(sortedDurations.length * 0.95)] || 0),
        errorRate: ((data.errors / data.count) * 100).toFixed(2) + '%'
      };
    }).sort((a, b) => b.requests - a.requests);

    return {
      summary: {
        totalRequests: entries.length,
        totalErrors: entries.filter(e => e.statusCode >= 400).length,
        errorRate: ((entries.filter(e => e.statusCode >= 400).length / entries.length) * 100).toFixed(2) + '%',
        avgResponseTime: Math.round(durations.reduce((a, b) => a + b, 0) / durations.length),
        minResponseTime: Math.round(Math.min(...durations)),
        maxResponseTime: Math.round(Math.max(...durations)),
        p50ResponseTime: Math.round(p50),
        p95ResponseTime: Math.round(p95),
        p99ResponseTime: Math.round(p99)
      },
      byEndpoint: endpointStats.slice(0, 20),
      byStatusCode,
      timeRange: {
        start: entries[0].timestamp,
        end: entries[entries.length - 1].timestamp
      }
    };
  }

  generateReport() {
    console.log('==========================================');
    console.log('PERFORMANCE METRICS REPORT');
    console.log('==========================================\n');

    const entries = this.readPerformanceLogs();
    
    if (entries.length === 0) {
      console.log('No performance data available.');
      console.log('Make sure the performance middleware is enabled and receiving requests.\n');
      return;
    }

    const stats = this.calculateStatistics(entries);

    console.log('SUMMARY');
    console.log('------------------------------------------');
    console.log(`Total Requests:       ${stats.summary.totalRequests}`);
    console.log(`Total Errors:         ${stats.summary.totalErrors}`);
    console.log(`Error Rate:           ${stats.summary.errorRate}`);
    console.log(`Avg Response Time:    ${stats.summary.avgResponseTime}ms`);
    console.log(`Min Response Time:    ${stats.summary.minResponseTime}ms`);
    console.log(`Max Response Time:    ${stats.summary.maxResponseTime}ms`);
    console.log(`P50 Response Time:    ${stats.summary.p50ResponseTime}ms`);
    console.log(`P95 Response Time:    ${stats.summary.p95ResponseTime}ms`);
    console.log(`P99 Response Time:    ${stats.summary.p99ResponseTime}ms`);
    console.log(`Time Range:           ${stats.timeRange.start} to ${stats.timeRange.end}`);

    console.log('\nTOP ENDPOINTS (by request count)');
    console.log('------------------------------------------');
    console.log('Endpoint                          | Requests | Avg(ms) | P95(ms) | Errors');
    console.log('------------------------------------------');
    stats.byEndpoint.forEach(ep => {
      const endpoint = ep.endpoint.padEnd(32);
      const requests = String(ep.requests).padStart(8);
      const avg = String(ep.avgDuration).padStart(7);
      const p95 = String(ep.p95).padStart(7);
      const errors = ep.errorRate.padStart(7);
      console.log(`${endpoint} | ${requests} | ${avg} | ${p95} | ${errors}`);
    });

    console.log('\nSTATUS CODE DISTRIBUTION');
    console.log('------------------------------------------');
    Object.entries(stats.byStatusCode)
      .sort((a, b) => b[1] - a[1])
      .forEach(([code, count]) => {
        const percentage = ((count / stats.summary.totalRequests) * 100).toFixed(2);
        console.log(`${code}: ${count} (${percentage}%)`);
      });

    // Save to file
    const reportPath = path.join(this.logsDir, `metrics-report-${Date.now()}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(stats, null, 2));
    console.log(`\n✓ Full report saved to: ${reportPath}\n`);
  }

  startRealTimeMonitoring(interval = 5000) {
    console.log(`Starting real-time monitoring (update every ${interval}ms)...`);
    console.log('Press Ctrl+C to stop\n');

    setInterval(() => {
      const entries = this.readPerformanceLogs();
      if (entries.length > 0) {
        const recent = entries.slice(-100); // Last 100 requests
        const stats = this.calculateStatistics(recent);
        
        console.clear();
        console.log('==========================================');
        console.log('REAL-TIME METRICS (Last 100 requests)');
        console.log('==========================================');
        console.log(`Requests:        ${stats.summary.totalRequests}`);
        console.log(`Errors:          ${stats.summary.totalErrors} (${stats.summary.errorRate})`);
        console.log(`Avg Response:    ${stats.summary.avgResponseTime}ms`);
        console.log(`P95 Response:    ${stats.summary.p95ResponseTime}ms`);
        console.log(`Updated:         ${new Date().toLocaleTimeString()}`);
      }
    }, interval);
  }
}

// CLI
if (require.main === module) {
  const collector = new MetricsCollector();
  const args = process.argv.slice(2);

  if (args.includes('--monitor') || args.includes('-m')) {
    const interval = parseInt(args[args.indexOf('--monitor') + 1] || args[args.indexOf('-m') + 1]) || 5000;
    collector.startRealTimeMonitoring(interval);
  } else {
    collector.generateReport();
  }
}

module.exports = MetricsCollector;
