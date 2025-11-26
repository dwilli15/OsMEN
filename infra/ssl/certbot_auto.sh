#!/bin/bash
#===============================================================================
# OsMEN SSL/TLS Automation Script
# Automated Let's Encrypt certificate management for production deployments
#===============================================================================

set -euo pipefail

# Configuration
DOMAIN="${OSMEN_DOMAIN:-osmen.local}"
EMAIL="${OSMEN_EMAIL:-admin@osmen.local}"
CERT_DIR="${CERT_DIR:-/etc/letsencrypt/live/${DOMAIN}}"
NGINX_CONF="${NGINX_CONF:-/etc/nginx/sites-enabled/osmen.conf}"
WEBROOT="${WEBROOT:-/var/www/certbot}"
STAGING="${STAGING:-false}"
RENEW_THRESHOLD_DAYS="${RENEW_THRESHOLD_DAYS:-30}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

#===============================================================================
# Pre-flight Checks
#===============================================================================
check_requirements() {
    log_info "Checking requirements..."
    
    # Check certbot
    if ! command -v certbot &> /dev/null; then
        log_error "certbot not found. Installing..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y certbot python3-certbot-nginx
        elif command -v yum &> /dev/null; then
            sudo yum install -y certbot python3-certbot-nginx
        else
            log_error "Could not install certbot. Please install manually."
            exit 1
        fi
    fi
    
    # Check nginx
    if ! command -v nginx &> /dev/null; then
        log_error "nginx not found. Please install nginx first."
        exit 1
    fi
    
    # Verify domain resolves
    if ! host "$DOMAIN" &> /dev/null && [ "$DOMAIN" != "osmen.local" ]; then
        log_warn "Domain $DOMAIN does not resolve. Ensure DNS is configured."
    fi
    
    log_success "Requirements satisfied"
}

#===============================================================================
# Certificate Operations
#===============================================================================
obtain_certificate() {
    log_info "Obtaining SSL certificate for $DOMAIN..."
    
    # Create webroot directory
    sudo mkdir -p "$WEBROOT"
    
    # Build certbot command
    local certbot_cmd="certbot certonly"
    certbot_cmd+=" --webroot -w $WEBROOT"
    certbot_cmd+=" -d $DOMAIN"
    certbot_cmd+=" --email $EMAIL"
    certbot_cmd+=" --agree-tos"
    certbot_cmd+=" --non-interactive"
    certbot_cmd+=" --keep-until-expiring"
    
    # Use staging for testing
    if [ "$STAGING" = "true" ]; then
        certbot_cmd+=" --staging"
        log_warn "Using Let's Encrypt staging environment (for testing)"
    fi
    
    # Run certbot
    if eval sudo $certbot_cmd; then
        log_success "Certificate obtained successfully!"
        configure_nginx
        return 0
    else
        log_error "Failed to obtain certificate"
        return 1
    fi
}

check_certificate_expiry() {
    log_info "Checking certificate expiry..."
    
    if [ ! -f "${CERT_DIR}/fullchain.pem" ]; then
        log_warn "No certificate found at ${CERT_DIR}"
        return 1
    fi
    
    local expiry_date
    expiry_date=$(openssl x509 -enddate -noout -in "${CERT_DIR}/fullchain.pem" | cut -d= -f2)
    local expiry_epoch
    expiry_epoch=$(date -d "$expiry_date" +%s)
    local now_epoch
    now_epoch=$(date +%s)
    local days_remaining=$(( (expiry_epoch - now_epoch) / 86400 ))
    
    log_info "Certificate expires in $days_remaining days ($expiry_date)"
    
    if [ $days_remaining -lt $RENEW_THRESHOLD_DAYS ]; then
        log_warn "Certificate expires soon. Renewal recommended."
        return 1
    fi
    
    log_success "Certificate is valid for $days_remaining more days"
    return 0
}

renew_certificate() {
    log_info "Attempting certificate renewal..."
    
    if sudo certbot renew --quiet; then
        log_success "Certificate renewed successfully!"
        reload_nginx
        return 0
    else
        log_error "Certificate renewal failed"
        return 1
    fi
}

