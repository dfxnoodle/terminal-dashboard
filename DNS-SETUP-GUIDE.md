# DNS Configuration Guide for Terminal Dashboard

## GoDaddy DNS Setup

### Prerequisites
- Your domain registered with GoDaddy
- Your server's public IP address
- SSH access to your server

### Step 1: Get Your Server's Public IP
```bash
# On your server, run:
curl -4 ifconfig.me
# or
dig +short myip.opendns.com @resolver1.opendns.com
```

### Step 2: Configure DNS Records in GoDaddy

1. **Log into GoDaddy Account**
   - Go to https://godaddy.com
   - Sign in to your account
   - Go to "My Products" → "DNS"

2. **Configure A Records**
   Add these DNS records:

   | Type | Name | Value | TTL |
   |------|------|-------|-----|
   | A    | @    | YOUR_SERVER_IP | 600 |
   | A    | www  | YOUR_SERVER_IP | 600 |

   **Where:**
   - `@` = your root domain (e.g., yourdomain.com)
   - `www` = www subdomain (e.g., www.yourdomain.com)
   - `YOUR_SERVER_IP` = your server's public IP address
   - `TTL` = Time To Live (600 seconds = 10 minutes)

3. **Optional: CNAME Records**
   If you want subdomains:

   | Type  | Name      | Value          | TTL |
   |-------|-----------|----------------|-----|
   | CNAME | dashboard | yourdomain.com | 600 |
   | CNAME | api       | yourdomain.com | 600 |

### Step 3: Server Configuration

#### 3.1 Update Firewall
```bash
# Allow HTTP and HTTPS traffic
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow ssh
sudo ufw enable
```

#### 3.2 Install Nginx (if not already installed)
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
# or
sudo dnf install nginx
```

#### 3.3 Configure SSL with Let's Encrypt
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate (replace yourdomain.com with your actual domain)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

### Step 4: Deploy Terminal Dashboard

1. **Set Environment Variables**
   ```bash
   export PRODUCTION_DOMAIN=yourdomain.com
   ```

2. **Build and Start**
   ```bash
   # Build for production
   ./build-production.sh
   
   # Start with your domain
   PRODUCTION_DOMAIN=yourdomain.com ./start-production.sh
   ```

### Step 5: Configure Nginx

1. **Copy the generated nginx config**
   ```bash
   sudo cp nginx-production.conf /etc/nginx/sites-available/terminal-dashboard
   ```

2. **Edit the configuration**
   ```bash
   sudo nano /etc/nginx/sites-available/terminal-dashboard
   ```
   
   **Update these lines:**
   ```nginx
   server_name yourdomain.com www.yourdomain.com;  # Your actual domain
   root /path/to/terminal-dashboard/frontend/dist;  # Your actual path
   
   # SSL certificates (if using certbot, these will be auto-configured)
   ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
   ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
   ```

3. **Enable the site**
   ```bash
   # Create symlink
   sudo ln -s /etc/nginx/sites-available/terminal-dashboard /etc/nginx/sites-enabled/
   
   # Remove default site (optional)
   sudo rm /etc/nginx/sites-enabled/default
   
   # Test configuration
   sudo nginx -t
   
   # Restart nginx
   sudo systemctl restart nginx
   sudo systemctl enable nginx
   ```

### Step 6: Test Your Setup

1. **Check DNS propagation**
   ```bash
   # Test DNS resolution
   nslookup yourdomain.com
   dig yourdomain.com
   ```

2. **Test website access**
   - Visit: `https://yourdomain.com`
   - Check: `https://yourdomain.com/api/dashboard/all`

### Troubleshooting

#### DNS Issues
- **DNS not resolving**: Wait 24-48 hours for full propagation
- **Wrong IP**: Double-check A record points to correct server IP
- **Subdomain issues**: Ensure CNAME records are correct

#### SSL Issues
```bash
# Check SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Renew certificate if needed
sudo certbot renew
```

#### Nginx Issues
```bash
# Check nginx status
sudo systemctl status nginx

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

#### Backend Issues
```bash
# Check if socket exists
ls -la /tmp/terminal_dashboard.sock

# Check backend logs
tail -f logs/backend-production.log
```

### Security Recommendations

1. **Configure Firewall**
   ```bash
   # Only allow necessary ports
   sudo ufw allow ssh
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw deny incoming
   sudo ufw enable
   ```

2. **Secure SSH** (if using SSH)
   ```bash
   # Disable password authentication (use keys only)
   sudo nano /etc/ssh/sshd_config
   # Set: PasswordAuthentication no
   sudo systemctl restart ssh
   ```

3. **Set up fail2ban** (optional)
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   ```

### Performance Optimization

1. **Enable nginx caching**
   ```nginx
   # Add to nginx config
   proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=10g 
                    inactive=60m use_temp_path=off;
   ```

2. **Configure log rotation**
   ```bash
   # Create logrotate config
   sudo nano /etc/logrotate.d/terminal-dashboard
   ```

### Monitoring

1. **Set up basic monitoring**
   ```bash
   # Check service status
   sudo systemctl status nginx
   ps aux | grep uvicorn
   
   # Monitor logs
   tail -f logs/backend-production.log
   tail -f /var/log/nginx/access.log
   ```

2. **Set up uptime monitoring** (optional)
   - Use services like UptimeRobot, Pingdom, or StatusCake
   - Monitor: `https://yourdomain.com/health`

---

## Quick Reference

### Environment Variables for Production
```bash
export PRODUCTION_DOMAIN=yourdomain.com
export BACKEND_HOST=0.0.0.0
export FRONTEND_HOST=0.0.0.0
```

### Start Commands
```bash
# Build
./build-production.sh

# Start
PRODUCTION_DOMAIN=yourdomain.com ./start-production.sh

# Stop
./stop-production.sh
```

### Important File Locations
- **Nginx config**: `/etc/nginx/sites-available/terminal-dashboard`
- **SSL certificates**: `/etc/letsencrypt/live/yourdomain.com/`
- **Application logs**: `logs/backend-production.log`
- **Nginx logs**: `/var/log/nginx/`
- **Unix socket**: `/tmp/terminal_dashboard.sock`
