#!/bin/bash

# ==============================================
# Docker Compose Configuration Validator
# ==============================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Docker Compose Configuration Validator     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

cd "$(dirname "$0")/.."

# Check if docker-compose file exists
if [ ! -f "docker-compose.production.yml" ]; then
    echo -e "${RED}❌ docker-compose.production.yml not found!${NC}"
    exit 1
fi

# Validate docker-compose syntax
echo -e "${GREEN}🔍 Validating docker-compose syntax...${NC}"
if docker-compose -f docker-compose.production.yml config > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker Compose syntax is valid${NC}"
else
    echo -e "${RED}❌ Docker Compose syntax error!${NC}"
    docker-compose -f docker-compose.production.yml config
    exit 1
fi

# Check for .env file
echo ""
echo -e "${GREEN}🔍 Checking environment configuration...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
    
    # Check for required variables
    required_vars=(
        "CF_API_EMAIL"
        "CF_DNS_API_TOKEN"
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
        "RABBITMQ_USER"
        "RABBITMQ_PASSWORD"
        "JWT_SIGNING_KEY"
        "AUTH_SECRET_KEY"
        "WORKFLOW_SECRET_KEY"
        "TICKET_SECRET_KEY"
        "MESSAGING_SECRET_KEY"
        "NOTIFICATION_SECRET_KEY"
        "EMAIL_HOST"
        "EMAIL_HOST_USER"
        "EMAIL_HOST_PASSWORD"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        echo -e "${GREEN}✓ All required variables are present${NC}"
    else
        echo -e "${RED}❌ Missing required variables:${NC}"
        for var in "${missing_vars[@]}"; do
            echo -e "   - ${var}"
        done
        exit 1
    fi
    
    # Check for default passwords
    echo ""
    echo -e "${YELLOW}⚠️  Checking for default/weak passwords...${NC}"
    weak_patterns=("change-this" "password" "123456" "admin" "secret")
    found_weak=false
    
    for pattern in "${weak_patterns[@]}"; do
        if grep -i "${pattern}" .env > /dev/null 2>&1; then
            echo -e "${RED}⚠️  Found potential weak password containing: ${pattern}${NC}"
            found_weak=true
        fi
    done
    
    if [ "$found_weak" = false ]; then
        echo -e "${GREEN}✓ No obvious weak passwords found${NC}"
    else
        echo -e "${YELLOW}   Please use strong, random passwords in production!${NC}"
    fi
    
else
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "   Create it from: .env.production.example"
    exit 1
fi

# Check Traefik configuration
echo ""
echo -e "${GREEN}🔍 Checking Traefik configuration...${NC}"
if [ -f "traefik/traefik.yml" ]; then
    echo -e "${GREEN}✓ traefik.yml exists${NC}"
else
    echo -e "${RED}❌ traefik/traefik.yml not found!${NC}"
    exit 1
fi

if [ -f "traefik/config.yml" ]; then
    echo -e "${GREEN}✓ config.yml exists${NC}"
else
    echo -e "${RED}❌ traefik/config.yml not found!${NC}"
    exit 1
fi

# Check if acme.json exists and has correct permissions
if [ -f "traefik/acme.json" ]; then
    perms=$(stat -c "%a" traefik/acme.json)
    if [ "$perms" = "600" ]; then
        echo -e "${GREEN}✓ acme.json has correct permissions (600)${NC}"
    else
        echo -e "${YELLOW}⚠️  acme.json permissions are ${perms}, should be 600${NC}"
        echo "   Fix with: chmod 600 traefik/acme.json"
    fi
else
    echo -e "${YELLOW}⚠️  acme.json not found (will be created on first run)${NC}"
fi

# Check database init script
echo ""
echo -e "${GREEN}🔍 Checking database initialization...${NC}"
if [ -f "db-init/init-databases.sh" ]; then
    echo -e "${GREEN}✓ Database init script exists${NC}"
else
    echo -e "${RED}❌ db-init/init-databases.sh not found!${NC}"
    exit 1
fi

# Verify Docker is installed
echo ""
echo -e "${GREEN}🔍 Checking Docker installation...${NC}"
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo -e "${GREEN}✓ Docker installed: ${docker_version}${NC}"
else
    echo -e "${RED}❌ Docker not installed!${NC}"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    compose_version=$(docker-compose --version)
    echo -e "${GREEN}✓ Docker Compose installed: ${compose_version}${NC}"
else
    echo -e "${RED}❌ Docker Compose not installed!${NC}"
    exit 1
fi

# Check if Docker daemon is running
if docker ps > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker daemon is running${NC}"
else
    echo -e "${RED}❌ Docker daemon is not running!${NC}"
    exit 1
fi

# Check network
echo ""
echo -e "${GREEN}🔍 Checking Docker network...${NC}"
if docker network ls | grep -q "traefik-public"; then
    echo -e "${GREEN}✓ traefik-public network exists${NC}"
else
    echo -e "${YELLOW}⚠️  traefik-public network doesn't exist${NC}"
    echo "   It will be created automatically or run: docker network create traefik-public"
fi

# Check for port conflicts
echo ""
echo -e "${GREEN}🔍 Checking for port conflicts...${NC}"
ports=(80 443)
conflicts=false

for port in "${ports[@]}"; do
    if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}⚠️  Port ${port} is already in use${NC}"
        lsof -Pi :${port} -sTCP:LISTEN | tail -n +2
        conflicts=true
    else
        echo -e "${GREEN}✓ Port ${port} is available${NC}"
    fi
done

if [ "$conflicts" = true ]; then
    echo -e "${YELLOW}   Warning: Port conflicts detected. Services may fail to start.${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Configuration validation complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""
echo "📋 Summary:"
echo "   - Docker Compose syntax: Valid"
echo "   - Environment file: Present"
echo "   - Traefik config: Present"
echo "   - Database init: Present"
echo "   - Docker: Installed & Running"
echo ""
echo "🚀 Ready to deploy!"
echo ""
echo "Next steps:"
echo "   1. Review .env file for any remaining placeholders"
echo "   2. Ensure DNS records are configured"
echo "   3. Run: docker-compose -f docker-compose.production.yml up -d"
echo ""
