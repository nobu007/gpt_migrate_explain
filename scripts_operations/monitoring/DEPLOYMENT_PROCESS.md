# Deployment Process for UCG Monitoring Dashboard

This document outlines the step-by-step process for deploying the UCG Monitoring Dashboard in production.

## Prerequisites

Before starting the deployment, ensure you have:

1. **Server Access**: SSH access to the production server
2. **Domain Name**: DNS configured for your monitoring domain
3. **SSL Certificate**: SSL certificate for HTTPS (Let's Encrypt recommended)
4. **System Requirements**: Ubuntu 20.04+ or CentOS 8+ with minimum 2GB RAM
5. **Dependencies**: Python 3.11+, Git, Nginx

## Deployment Steps

### Step 1: Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.11 python3.11-venv python3-pip git nginx supervisor curl

# Install uv (recommended package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### Step 2: User and Directory Setup

```bash
# Create system user
sudo useradd -r -s /bin/bash -d /opt/ucg-monitoring ucg-monitoring

# Create directory structure
sudo mkdir -p /opt/ucg-monitoring
sudo mkdir -p /var/log/ucg-monitoring
sudo mkdir -p /var/lib/ucg-monitoring
sudo mkdir -p /var/backups/ucg-monitoring
sudo mkdir -p /etc/ucg-monitoring

# Set ownership
sudo chown ucg-monitoring:ucg-monitoring /opt/ucg-monitoring
sudo chown ucg-monitoring:ucg-monitoring /var/log/ucg-monitoring
sudo chown ucg-monitoring:ucg-monitoring /var/lib/ucg-monitoring
sudo chown ucg-monitoring:ucg-monitoring /var/backups/ucg-monitoring
```

### Step 3: Application Deployment

```bash
# Clone repository
sudo -u ucg-monitoring git clone https://github.com/your-org/ucg-devops.git /opt/ucg-monitoring/app

# Navigate to application directory
cd /opt/ucg-monitoring/app

# Create virtual environment
sudo -u ucg-monitoring python3.11 -m venv /opt/ucg-monitoring/venv

# Install dependencies
sudo -u ucg-monitoring /opt/ucg-monitoring/venv/bin/pip install --upgrade pip
sudo -u ucg-monitoring /opt/ucg-monitoring/venv/bin/pip install -r requirements.txt

# Or with uv (faster)
sudo -u ucg-monitoring uv sync
```

### Step 4: Configuration Setup

```bash
# Copy configuration files
sudo cp /opt/ucg-monitoring/app/config/monitoring.yaml /etc/ucg-monitoring/
sudo cp /opt/ucg-monitoring/app/config/logging_production.yaml /etc/ucg-monitoring/
sudo cp /opt/ucg-monitoring/app/.env.example /etc/ucg-monitoring/.env

# Set proper ownership and permissions
sudo chown ucg-monitoring:ucg-monitoring /etc/ucg-monitoring/*
sudo chmod 600 /etc/ucg-monitoring/.env
sudo chmod 644 /etc/ucg-monitoring/*.yaml
```

### Step 5: Environment Configuration

Edit `/etc/ucg-monitoring/.env`:

```bash
sudo nano /etc/ucg-monitoring/.env
```

Update the following variables:

```bash
# Production settings
UCG_ENVIRONMENT=production

# Monitoring Dashboard
MONITOR_HOST=127.0.0.1
MONITOR_PORT=8000
MONITOR_DEBUG=false
MONITOR_AUTO_BROWSER=false
MONITOR_LOG_LEVEL=INFO

# Security
MONITOR_API_KEY=your-secure-api-key-here
MONITOR_CORS_ORIGINS=https://monitoring.your-domain.com
MONITOR_RATE_LIMIT_ENABLED=true

# API Keys (if needed)
OPENAI_API_KEY=your-openai-key
CLAUDE_API_KEY=your-claude-key

# Notifications
MONITOR_SLACK_WEBHOOK=https://hooks.slack.com/services/your-webhook
```

### Step 6: Service Installation

```bash
# Copy systemd service file
sudo cp /opt/ucg-monitoring/app/scripts_operations/monitoring/ucg-monitoring.service /etc/systemd/system/

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable ucg-monitoring

# Start the service
sudo systemctl start ucg-monitoring

# Check service status
sudo systemctl status ucg-monitoring
```

### Step 7: Nginx Configuration

```bash
# Copy Nginx configuration (create from template in PRODUCTION_DEPLOYMENT.md)
sudo nano /etc/nginx/sites-available/ucg-monitoring

# Enable the site
sudo ln -s /etc/nginx/sites-available/ucg-monitoring /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 8: SSL Certificate Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d monitoring.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 9: Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Install fail2ban for additional security
sudo apt install fail2ban
```

### Step 10: Health Check and Verification

```bash
# Run health check script
/opt/ucg-monitoring/app/scripts_operations/monitoring/health_check.sh

# Test endpoints
curl -f http://localhost:8000/api/health
curl -f https://monitoring.your-domain.com/api/health

# Check WebSocket (if wscat is installed)
wscat -c wss://monitoring.your-domain.com/ws
```

## Post-Deployment Tasks

### 1. Set Up Monitoring

```bash
# Add health check to cron
sudo crontab -e

# Add this line for health checks every 5 minutes
*/5 * * * * /opt/ucg-monitoring/app/scripts_operations/monitoring/health_check.sh --quiet || systemctl restart ucg-monitoring
```

### 2. Configure Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/ucg-monitoring

# Add the following content:
/var/log/ucg-monitoring/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ucg-monitoring ucg-monitoring
    postrotate
        systemctl reload ucg-monitoring
    endscript
}
```

### 3. Set Up Backups

```bash
# Make backup script executable
sudo chmod +x /opt/ucg-monitoring/app/scripts_operations/monitoring/backup.sh

