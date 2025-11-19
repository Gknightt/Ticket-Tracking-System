# Performance Monitoring Suite

This directory contains tools and configurations for monitoring the Ticket Tracking System's performance, collecting real metrics, and conducting load tests.

## Directory Structure

```
monitoring/
├── middleware/          # Express/Django middleware for request tracking
├── load-tests/         # Load testing configurations (Artillery, Apache Bench)
├── database/           # Database performance queries and monitoring
├── metrics/            # Metrics collection and reporting scripts
├── docker/             # Docker container resource monitoring
└── README.md           # This file
```

## Quick Start

### 1. Install Dependencies
```bash
cd monitoring
npm install
pip install -r requirements.txt
```

### 2. Run Load Tests
```bash
# Artillery load test
npm run load-test

# Apache Bench simple test
./load-tests/run-ab-test.sh
```

### 3. Monitor Real-time Performance
```bash
# Start metrics collector
npm run metrics:collect

# Monitor Docker resources
./docker/monitor.sh
```

### 4. Generate Performance Report
```bash
npm run report:generate
```

## Features

- **Response Time Tracking**: Automatic logging of all API endpoints
- **Load Testing**: Configurable scenarios for stress testing
- **Database Monitoring**: Query performance and table statistics
- **Resource Monitoring**: CPU, Memory, Network, Disk I/O
- **Automated Reports**: Generate performance reports from real data

## Integration

See individual README files in each subdirectory for integration instructions.
