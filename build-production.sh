#!/bin/bash

# Production build script for Terminal Dashboard
# This script builds the frontend for production and prepares the backend

set -u -o pipefail

echo "🏗️  Building Terminal Dashboard for Production"
echo "============================================="

# Check if required tools are available
command -v npm >/dev/null 2>&1 || { echo "❌ npm is required but not installed. Aborting." >&2; exit 1; }

# Set production environment variables
export NODE_ENV=production

# Dynamic API URL configuration
if [ -n "$PRODUCTION_DOMAIN" ]; then
    # Use HTTPS for production domain
    export VITE_API_URL="https://${PRODUCTION_DOMAIN}/api"
    echo "🔧 Production API URL (HTTPS): $VITE_API_URL"
elif [ -n "$VITE_API_URL" ]; then
    # Use provided API URL
    echo "🔧 Production API URL (Custom): $VITE_API_URL"
else
    # Fallback to localhost for development
    export VITE_API_URL="http://localhost:8003"
    echo "🔧 Production API URL (Fallback): $VITE_API_URL"
fi

# Build frontend
echo ""
echo "🎨 Building Vue.js frontend for production..."
cd frontend

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Build frontend
echo "🔨 Building frontend assets..."
npm run build

# Check if build was successful
if [ ! -d "dist" ]; then
    echo "❌ Frontend build failed - dist directory not found"
    exit 1
fi

echo "✅ Frontend built successfully"

# Prepare backend
echo ""
echo "🔧 Preparing backend for production..."
cd ../backend

# Setup Python virtual environment if it doesn't exist
if [ ! -d "../.venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv ../.venv
fi

# Activate virtual environment
echo "📦 Activating Python virtual environment..."
source ../.venv/bin/activate

# Install/update backend dependencies
echo "📦 Installing backend dependencies..."
pip install -r ../requirements.txt

# Validate backend configuration
echo "🔍 Validating backend configuration..."
if [ ! -f "../.env" ]; then
    echo "⚠️  Warning: .env file not found. Make sure to configure environment variables."
    echo "   Required variables: ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY"
fi

# Test backend import
python -c "from main import app; print('✅ Backend imports successfully')" || {
    echo "❌ Backend validation failed"
    exit 1
}

cd ..

# Create production start script
echo ""
echo "📝 Creating production start script..."
cat > start-production.sh << 'EOF'
#!/bin/bash

# Production start script for Terminal Dashboard
# This script starts both frontend and backend in production mode

set -e

echo "🚀 Starting Terminal Dashboard in Production Mode"
echo "================================================="

# Default configuration
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8003}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${FRONTEND_PORT:-3003}"

# Production domain configuration
if [ -n "$PRODUCTION_DOMAIN" ]; then
    echo "🌐 Production domain: https://$PRODUCTION_DOMAIN"
    echo "🔧 API will be served at: https://$PRODUCTION_DOMAIN/api"
else
    echo "⚠️  PRODUCTION_DOMAIN not set. Using localhost configuration."
    echo "   Set PRODUCTION_DOMAIN=your-domain.com for production deployment"
fi

# Start backend
echo "🔧 Starting production backend server..."
echo "🌐 Backend will be accessible via Unix socket: /tmp/terminal_dashboard.sock"

cd backend

# Activate virtual environment
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
else
    echo "❌ Virtual environment not found. Run build-production.sh first."
    exit 1
fi

# Set production environment
export NODE_ENV=production
export NETWORK_MODE=true

# Start backend with production settings (4 workers for better performance)
nohup uvicorn main:app \
    --uds /tmp/terminal_dashboard.sock \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-log \
    --log-level info \
    --timeout-keep-alive 65 \
    --limit-concurrency 1000 > ../logs/backend-production.log 2>&1 &

BACKEND_PID=$!

# Set appropriate permissions for the socket
sleep 2
if [ -S "/tmp/terminal_dashboard.sock" ]; then
    chmod 666 /tmp/terminal_dashboard.sock
    echo "✅ Backend started (PID: $BACKEND_PID) - Socket: /tmp/terminal_dashboard.sock"
else
    echo "⚠️  Backend started (PID: $BACKEND_PID) - Socket may still be initializing"
fi

