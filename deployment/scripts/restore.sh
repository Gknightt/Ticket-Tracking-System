#!/bin/bash

# ==============================================
# Restore Script for Production Deployment
# ==============================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKUP_DIR="/opt/backups/ticket-tracking-system"

if [ $# -eq 0 ]; then
    echo -e "${RED}❌ No backup timestamp provided!${NC}"
    echo "Usage: ./restore.sh TIMESTAMP"
    echo ""
    echo "Available backups:"
    ls -1 ${BACKUP_DIR}/postgres_all_*.sql.gz | sed 's/.*postgres_all_\(.*\).sql.gz/\1/'
    exit 1
fi

TIMESTAMP=$1

echo -e "${YELLOW}⚠️  WARNING: This will restore data from backup!${NC}"
echo "   Timestamp: ${TIMESTAMP}"
echo "   This will OVERWRITE current data!"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Load environment variables
if [ -f "../.env" ]; then
    source ../.env
else
    echo -e "${RED}❌ .env file not found!${NC}"
    exit 1
fi

echo "🔄 Starting restore process..."
echo "======================================"

# Stop all services
echo -e "${YELLOW}⏸️  Stopping all services...${NC}"
cd ..
docker-compose -f docker-compose.production.yml down

# Restore PostgreSQL databases
echo -e "${GREEN}📥 Restoring PostgreSQL databases...${NC}"
if [ -f "${BACKUP_DIR}/postgres_all_${TIMESTAMP}.sql.gz" ]; then
    gunzip -c ${BACKUP_DIR}/postgres_all_${TIMESTAMP}.sql.gz | docker-compose -f docker-compose.production.yml exec -T postgres psql -U ${POSTGRES_USER}
    echo -e "${GREEN}✓ Database restore completed${NC}"
else
    echo -e "${RED}❌ Backup file not found: ${BACKUP_DIR}/postgres_all_${TIMESTAMP}.sql.gz${NC}"
    exit 1
fi

# Restore RabbitMQ data
echo -e "${GREEN}📥 Restoring RabbitMQ data...${NC}"
if [ -f "${BACKUP_DIR}/rabbitmq_data_${TIMESTAMP}.tar.gz" ]; then
    docker run --rm \
        -v $(pwd)/deployment_rabbitmq_data:/volume \
        -v ${BACKUP_DIR}:/backup \
        alpine sh -c "rm -rf /volume/* && tar xzf /backup/rabbitmq_data_${TIMESTAMP}.tar.gz -C /volume"
    echo -e "${GREEN}✓ RabbitMQ data restored${NC}"
fi

# Restore media files
echo -e "${GREEN}📥 Restoring media files...${NC}"

if [ -f "${BACKUP_DIR}/auth_media_${TIMESTAMP}.tar.gz" ]; then
    docker run --rm \
        -v $(pwd)/deployment_auth_media:/volume \
        -v ${BACKUP_DIR}:/backup \
        alpine sh -c "rm -rf /volume/* && tar xzf /backup/auth_media_${TIMESTAMP}.tar.gz -C /volume"
fi

if [ -f "${BACKUP_DIR}/ticket_media_${TIMESTAMP}.tar.gz" ]; then
    docker run --rm \
        -v $(pwd)/deployment_ticket_media:/volume \
        -v ${BACKUP_DIR}:/backup \
        alpine sh -c "rm -rf /volume/* && tar xzf /backup/ticket_media_${TIMESTAMP}.tar.gz -C /volume"
fi

if [ -f "${BACKUP_DIR}/workflow_media_${TIMESTAMP}.tar.gz" ]; then
    docker run --rm \
        -v $(pwd)/deployment_workflow_media:/volume \
        -v ${BACKUP_DIR}:/backup \
        alpine sh -c "rm -rf /volume/* && tar xzf /backup/workflow_media_${TIMESTAMP}.tar.gz -C /volume"
fi

echo -e "${GREEN}✓ Media files restored${NC}"

# Restore configuration files
echo -e "${GREEN}📥 Restoring configuration files...${NC}"
if [ -f "${BACKUP_DIR}/config_${TIMESTAMP}.tar.gz" ]; then
    tar xzf ${BACKUP_DIR}/config_${TIMESTAMP}.tar.gz -C deployment/
    echo -e "${GREEN}✓ Configuration files restored${NC}"
fi

# Start services
echo -e "${GREEN}🚀 Starting services...${NC}"
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be ready
echo -e "${GREEN}⏳ Waiting for services to become healthy...${NC}"
sleep 30

echo ""
echo -e "${GREEN}======================================"
echo "✅ Restore completed successfully!"
echo "======================================${NC}"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.production.yml ps
echo ""
echo -e "${YELLOW}⚠️  Please verify that all services are running correctly${NC}"
echo ""