#===============================================================================
# Nginx Configuration
#===============================================================================
configure_nginx() {
    log_info "Configuring nginx for SSL..."
    
    # Backup existing config
    if [ -f "$NGINX_CONF" ]; then
        sudo cp "$NGINX_CONF" "${NGINX_CONF}.bak"
    fi
    
    # Generate SSL nginx config
    cat << EOF | sudo tee "$NGINX_CONF" > /dev/null
# OsMEN SSL Configuration - Auto-generated
# Generated: $(date)

upstream gateway {
    server 127.0.0.1:8080;
    keepalive 32;
}

upstream mcp {
    server 127.0.0.1:8081;
    keepalive 16;
}

# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root $WEBROOT;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;
    
    # SSL certificates
    ssl_certificate ${CERT_DIR}/fullchain.pem;
    ssl_certificate_key ${CERT_DIR}/privkey.pem;
    
    # SSL configuration (Modern compatibility)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # SSL session settings
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate ${CERT_DIR}/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' wss:; frame-ancestors 'none';" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/rss+xml application/atom+xml image/svg+xml;
    
    # API Gateway
    location /api/ {
        proxy_pass http://gateway/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }
    
    # MCP Server
    location /mcp/ {
        proxy_pass http://mcp/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://gateway/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
    
    # Health check (no auth required)
    location /health {
        proxy_pass http://gateway/health;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }
    
    # Static files and dashboard
    location / {
        root /var/www/osmen;
        try_files \$uri \$uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;
}
EOF
    
    # Test nginx configuration
    if sudo nginx -t; then
        log_success "Nginx configuration is valid"
        reload_nginx
    else
        log_error "Nginx configuration is invalid. Restoring backup..."
        sudo cp "${NGINX_CONF}.bak" "$NGINX_CONF"
        exit 1
    fi
}

reload_nginx() {
    log_info "Reloading nginx..."
    if sudo systemctl reload nginx; then
        log_success "Nginx reloaded successfully"
    else
        log_warn "Could not reload nginx via systemctl, trying direct reload..."
        sudo nginx -s reload
    fi
}

#===============================================================================
# Cron Setup
#===============================================================================
setup_auto_renewal() {
    log_info "Setting up automatic certificate renewal..."
    
    # Create renewal script
    local renewal_script="/etc/cron.daily/osmen-ssl-renew"
    cat << 'EOF' | sudo tee "$renewal_script" > /dev/null
#!/bin/bash
# OsMEN SSL Auto-Renewal
certbot renew --quiet --deploy-hook "systemctl reload nginx"
EOF
    
    sudo chmod +x "$renewal_script"
    log_success "Auto-renewal configured (runs daily)"
    
    # Also add to certbot's renewal hooks
    sudo mkdir -p /etc/letsencrypt/renewal-hooks/deploy
    cat << 'EOF' | sudo tee /etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh > /dev/null
#!/bin/bash
systemctl reload nginx
EOF
    sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh
}

#===============================================================================
# Self-Signed Certificates (Development)
#===============================================================================
generate_self_signed() {
    log_info "Generating self-signed certificate for development..."
    
    local ssl_dir="/etc/nginx/ssl"
    sudo mkdir -p "$ssl_dir"
    
    # Generate private key and certificate
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "${ssl_dir}/${DOMAIN}.key" \
        -out "${ssl_dir}/${DOMAIN}.crt" \
        -subj "/CN=${DOMAIN}/O=OsMEN/C=US"
    
    # Create symlinks for nginx config compatibility
    sudo mkdir -p "${CERT_DIR}"
    sudo ln -sf "${ssl_dir}/${DOMAIN}.crt" "${CERT_DIR}/fullchain.pem"
    sudo ln -sf "${ssl_dir}/${DOMAIN}.key" "${CERT_DIR}/privkey.pem"
    sudo ln -sf "${ssl_dir}/${DOMAIN}.crt" "${CERT_DIR}/chain.pem"
    
    log_success "Self-signed certificate generated"
    log_warn "Note: Browsers will show a security warning. Use Let's Encrypt for production."
}

#===============================================================================
# Status
#===============================================================================
show_status() {
    echo ""
    echo "==================== SSL/TLS Status ===================="
    echo ""
    
    # Certificate status
    if [ -f "${CERT_DIR}/fullchain.pem" ]; then
        local issuer
        issuer=$(openssl x509 -issuer -noout -in "${CERT_DIR}/fullchain.pem" | cut -d= -f2-)
        local expiry
        expiry=$(openssl x509 -enddate -noout -in "${CERT_DIR}/fullchain.pem" | cut -d= -f2)
        local subject
        subject=$(openssl x509 -subject -noout -in "${CERT_DIR}/fullchain.pem" | cut -d= -f2-)
        
        echo "Certificate: INSTALLED"
        echo "Domain:      $subject"
        echo "Issuer:      $issuer"
        echo "Expires:     $expiry"
        
        check_certificate_expiry
    else
        echo "Certificate: NOT INSTALLED"
    fi
    
    echo ""
    
    # Nginx status
    if systemctl is-active --quiet nginx; then
        echo "Nginx:       RUNNING"
    else
        echo "Nginx:       STOPPED"
    fi
    
    # HTTPS test
    if curl -sk "https://${DOMAIN}/health" &> /dev/null; then
        echo "HTTPS:       WORKING"
    else
        echo "HTTPS:       NOT ACCESSIBLE"
    fi
    
    echo ""
    echo "======================================================="
}

#===============================================================================
# Main
#===============================================================================
main() {
    local action="${1:-help}"
    
    case "$action" in
        install|obtain)
            check_requirements
            obtain_certificate
            setup_auto_renewal
            show_status
            ;;
        renew)
            renew_certificate
            ;;
        check)
            check_certificate_expiry
            ;;
        status)
            show_status
            ;;
        configure-nginx)
            configure_nginx
            ;;
        self-signed)
            generate_self_signed
            configure_nginx
            ;;
        auto-renew)
            setup_auto_renewal
            ;;
        help|*)
            echo "OsMEN SSL/TLS Automation"
            echo ""
            echo "Usage: $0 <command>"
            echo ""
            echo "Commands:"
            echo "  install         Obtain Let's Encrypt certificate and configure nginx"
            echo "  renew           Renew existing certificate"
            echo "  check           Check certificate expiry"
            echo "  status          Show SSL/TLS status"
            echo "  configure-nginx Update nginx SSL configuration"
            echo "  self-signed     Generate self-signed certificate (development)"
            echo "  auto-renew      Setup automatic renewal cron job"
            echo ""
            echo "Environment Variables:"
            echo "  OSMEN_DOMAIN          Domain name (default: osmen.local)"
            echo "  OSMEN_EMAIL           Email for Let's Encrypt (default: admin@osmen.local)"
            echo "  STAGING               Use staging environment (default: false)"
            echo "  RENEW_THRESHOLD_DAYS  Days before expiry to renew (default: 30)"
            ;;
    esac
}

main "$@"
