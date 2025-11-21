#!/bin/bash

# ==============================================
# SSL Certificate Setup Script
# ==============================================

set -e

echo "🔒 SSL Certificate Setup for mapactive.tech"
echo "============================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if .env exists
if [ ! -f "../.env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create .env file from .env.production.example"
    exit 1
fi

# Load environment variables
source ../.env

# Verify Cloudflare credentials
if [ -z "$CF_API_EMAIL" ] || [ -z "$CF_DNS_API_TOKEN" ]; then
    echo -e "${RED}❌ Cloudflare credentials not set in .env file!${NC}"
    echo "Please set CF_API_EMAIL and CF_DNS_API_TOKEN"
    exit 1
fi

echo -e "${GREEN}✓ Cloudflare credentials found${NC}"

# Check DNS records
echo ""
echo -e "${YELLOW}📋 Checking DNS records for mapactive.tech...${NC}"
echo ""
echo "Please ensure the following DNS records exist in Cloudflare:"
echo ""
echo "  Type  | Name         | Content (Target)"
echo "  ------|--------------|-------------------"
echo "  A     | @            | YOUR_SERVER_IP"
echo "  A     | www          | YOUR_SERVER_IP"
echo "  A     | auth         | YOUR_SERVER_IP"
echo "  A     | workflow     | YOUR_SERVER_IP"
echo "  A     | ticket       | YOUR_SERVER_IP"
echo "  A     | messaging    | YOUR_SERVER_IP"
echo "  A     | notification | YOUR_SERVER_IP"
echo "  A     | rabbitmq     | YOUR_SERVER_IP"
echo "  A     | traefik      | YOUR_SERVER_IP"
echo ""
echo -e "${YELLOW}⚠️  Set Proxy status to 'DNS only' (grey cloud) during initial setup${NC}"
echo ""

read -p "Have you configured all DNS records? (y/n) " dns_ready

if [ "$dns_ready" != "y" ] && [ "$dns_ready" != "Y" ]; then
    echo -e "${YELLOW}Please configure DNS records and run this script again.${NC}"
    exit 0
fi

# Check acme.json permissions
echo ""
echo -e "${GREEN}🔧 Configuring acme.json permissions...${NC}"
if [ ! -f "../traefik/acme.json" ]; then
    touch ../traefik/acme.json
fi
chmod 600 ../traefik/acme.json
echo -e "${GREEN}✓ acme.json configured${NC}"

# Update Traefik config with email
echo ""
echo -e "${GREEN}📧 Updating Traefik configuration with your email...${NC}"
sed -i "s/your-email@example.com/$CF_API_EMAIL/g" ../traefik/traefik.yml
echo -e "${GREEN}✓ Email configured in traefik.yml${NC}"

# Test DNS resolution
echo ""
echo -e "${GREEN}🔍 Testing DNS resolution...${NC}"
domains=("mapactive.tech" "auth.mapactive.tech" "workflow.mapactive.tech" "ticket.mapactive.tech")

for domain in "${domains[@]}"; do
    if nslookup $domain > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $domain resolves correctly${NC}"
    else
        echo -e "${RED}❌ $domain does not resolve${NC}"
        echo -e "${YELLOW}   Please check your DNS configuration${NC}"
    fi
done

# Instructions
echo ""
echo -e "${GREEN}=================================================="
echo "✅ SSL Setup Complete!"
echo "==================================================${NC}"
echo ""
echo "📝 Next steps:"
echo "   1. Ensure all DNS records are properly configured"
echo "   2. Wait 5-10 minutes for DNS propagation"
echo "   3. Run the deployment script: ./deploy.sh"
echo "   4. Monitor Traefik logs: docker-compose logs -f traefik"
echo ""
echo -e "${YELLOW}⚠️  SSL certificates will be automatically requested when services start${NC}"
echo ""
echo "📊 To check certificate status:"
echo "   docker-compose -f ../docker-compose.production.yml logs traefik | grep acme"
echo ""
echo "🔧 Troubleshooting:"
echo "   - If certificates fail to issue, check Cloudflare API token permissions"
echo "   - Ensure API token has 'Zone:DNS:Edit' permission"
echo "   - Check rate limits: Let's Encrypt has 5 failures per hour limit"
echo ""
