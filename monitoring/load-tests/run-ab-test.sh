#!/bin/bash

# Apache Bench Load Testing Script
# Usage: ./run-ab-test.sh [url] [requests] [concurrency]

URL=${1:-"http://localhost:8000/api/tickets"}
REQUESTS=${2:-1000}
CONCURRENCY=${3:-10}

echo "=========================================="
echo "Apache Bench Load Test"
echo "=========================================="
echo "URL: $URL"
echo "Total Requests: $REQUESTS"
echo "Concurrency: $CONCURRENCY"
echo "=========================================="
echo ""

# Check if ab is installed
if ! command -v ab &> /dev/null; then
    echo "Apache Bench (ab) is not installed."
    echo "Install with: sudo apt-get install apache2-utils"
    exit 1
fi

# Run the test
ab -n $REQUESTS -c $CONCURRENCY -g results.tsv "$URL"

# Parse results
echo ""
echo "=========================================="
echo "Quick Summary"
echo "=========================================="
grep "Requests per second" results.log 2>/dev/null || echo "Results logged to console"
grep "Time per request" results.log 2>/dev/null || echo ""

echo ""
echo "Detailed results saved to results.tsv"
echo "Run 'npm run metrics:analyze' to see full analysis"
