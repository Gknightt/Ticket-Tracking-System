#!/bin/bash

# Comprehensive Load Testing Suite
# Runs multiple test scenarios and generates reports

echo "=========================================="
echo "Ticket Tracking System - Load Test Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if services are running
echo "Checking if services are running..."
if ! curl -s http://localhost:8000/api/health > /dev/null; then
    echo -e "${RED}Error: Backend service not responding${NC}"
    echo "Please start the services first"
    exit 1
fi

echo -e "${GREEN}Services are running${NC}"
echo ""

# 1. Smoke Test
echo -e "${YELLOW}[1/3] Running smoke test...${NC}"
npm run load-test:smoke
echo ""

# 2. Load Test
echo -e "${YELLOW}[2/3] Running standard load test...${NC}"
npm run load-test
echo ""

# 3. Stress Test (optional, prompt user)
read -p "Run stress test? This may take 10+ minutes (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}[3/3] Running stress test...${NC}"
    npm run load-test:stress
else
    echo -e "${YELLOW}[3/3] Skipping stress test${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Load tests completed!"
echo "==========================================${NC}"
echo ""
echo "Generate report with: npm run report:generate"
