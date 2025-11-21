#!/bin/bash

# ==============================================
# Service Health Monitoring Script
# ==============================================

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Ticket Tracking System - Health Monitor    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose not found${NC}"
    exit 1
fi

cd "$(dirname "$0")/.."

# Function to check if a service is running
check_service() {
    local service=$1
    local status=$(docker-compose -f docker-compose.production.yml ps -q ${service} 2>/dev/null)
    
    if [ -z "$status" ]; then
        echo -e "${RED}● ${service}: DOWN${NC}"
        return 1
    else
        local health=$(docker inspect --format='{{.State.Status}}' ${service} 2>/dev/null)
        if [ "$health" = "running" ]; then
            echo -e "${GREEN}● ${service}: UP${NC}"
            return 0
        else
            echo -e "${YELLOW}● ${service}: STARTING${NC}"
            return 2
        fi
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 ${url} 2>/dev/null)
    
    if [ "$response" -ge 200 ] && [ "$response" -lt 400 ]; then
        echo -e "${GREEN}✓ ${name}: ${response}${NC}"
    elif [ "$response" -ge 400 ] && [ "$response" -lt 500 ]; then
        echo -e "${YELLOW}⚠ ${name}: ${response}${NC}"
    else
        echo -e "${RED}✗ ${name}: No response${NC}"
    fi
}

# Check Docker services
echo -e "${BLUE}═══ Docker Services ═══${NC}"
services=("traefik" "postgres" "rabbitmq" "auth-service" "workflow-api" "workflow-worker" "ticket-service" "messaging-service" "notification-service" "notification-worker" "frontend")

for service in "${services[@]}"; do
    check_service ${service}
done

echo ""

# Check HTTP endpoints
echo -e "${BLUE}═══ HTTP Endpoints ═══${NC}"
check_endpoint "Frontend        " "https://mapactive.tech"
check_endpoint "Auth Service    " "https://auth.mapactive.tech/health/"
check_endpoint "Workflow API    " "https://workflow.mapactive.tech/health/"
check_endpoint "Ticket Service  " "https://ticket.mapactive.tech/health/"
check_endpoint "Messaging       " "https://messaging.mapactive.tech/health/"
check_endpoint "Notification    " "https://notification.mapactive.tech/health/"
check_endpoint "RabbitMQ UI     " "https://rabbitmq.mapactive.tech"

echo ""

# Check SSL certificates
echo -e "${BLUE}═══ SSL Certificates ═══${NC}"
if [ -f "traefik/acme.json" ]; then
    cert_count=$(cat traefik/acme.json | grep -o '"domain"' | wc -l)
    if [ "$cert_count" -gt 0 ]; then
        echo -e "${GREEN}✓ SSL Certificates: ${cert_count} domains configured${NC}"
    else
        echo -e "${RED}✗ SSL Certificates: No certificates found${NC}"
    fi
else
    echo -e "${RED}✗ SSL Certificates: acme.json not found${NC}"
fi

echo ""

# Check disk usage
echo -e "${BLUE}═══ Disk Usage ═══${NC}"
echo "Docker volumes:"
docker system df -v | grep -A 20 "Local Volumes" | tail -n +3 | head -n 10

echo ""

# Check database connections
echo -e "${BLUE}═══ Database Status ═══${NC}"
db_status=$(docker-compose -f docker-compose.production.yml exec -T postgres pg_isready -U ${POSTGRES_USER:-postgres} 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PostgreSQL: Ready${NC}"
    
    # Get database sizes
    docker-compose -f docker-compose.production.yml exec -T postgres psql -U ${POSTGRES_USER:-postgres} -c "\l+" 2>/dev/null | grep -E "auth_db|workflow_db|ticket_db|messaging_db|notification_db" | while read -r line; do
        db=$(echo $line | awk '{print $1}')
        size=$(echo $line | awk '{print $7" "$8}')
        echo "  - ${db}: ${size}"
    done
else
    echo -e "${RED}✗ PostgreSQL: Not ready${NC}"
fi

echo ""

# Check RabbitMQ queues
echo -e "${BLUE}═══ RabbitMQ Queues ═══${NC}"
rabbitmq_queues=$(docker-compose -f docker-compose.production.yml exec -T rabbitmq rabbitmqctl list_queues name messages 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ RabbitMQ: Connected${NC}"
    echo "$rabbitmq_queues" | tail -n +2 | while read -r queue messages; do
        if [ ! -z "$queue" ]; then
            if [ "$messages" -gt 100 ]; then
                echo -e "  ${RED}⚠ ${queue}: ${messages} messages${NC}"
            elif [ "$messages" -gt 0 ]; then
                echo -e "  ${YELLOW}- ${queue}: ${messages} messages${NC}"
            else
                echo -e "  ${GREEN}✓ ${queue}: ${messages} messages${NC}"
            fi
        fi
    done
else
    echo -e "${RED}✗ RabbitMQ: Cannot connect${NC}"
fi

echo ""

# Check container logs for errors
echo -e "${BLUE}═══ Recent Errors (Last 5 minutes) ═══${NC}"
error_count=$(docker-compose -f docker-compose.production.yml logs --since 5m 2>&1 | grep -i -c "error\|exception\|failed")
if [ "$error_count" -gt 0 ]; then
    echo -e "${RED}⚠ Found ${error_count} errors in logs${NC}"
    echo "  Run: docker-compose -f docker-compose.production.yml logs --since 5m | grep -i error"
else
    echo -e "${GREEN}✓ No errors in recent logs${NC}"
fi

echo ""

# System resources
echo -e "${BLUE}═══ System Resources ═══${NC}"
echo "Memory Usage:"
free -h | grep -E "Mem|Swap"
echo ""
echo "CPU Load:"
uptime
echo ""
echo "Docker Stats (Top 5 containers by memory):"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -n 6

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}Health check complete - $(date)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""
