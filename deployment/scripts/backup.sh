#!/bin/bash

# ==============================================
# Backup Script for Production Deployment
# ==============================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKUP_DIR="/opt/backups/ticket-tracking-system"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Load environment variables
if [ -f "../.env" ]; then
    source ../.env
else
    echo -e "${RED}❌ .env file not found!${NC}"
    exit 1
fi

echo "🔄 Starting backup process..."
echo "======================================"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Backup PostgreSQL databases
echo -e "${GREEN}📦 Backing up PostgreSQL databases...${NC}"
docker-compose -f ../docker-compose.production.yml exec -T postgres pg_dumpall -U ${POSTGRES_USER} | gzip > ${BACKUP_DIR}/postgres_all_${TIMESTAMP}.sql.gz
echo -e "${GREEN}✓ Database backup completed${NC}"

# Backup individual databases for easier restoration
databases=("auth_db" "workflow_db" "workflowmanagement" "ticket_db" "messaging_db" "notification_db" "notificationservice")
for db in "${databases[@]}"; do
    echo -e "${GREEN}📦 Backing up $db...${NC}"
    docker-compose -f ../docker-compose.production.yml exec -T postgres pg_dump -U ${POSTGRES_USER} ${db} | gzip > ${BACKUP_DIR}/${db}_${TIMESTAMP}.sql.gz
done

# Backup Docker volumes
echo -e "${GREEN}📦 Backing up Docker volumes...${NC}"
cd ..
docker run --rm \
    -v $(pwd)/deployment_rabbitmq_data:/volume \
    -v ${BACKUP_DIR}:/backup \
    alpine tar czf /backup/rabbitmq_data_${TIMESTAMP}.tar.gz -C /volume ./

docker run --rm \
    -v $(pwd)/deployment_auth_media:/volume \
    -v ${BACKUP_DIR}:/backup \
    alpine tar czf /backup/auth_media_${TIMESTAMP}.tar.gz -C /volume ./

docker run --rm \
    -v $(pwd)/deployment_ticket_media:/volume \
    -v ${BACKUP_DIR}:/backup \
    alpine tar czf /backup/ticket_media_${TIMESTAMP}.tar.gz -C /volume ./

docker run --rm \
    -v $(pwd)/deployment_workflow_media:/volume \
    -v ${BACKUP_DIR}:/backup \
    alpine tar czf /backup/workflow_media_${TIMESTAMP}.tar.gz -C /volume ./

echo -e "${GREEN}✓ Volume backup completed${NC}"

# Backup configuration files
echo -e "${GREEN}📦 Backing up configuration files...${NC}"
tar czf ${BACKUP_DIR}/config_${TIMESTAMP}.tar.gz \
    .env \
    docker-compose.production.yml \
    traefik/traefik.yml \
    traefik/config.yml

echo -e "${GREEN}✓ Configuration backup completed${NC}"

# Clean up old backups
echo -e "${GREEN}🗑️  Cleaning up backups older than ${RETENTION_DAYS} days...${NC}"
find ${BACKUP_DIR} -name "*.gz" -mtime +${RETENTION_DAYS} -delete
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete

# Create backup manifest
cat > ${BACKUP_DIR}/manifest_${TIMESTAMP}.txt <<EOF
Backup created: $(date)
Backup directory: ${BACKUP_DIR}
Timestamp: ${TIMESTAMP}

Files included:
- postgres_all_${TIMESTAMP}.sql.gz (Full database dump)
- Individual database dumps for each service
- rabbitmq_data_${TIMESTAMP}.tar.gz (RabbitMQ data)
- auth_media_${TIMESTAMP}.tar.gz (Auth service media files)
- ticket_media_${TIMESTAMP}.tar.gz (Ticket service media files)
- workflow_media_${TIMESTAMP}.tar.gz (Workflow service media files)
- config_${TIMESTAMP}.tar.gz (Configuration files)

Restore instructions:
1. Stop all services: docker-compose -f docker-compose.production.yml down
2. Restore database: gunzip -c postgres_all_${TIMESTAMP}.sql.gz | docker-compose -f docker-compose.production.yml exec -T postgres psql -U ${POSTGRES_USER}
3. Restore volumes using docker run commands
4. Start services: docker-compose -f docker-compose.production.yml up -d
EOF

# Display backup summary
echo ""
echo -e "${GREEN}======================================"
echo "✅ Backup completed successfully!"
echo "======================================${NC}"
echo ""
echo "📊 Backup Summary:"
echo "   Location: ${BACKUP_DIR}"
echo "   Timestamp: ${TIMESTAMP}"
echo ""
ls -lh ${BACKUP_DIR}/*${TIMESTAMP}*
echo ""
echo -e "${YELLOW}💾 Total backup size: $(du -sh ${BACKUP_DIR} | cut -f1)${NC}"
echo ""
echo "📝 Manifest file: ${BACKUP_DIR}/manifest_${TIMESTAMP}.txt"
echo ""
