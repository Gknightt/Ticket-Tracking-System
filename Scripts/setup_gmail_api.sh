#!/bin/bash

# Gmail API Setup Script for Notification Service
# This script helps set up the Gmail API integration

set -e

echo "=========================================="
echo "Gmail API Setup Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "notification_service" ]; then
    echo -e "${RED}Error: notification_service directory not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo -e "${YELLOW}Step 1: Check for credentials.json${NC}"
if [ -f "notification_service/credentials.json" ]; then
    echo -e "${GREEN}✓ credentials.json found${NC}"
else
    echo -e "${RED}✗ credentials.json NOT found${NC}"
    echo ""
    echo "Please follow these steps:"
    echo "1. Go to https://console.cloud.google.com/"
    echo "2. Create a service account with Gmail API access"
    echo "3. Download the JSON credentials file"
    echo "4. Copy it to: notification_service/credentials.json"
    echo ""
    read -p "Press Enter after you've added credentials.json to continue..."
    
    if [ ! -f "notification_service/credentials.json" ]; then
        echo -e "${RED}Error: credentials.json still not found. Exiting.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ credentials.json found${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Update .env file${NC}"
cd notification_service

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created${NC}"
    else
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Check if Gmail settings are configured
if grep -q "GMAIL_CREDENTIALS_PATH=credentials.json" .env; then
    echo -e "${GREEN}✓ Gmail configuration found in .env${NC}"
else
    echo -e "${YELLOW}! Adding Gmail configuration to .env${NC}"
    echo "" >> .env
    echo "# Gmail API Configuration" >> .env
    echo "GMAIL_CREDENTIALS_PATH=credentials.json" >> .env
    echo "GMAIL_SENDER_EMAIL=" >> .env
fi

echo ""
echo -e "${YELLOW}Please update the following in notification_service/.env:${NC}"
echo "  - GMAIL_SENDER_EMAIL=your-email@gmail.com"
echo "  - DJANGO_DEFAULT_FROM_EMAIL=noreply@yourdomain.com"
echo ""
read -p "Press Enter after updating .env to continue..."

echo ""
echo -e "${YELLOW}Step 3: Install Python dependencies${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 4: Run migrations${NC}"
python manage.py migrate
echo -e "${GREEN}✓ Migrations complete${NC}"

echo ""
echo -e "${YELLOW}Step 5: Check Celery configuration${NC}"
cd ..

if [ -f "auth/.env" ]; then
    if grep -q "DJANGO_CELERY_BROKER_URL" auth/.env; then
        echo -e "${GREEN}✓ Celery broker configured in auth service${NC}"
    else
        echo -e "${YELLOW}! Add DJANGO_CELERY_BROKER_URL to auth/.env${NC}"
    fi
else
    echo -e "${YELLOW}! auth/.env not found${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Start RabbitMQ (if not already running):"
echo "   sudo systemctl start rabbitmq-server"
echo ""
echo "2. Start Celery worker for notification service:"
echo "   cd notification_service"
echo "   celery -A notification_service worker --pool=solo --loglevel=info -Q NOTIFICATION_TASKS,inapp-notification-queue"
echo ""
echo "3. Test the setup:"
echo "   python manage.py shell"
echo "   >>> from notifications.gmail_service import get_gmail_service"
echo "   >>> gmail = get_gmail_service()"
echo "   >>> gmail.send_email('test@example.com', 'Test', 'This is a test')"
echo ""
echo "4. Review the migration guide:"
echo "   cat ../GMAIL_API_MIGRATION.md"
echo ""
