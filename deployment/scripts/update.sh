#!/bin/bash

# ==============================================
# Update Script for Production Deployment
# ==============================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Application Update Script                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root${NC}" 
   exit 1
fi

cd "$(dirname "$0")/.."

# 1. Backup before update
echo -e "${YELLOW}⚠️  Creating backup before update...${NC}"
./scripts/backup.sh

# 2. Pull latest changes
echo -e "${GREEN}📥 Pulling latest changes from repository...${NC}"
git fetch origin
git pull origin main

# 3. Check for .env changes
echo -e "${GREEN}🔍 Checking for environment variable changes...${NC}"
if [ -f ".env.production.example" ]; then
    # Show new variables that might need to be added
    echo -e "${YELLOW}Review .env.production.example for any new variables${NC}"
fi

# 4. Build new images
echo -e "${GREEN}🔨 Building new Docker images...${NC}"
docker-compose -f docker-compose.production.yml build --no-cache

# 5. Stop services (with warning)
echo -e "${YELLOW}⚠️  Stopping services for update...${NC}"
docker-compose -f docker-compose.production.yml down

# 6. Start services with new images
echo -e "${GREEN}🚀 Starting services with updated images...${NC}"
docker-compose -f docker-compose.production.yml up -d

# 7. Wait for services to be ready
echo -e "${GREEN}⏳ Waiting for services to become healthy...${NC}"
sleep 30

# 8. Run database migrations
echo -e "${GREEN}🗄️  Running database migrations...${NC}"
docker-compose -f docker-compose.production.yml exec -T auth-service python manage.py migrate
docker-compose -f docker-compose.production.yml exec -T workflow-api python manage.py migrate
docker-compose -f docker-compose.production.yml exec -T ticket-service python manage.py migrate
docker-compose -f docker-compose.production.yml exec -T messaging-service python manage.py migrate
docker-compose -f docker-compose.production.yml exec -T notification-service python manage.py migrate

# 9. Collect static files (if needed)
echo -e "${GREEN}📦 Collecting static files...${NC}"
docker-compose -f docker-compose.production.yml exec -T auth-service python manage.py collectstatic --noinput || true
docker-compose -f docker-compose.production.yml exec -T workflow-api python manage.py collectstatic --noinput || true

# 10. Clean up old images
echo -e "${GREEN}🗑️  Cleaning up old Docker images...${NC}"
docker image prune -f

# 11. Display status
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Update Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.production.yml ps
echo ""
echo "🔍 Running health check..."
./scripts/monitor.sh
echo ""
echo -e "${YELLOW}⚠️  Please monitor logs for any issues:${NC}"
echo "   docker-compose -f docker-compose.production.yml logs -f"
echo ""