# Add to cron for daily backups
sudo crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /opt/ucg-monitoring/app/scripts_operations/monitoring/backup.sh
```

### 4. Configure Notifications

Update your monitoring configuration to send alerts to Slack, email, or other notification systems.

## Verification Checklist

After deployment, verify the following:

- [ ] Service is running: `sudo systemctl status ucg-monitoring`
- [ ] HTTP endpoint responds: `curl http://localhost:8000/api/health`
- [ ] HTTPS endpoint responds: `curl https://monitoring.your-domain.com/api/health`
- [ ] WebSocket connection works
- [ ] Dashboard loads in browser
- [ ] API endpoints return data
- [ ] Logs are being written
- [ ] SSL certificate is valid
- [ ] Firewall is configured
- [ ] Backups are scheduled
- [ ] Health checks are scheduled

## Rollback Procedure

If deployment fails, follow these steps to rollback:

```bash
# Stop the service
sudo systemctl stop ucg-monitoring

# Restore from backup (if available)
sudo tar -xzf /var/backups/ucg-monitoring/config_backup_YYYYMMDD_HHMMSS.tar.gz -C /

# Or remove the service entirely
sudo systemctl disable ucg-monitoring
sudo rm /etc/systemd/system/ucg-monitoring.service
sudo systemctl daemon-reload

# Remove Nginx configuration
sudo rm /etc/nginx/sites-enabled/ucg-monitoring
sudo systemctl reload nginx
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo journalctl -u ucg-monitoring -f
   sudo systemctl status ucg-monitoring
   ```

2. **Permission errors**
   ```bash
   sudo chown -R ucg-monitoring:ucg-monitoring /opt/ucg-monitoring
   sudo chown -R ucg-monitoring:ucg-monitoring /var/log/ucg-monitoring
   ```

3. **Port conflicts**
   ```bash
   sudo netstat -tuln | grep :8000
   sudo lsof -i :8000
   ```

4. **SSL certificate issues**
   ```bash
   sudo certbot certificates
   sudo nginx -t
   ```

### Log Locations

- Application logs: `/var/log/ucg-monitoring/monitoring.log`
- Error logs: `/var/log/ucg-monitoring/error.log`
- Nginx logs: `/var/log/nginx/ucg-monitoring.access.log`
- System logs: `sudo journalctl -u ucg-monitoring`

## Maintenance

### Regular Tasks

1. **Weekly**: Check service status and logs
2. **Monthly**: Review resource usage and performance
3. **Quarterly**: Update dependencies and security patches
4. **Annually**: Renew SSL certificates (if not automated)

### Update Procedure

```bash
# 1. Create backup
sudo /opt/ucg-monitoring/app/scripts_operations/monitoring/backup.sh

# 2. Stop service
sudo systemctl stop ucg-monitoring

# 3. Update code
cd /opt/ucg-monitoring/app
sudo -u ucg-monitoring git pull origin main

# 4. Update dependencies
sudo -u ucg-monitoring /opt/ucg-monitoring/venv/bin/pip install -r requirements.txt

# 5. Start service
sudo systemctl start ucg-monitoring

# 6. Verify deployment
/opt/ucg-monitoring/app/scripts_operations/monitoring/health_check.sh
```

This completes the deployment process. The monitoring dashboard should now be running securely in production.