/**
 * Performance Report Generator
 * Creates comprehensive HTML and Markdown reports
 */

const fs = require('fs');
const path = require('path');

class ReportGenerator {
  constructor() {
    this.logsDir = path.join(__dirname, '../logs');
    this.outputDir = path.join(__dirname, '../reports');
    
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  getLatestMetrics() {
    const files = fs.readdirSync(this.logsDir)
      .filter(f => f.startsWith('metrics-report-') && f.endsWith('.json'))
      .sort()
      .reverse();
    
    if (files.length === 0) {
      console.log('No metrics reports found. Run metrics collection first.');
      return null;
    }

    const latestFile = path.join(this.logsDir, files[0]);
    return JSON.parse(fs.readFileSync(latestFile, 'utf8'));
  }

  generateMarkdownReport(metrics) {
    const timestamp = new Date().toISOString();
    
    let markdown = `# Performance Metrics Report\n\n`;
    markdown += `**Generated:** ${timestamp}\n\n`;
    markdown += `---\n\n`;
    
    // Summary
    markdown += `## Executive Summary\n\n`;
    markdown += `| Metric | Value |\n`;
    markdown += `|--------|-------|\n`;
    Object.entries(metrics.summary).forEach(([key, value]) => {
      markdown += `| ${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} | ${value} |\n`;
    });
    
    // Time Range
    markdown += `\n**Analysis Period:** ${metrics.timeRange.start} to ${metrics.timeRange.end}\n\n`;
    
    // Endpoints
    markdown += `## Endpoint Performance\n\n`;
    markdown += `| Endpoint | Requests | Avg (ms) | P95 (ms) | Max (ms) | Error Rate |\n`;
    markdown += `|----------|----------|----------|----------|----------|------------|\n`;
    metrics.byEndpoint.forEach(ep => {
      markdown += `| ${ep.endpoint} | ${ep.requests} | ${ep.avgDuration} | ${ep.p95} | ${ep.maxDuration} | ${ep.errorRate} |\n`;
    });
    
    // Status Codes
    markdown += `\n## Status Code Distribution\n\n`;
    markdown += `| Status Code | Count | Percentage |\n`;
    markdown += `|-------------|-------|------------|\n`;
    Object.entries(metrics.byStatusCode).forEach(([code, count]) => {
      const percentage = ((count / metrics.summary.totalRequests) * 100).toFixed(2);
      markdown += `| ${code} | ${count} | ${percentage}% |\n`;
    });
    
    // Performance Assessment
    markdown += `\n## Performance Assessment\n\n`;
    markdown += this.generateAssessment(metrics);
    
    // Recommendations
    markdown += `\n## Recommendations\n\n`;
    markdown += this.generateRecommendations(metrics);
    
    return markdown;
  }

  generateAssessment(metrics) {
    let assessment = '';
    const avgTime = metrics.summary.avgResponseTime;
    const p95Time = metrics.summary.p95ResponseTime;
    const errorRate = parseFloat(metrics.summary.errorRate);
    
    // Response Time Assessment
    if (p95Time < 500) {
      assessment += `✅ **Response Time:** Excellent (P95: ${p95Time}ms)\n`;
    } else if (p95Time < 1000) {
      assessment += `⚠️ **Response Time:** Good (P95: ${p95Time}ms)\n`;
    } else {
      assessment += `❌ **Response Time:** Needs Improvement (P95: ${p95Time}ms)\n`;
    }
    
    // Error Rate Assessment
    if (errorRate < 1) {
      assessment += `✅ **Error Rate:** Excellent (${metrics.summary.errorRate})\n`;
    } else if (errorRate < 5) {
      assessment += `⚠️ **Error Rate:** Acceptable (${metrics.summary.errorRate})\n`;
    } else {
      assessment += `❌ **Error Rate:** High (${metrics.summary.errorRate})\n`;
    }
    
    // Request Volume
    assessment += `📊 **Request Volume:** ${metrics.summary.totalRequests} requests analyzed\n`;
    
    return assessment;
  }

  generateRecommendations(metrics) {
    let recommendations = [];
    
    const avgTime = metrics.summary.avgResponseTime;
    const p95Time = metrics.summary.p95ResponseTime;
    const errorRate = parseFloat(metrics.summary.errorRate);
    
    if (p95Time > 1000) {
      recommendations.push('- Consider implementing caching for frequently accessed endpoints');
      recommendations.push('- Review database query performance and add indexes where needed');
    }
    
    if (errorRate > 1) {
      recommendations.push('- Investigate and fix endpoints with high error rates');
      recommendations.push('- Implement better error handling and monitoring');
    }
    
    // Find slow endpoints
    const slowEndpoints = metrics.byEndpoint.filter(ep => ep.avgDuration > 1000);
    if (slowEndpoints.length > 0) {
      recommendations.push(`- Optimize slow endpoints: ${slowEndpoints.map(e => e.endpoint).join(', ')}`);
    }
    
    if (recommendations.length === 0) {
      recommendations.push('- System is performing well. Continue monitoring.');
      recommendations.push('- Consider load testing to find system limits.');
    }
    
    return recommendations.join('\n');
  }

  generate() {
    console.log('Generating performance report...\n');
    
    const metrics = this.getLatestMetrics();
    if (!metrics) {
      return;
    }
    
    const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
    
    // Generate Markdown Report
    const markdown = this.generateMarkdownReport(metrics);
    const mdPath = path.join(this.outputDir, `performance-report-${timestamp}.md`);
    fs.writeFileSync(mdPath, markdown);
    console.log(`✓ Markdown report: ${mdPath}`);
    
    // Copy JSON for reference
    const jsonPath = path.join(this.outputDir, `performance-report-${timestamp}.json`);
    fs.writeFileSync(jsonPath, JSON.stringify(metrics, null, 2));
    console.log(`✓ JSON report: ${jsonPath}`);
    
    console.log('\n📊 Report generation complete!\n');
  }
}

if (require.main === module) {
  const generator = new ReportGenerator();
  generator.generate();
}

module.exports = ReportGenerator;