# Wait for backend to start
sleep 3

# Serve frontend static files
echo ""
echo "🎨 Starting production frontend server..."
echo "🌐 Frontend will be accessible at: http://$FRONTEND_HOST:$FRONTEND_PORT"

cd ../frontend

# Check if dist directory exists
if [ ! -d "dist" ]; then
    echo "❌ Frontend build not found. Run build-production.sh first."
    kill $BACKEND_PID
    exit 1
fi

# Serve static files using a simple HTTP server
# You can replace this with nginx, apache, or any other web server
nohup python3 -m http.server $FRONTEND_PORT \
    --bind $FRONTEND_HOST \
    --directory dist > ../logs/frontend-production.log 2>&1 &

FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"

cd ..

# Save PIDs for easy stopping
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "🎉 Terminal Dashboard is running in production mode!"
echo "📊 Frontend: http://$FRONTEND_HOST:$FRONTEND_PORT"
echo "🔧 Backend API: Unix socket /tmp/terminal_dashboard.sock"
echo "📝 Logs: logs/backend-production.log and logs/frontend-production.log"
echo ""
echo "To stop the servers, run: ./stop-production.sh"
EOF

chmod +x start-production.sh

# Create production stop script
echo "📝 Creating production stop script..."
cat > stop-production.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping Terminal Dashboard Production Services"
echo "================================================="

# Create logs directory if it doesn't exist
mkdir -p logs

# Stop backend
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🔧 Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        rm logs/backend.pid
        echo "✅ Backend stopped"
    else
        echo "⚠️  Backend process not running"
        rm -f logs/backend.pid
    fi
else
    echo "⚠️  Backend PID file not found"
fi

# Stop frontend
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🎨 Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm logs/frontend.pid
        echo "✅ Frontend stopped"
    else
        echo "⚠️  Frontend process not running"
        rm -f logs/frontend.pid
    fi
else
    echo "⚠️  Frontend PID file not found"
fi

# Alternative: Kill all related processes
echo ""
echo "🧹 Cleaning up any remaining processes..."
pkill -f "uvicorn.*main:app" || true
pkill -f "python.*http.server.*dist" || true

# Clean up socket file
if [ -S "/tmp/terminal_dashboard.sock" ]; then
    rm -f /tmp/terminal_dashboard.sock
    echo "🧹 Removed Unix socket file"
fi

echo "✅ All services stopped"
EOF

chmod +x stop-production.sh

# Create logs directory
mkdir -p logs

# Create nginx configuration template (optional)
echo "📝 Creating nginx configuration template..."
cat > nginx-production.conf << 'EOF'
# Nginx configuration for Terminal Dashboard Production
# Copy this to your nginx sites-available directory and modify as needed

# Upstream backend servers (4 workers via Unix socket)
upstream terminal_dashboard_backend {
    server unix:/tmp/terminal_dashboard.sock;
    keepalive 32;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name ethihad-rail-dashboard.linus.services;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name ethihad-rail-dashboard.linus.services;

    # SSL configuration (certbot managed)
    ssl_certificate /etc/letsencrypt/live/ethihad-rail-dashboard.linus.services/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ethihad-rail-dashboard.linus.services/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Frontend static files
    location / {
        root /media/dinochlai/Data/terminal-dashboard/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Enable compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types
            text/plain
            text/css
            text/xml
            text/javascript
            application/json
            application/javascript
            application/xml+rss
            application/atom+xml
            image/svg+xml;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Security for index.html
        location = /index.html {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
        }
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://terminal_dashboard_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
        
        # CORS headers (if needed for cross-origin requests)
        add_header Access-Control-Allow-Origin $http_origin always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With" always;
        add_header Access-Control-Allow-Credentials true always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin $http_origin;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With";
            add_header Access-Control-Allow-Credentials true;
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 204;
        }
    }

    # Health check endpoint
    location /health {
        proxy_pass http://terminal_dashboard_backend/;
        proxy_set_header Host $host;
        access_log off;
    }

    # Direct socket status check (for monitoring)
    location /socket-status {
        access_log off;
        return 200 "Socket: /tmp/terminal_dashboard.sock";
        add_header Content-Type text/plain;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ ~$ {
        deny all;
    }
}

