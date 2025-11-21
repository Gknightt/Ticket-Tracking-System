#!/bin/bash

# ==============================================
# Production Deployment Script for DigitalOcean
# ==============================================

set -e

echo "🚀 Starting Production Deployment Setup for mapactive.tech"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root${NC}" 
   exit 1
fi

# 1. Update system packages
echo -e "${GREEN}📦 Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

# 2. Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo -e "${GREEN}🐳 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
else
    echo -e "${YELLOW}✓ Docker already installed${NC}"
fi

# 3. Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}📦 Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo -e "${YELLOW}✓ Docker Compose already installed${NC}"
fi

# 4. Create deployment directory
DEPLOY_DIR="/opt/ticket-tracking-system"
echo -e "${GREEN}📁 Creating deployment directory at ${DEPLOY_DIR}...${NC}"
mkdir -p ${DEPLOY_DIR}
cd ${DEPLOY_DIR}

# 5. Clone repository (if not already cloned)
if [ ! -d ".git" ]; then
    echo -e "${GREEN}📥 Cloning repository...${NC}"
    git clone https://github.com/Gknightt/Ticket-Tracking-System.git .
else
    echo -e "${YELLOW}✓ Repository already cloned${NC}"
    echo -e "${GREEN}📥 Pulling latest changes...${NC}"
    git pull
fi

# 6. Navigate to deployment directory
cd deployment

# 7. Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found!${NC}"
    echo -e "${YELLOW}Creating .env from example...${NC}"
    cp .env.production.example .env
    echo -e "${RED}❌ IMPORTANT: Edit the .env file with your actual values before continuing!${NC}"
    echo -e "${YELLOW}Edit: nano .env${NC}"
    echo ""
    echo -e "${YELLOW}Required changes:${NC}"
    echo "  - Set Cloudflare API credentials (CF_API_EMAIL, CF_DNS_API_TOKEN)"
    echo "  - Set strong passwords for all services"
    echo "  - Set JWT signing keys"
    echo "  - Configure email settings"
    echo ""
    read -p "Press enter when you've finished editing .env..."
fi

# 8. Create acme.json for SSL certificates
echo -e "${GREEN}🔒 Setting up SSL certificate storage...${NC}"
touch traefik/acme.json
chmod 600 traefik/acme.json

# 9. Setup Docker network
echo -e "${GREEN}🌐 Creating Docker network...${NC}"
docker network create traefik-public 2>/dev/null || echo -e "${YELLOW}✓ Network already exists${NC}"

# 10. Pull Docker images
echo -e "${GREEN}📥 Pulling Docker images...${NC}"
docker-compose -f docker-compose.production.yml pull

# 11. Build services
echo -e "${GREEN}🔨 Building services...${NC}"
docker-compose -f docker-compose.production.yml build --no-cache

# 12. Start services
echo -e "${GREEN}🚀 Starting services...${NC}"
docker-compose -f docker-compose.production.yml up -d

# 13. Wait for services to be healthy
echo -e "${GREEN}⏳ Waiting for services to become healthy...${NC}"
sleep 30

# 14. Run database migrations
echo -e "${GREEN}🗄️  Running database migrations...${NC}"
docker-compose -f docker-compose.production.yml exec -T auth-service python manage.py migrate
docker-compose -f docker-compose.production.yml exec -T workflow-api python manage.py migrate
docker-compose -f docker-compose.production.yml exec -T ticket-service python manage.py migrate
docker-compose -f docker-compose.production.yml exec -T messaging-service python manage.py migrate
docker-compose -f docker-compose.production.yml exec -T notification-service python manage.py migrate

# 15. Create superuser (optional)
echo -e "${YELLOW}⚠️  Would you like to create a superuser? (y/n)${NC}"
read -p "" create_superuser
if [ "$create_superuser" = "y" ] || [ "$create_superuser" = "Y" ]; then
    echo -e "${GREEN}👤 Creating superuser...${NC}"
    docker-compose -f docker-compose.production.yml exec auth-service python manage.py createsuperuser
fi

# 16. Display status
echo ""
echo -e "${GREEN}=================================================="
echo "✅ Deployment Complete!"
echo "==================================================${NC}"
echo ""
echo "🌐 Your services are now available at:"
echo "   Frontend:      https://mapactive.tech"
echo "   Auth:          https://auth.mapactive.tech"
echo "   Workflow:      https://workflow.mapactive.tech"
echo "   Tickets:       https://ticket.mapactive.tech"
echo "   Messaging:     https://messaging.mapactive.tech"
echo "   Notification:  https://notification.mapactive.tech"
echo "   RabbitMQ:      https://rabbitmq.mapactive.tech"
echo "   Traefik:       https://traefik.mapactive.tech"
echo ""
echo "📊 Useful commands:"
echo "   View logs:        docker-compose -f docker-compose.production.yml logs -f [service-name]"
echo "   Restart service:  docker-compose -f docker-compose.production.yml restart [service-name]"
echo "   Stop all:         docker-compose -f docker-compose.production.yml down"
echo "   Start all:        docker-compose -f docker-compose.production.yml up -d"
echo ""
echo -e "${YELLOW}⚠️  NOTE: It may take a few minutes for SSL certificates to be issued.${NC}"
echo -e "${YELLOW}    Monitor Traefik logs: docker-compose logs -f traefik${NC}"
echo ""
