#!/bin/bash
# Quick Setup Script for Push Notifications
# Run this after creating your VAPID keys

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Push Notifications Setup${NC}"
echo "========================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    touch .env
fi

# Check if VAPID keys are set
if grep -q "PUSH_VAPID_PUBLIC_KEY" .env; then
    echo -e "${GREEN}✓ VAPID keys already configured${NC}"
else
    echo -e "${YELLOW}VAPID keys not found. Generate them with:${NC}"
    echo "  python -c \"from pywebpush import generate_vapid_keys; keys = generate_vapid_keys(); print(f'Public: {keys[\\\"public_key\\\"]}'); print(f'Private: {keys[\\\"private_key\\\"]}')\""
    echo ""
    echo -e "${YELLOW}Then add to .env:${NC}"
    echo "  PUSH_VAPID_PUBLIC_KEY=<your_public_key>"
    echo "  PUSH_VAPID_PRIVATE_KEY=<your_private_key>"
    echo "  PUSH_VAPID_EMAIL=your-email@example.com"
    echo ""
fi

echo -e "${YELLOW}Setting up Push Notifications...${NC}"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install pywebpush cryptography
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Run migrations
echo "Running database migrations..."
python manage.py makemigrations nogoff
python manage.py migrate
echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo -e "${GREEN}✓ Static files collected${NC}"
echo ""

echo -e "${GREEN}✓ Push notifications setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Add notification icons to /nogoff/static/images/"
echo "   - icon.png (192x192)"
echo "   - badge.png (72x72)"
echo ""
echo "2. Test by visiting the app and allowing notifications"
echo ""
echo "3. Send a test notification:"
echo "   python manage.py send_push_notification --title 'Test' --body 'Hello!'"
echo ""
echo -e "${YELLOW}For more information, see PUSH_NOTIFICATIONS_GUIDE.md${NC}"
