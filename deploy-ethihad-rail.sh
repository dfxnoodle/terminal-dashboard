#!/bin/bash

# Deployment script for ethihad-rail-dashboard.linus.services
# This script automates the complete deployment process with HTTPS

set -e

DOMAIN="ethihad-rail-dashboard.linus.services"
PROJECT_DIR="/media/dinochlai/Data/terminal-dashboard"

echo "🚀 Deploying Terminal Dashboard to $DOMAIN"
echo "=============================================="

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    SUDO=""
else
    SUDO="sudo"
fi

# 1. Update system packages
echo "📦 Updating system packages..."
$SUDO apt update

# 2. Install required packages
echo "📦 Installing nginx and certbot..."
$SUDO apt install -y nginx certbot python3-certbot-nginx

# 3. Build the application
echo "🏗️  Building application for production..."
cd "$PROJECT_DIR"
./build-production.sh

# 4. Configure nginx
echo "🔧 Configuring nginx..."
$SUDO cp nginx-production.conf /etc/nginx/sites-available/terminal-dashboard

# Remove default nginx site if it exists
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    $SUDO rm -f /etc/nginx/sites-enabled/default
fi

# Enable our site
$SUDO ln -sf /etc/nginx/sites-available/terminal-dashboard /etc/nginx/sites-enabled/

# Test nginx configuration
echo "🔍 Testing nginx configuration..."
$SUDO nginx -t

# 5. Start nginx
echo "🌐 Starting nginx..."
$SUDO systemctl enable nginx
$SUDO systemctl restart nginx

# 6. Check if DNS is configured
echo "🔍 Checking DNS configuration..."
if ! nslookup "$DOMAIN" >/dev/null 2>&1; then
    echo "⚠️  WARNING: DNS for $DOMAIN is not configured or not propagated yet"
    echo "   Please ensure your DNS A record points to this server's IP address:"
    curl -4 ifconfig.me 2>/dev/null && echo ""
    echo "   You can continue after DNS propagation is complete."
    read -p "   Press Enter to continue or Ctrl+C to abort..."
fi

# 7. Obtain SSL certificate
echo "🔒 Obtaining SSL certificate..."
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "   Getting new SSL certificate for $DOMAIN..."
    $SUDO certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email dfxnoodle@gmail.com || {
        echo "❌ Failed to obtain SSL certificate"
        echo "   Common issues:"
        echo "   - DNS not configured correctly"
        echo "   - Domain not pointing to this server"
        echo "   - Firewall blocking ports 80/443"
        echo ""
        echo "   You can manually run: sudo certbot --nginx -d $DOMAIN"
        echo "   Then run: PRODUCTION_DOMAIN=$DOMAIN ./start-production.sh"
        exit 1
    }
else
    echo "   SSL certificate already exists for $DOMAIN"
fi

# 8. Configure firewall (if ufw is available)
if command -v ufw >/dev/null 2>&1; then
    echo "🔥 Configuring firewall..."
    $SUDO ufw allow 'Nginx Full' || true
    $SUDO ufw allow ssh || true
    echo "   Firewall configured to allow HTTP, HTTPS, and SSH"
fi

# 9. Start the application
echo "🚀 Starting Terminal Dashboard..."
PRODUCTION_DOMAIN="$DOMAIN" ./start-production.sh

echo ""
echo "🎉 Deployment completed successfully!"
echo "===================================="
echo ""
echo "🌐 Your Terminal Dashboard is now available at:"
echo "   https://$DOMAIN"
echo ""
echo "📊 Application Status:"
echo "   - Frontend: Served by nginx with SSL"
echo "   - Backend: Running via Unix socket /tmp/terminal_dashboard.sock"
echo "   - SSL: Let's Encrypt certificate configured"
echo "   - Logs: Available in logs/ directory"
echo ""
echo "🔧 Management Commands:"
echo "   Stop services: ./stop-production.sh"
echo "   Restart nginx: sudo systemctl restart nginx"
echo "   Renew SSL: sudo certbot renew"
echo "   Check status: sudo systemctl status nginx"
echo ""
echo "📝 Important files:"
echo "   - Nginx config: /etc/nginx/sites-available/terminal-dashboard"
echo "   - SSL certificates: /etc/letsencrypt/live/$DOMAIN/"
echo "   - Application logs: $PROJECT_DIR/logs/"
echo ""
echo "🔄 SSL Certificate Auto-Renewal:"
echo "   Certbot will automatically renew certificates."
echo "   Test renewal: sudo certbot renew --dry-run"