# Additional server block for monitoring (optional)
# server {
#     listen 8080;
#     server_name localhost;
#     location /nginx_status {
#         stub_status on;
#         access_log off;
#         allow 127.0.0.1;
#         deny all;
#     }
# }
EOF

echo ""
echo "🎉 Production build completed successfully!"
echo "==========================================="
echo ""
echo "📁 Build artifacts:"
echo "   - Frontend: frontend/dist/"
echo "   - Backend: backend/ (with virtual environment)"
echo ""
echo "📝 Production scripts created:"
echo "   - start-production.sh  (start services)"
echo "   - stop-production.sh   (stop services)"
echo "   - nginx-production.conf (nginx config template)"
echo "   - DNS-SETUP-GUIDE.md   (complete DNS and deployment guide)"
echo ""
echo "🚀 To start in production mode:"
echo ""
echo "   # For local/development testing:"
echo "   ./start-production.sh"
echo ""
echo "   # For production with domain:"
echo "   PRODUCTION_DOMAIN=yourdomain.com ./start-production.sh"
echo ""
echo "   # With custom configuration:"
echo "   PRODUCTION_DOMAIN=yourdomain.com BACKEND_PORT=8080 ./start-production.sh"
echo ""
echo "🔧 Production configuration:"
echo "   - Frontend built with optimizations and dynamic API URL"
echo "   - Backend with 4 workers for high performance via Unix socket"
echo "   - Unix socket provides better performance than TCP"
echo "   - Support for HTTPS domains"
echo "   - Logs saved to logs/ directory"
echo "   - PIDs tracked for clean shutdown"
echo "   - Enhanced uvicorn settings for production"
echo ""
echo "🌐 Environment variables:"
echo "   - PRODUCTION_DOMAIN: Your domain name (enables HTTPS API URLs)"
echo "   - BACKEND_HOST: Backend bind address (default: 0.0.0.0)"
echo "   - BACKEND_PORT: Backend port (default: 8003)"
echo "   - FRONTEND_HOST: Frontend bind address (default: 0.0.0.0)"
echo "   - FRONTEND_PORT: Frontend port (default: 3003)"
echo ""
echo "🔒 HTTPS Setup for ethihad-rail-dashboard.linus.services:"
echo "   1. Install certbot: sudo apt install certbot python3-certbot-nginx"
echo "   2. Obtain SSL certificate: sudo certbot --nginx -d ethihad-rail-dashboard.linus.services"
echo "   3. Start production: PRODUCTION_DOMAIN=ethihad-rail-dashboard.linus.services ./start-production.sh"
echo ""
echo "⚠️  Important notes:"
echo "   1. Configure your .env file with production credentials"
echo "   2. Use nginx/apache for better static file serving and SSL"
echo "   3. Set PRODUCTION_DOMAIN for proper HTTPS API URLs"
echo "   4. Configure firewall rules appropriately"
echo "   5. Set up log rotation for production logs"
echo "   6. Use a process manager like systemd or pm2 for production"
echo "   7. Unix socket /tmp/terminal_dashboard.sock provides better performance"
echo "   8. Ensure nginx has permissions to access the Unix socket"
echo ""
echo "📋 Next Steps for ethihad-rail-dashboard.linus.services:"
echo "   1. Read DNS-SETUP-GUIDE.md for complete instructions"
echo "   2. Get your server's public IP: curl -4 ifconfig.me"
echo "   3. Configure DNS A record: ethihad-rail-dashboard.linus.services → YOUR_SERVER_IP"
echo "   4. Install nginx: sudo apt update && sudo apt install nginx"
echo "   5. Copy nginx config: sudo cp nginx-production.conf /etc/nginx/sites-available/terminal-dashboard"
echo "   6. Enable site: sudo ln -s /etc/nginx/sites-available/terminal-dashboard /etc/nginx/sites-enabled/"
echo "   7. Test nginx: sudo nginx -t"
echo "   8. Install certbot: sudo apt install certbot python3-certbot-nginx"
echo "   9. Get SSL certificate: sudo certbot --nginx -d ethihad-rail-dashboard.linus.services"
echo "   10. Deploy: PRODUCTION_DOMAIN=ethihad-rail-dashboard.linus.services ./start-production.sh"
