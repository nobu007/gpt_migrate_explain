#!/bin/bash

# Monitoring and Alerting Setup Script for UCG Monitoring Dashboard
# This script sets up comprehensive monitoring and alerting for the monitoring service itself

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MONITORING_USER="ucg-monitoring"
MONITORING_DIR="/opt/ucg-monitoring"
CONFIG_DIR="/etc/ucg-monitoring"
LOG_DIR="/var/log/ucg-monitoring"
DATA_DIR="/var/lib/ucg-monitoring"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        exit 1
    fi
}

# Install required packages
install_packages() {
    log "Installing required packages..."
    
    # Update package list
    apt-get update
    
    # Install monitoring tools
    apt-get install -y \
        prometheus \
        grafana \
        alertmanager \
        node-exporter \
        nginx-prometheus-exporter \
        fluentd \
        td-agent \
        curl \
        jq \
        bc \
        wscat
    
    # Install Python packages for metrics
    pip3 install \
        prometheus-client \
        psutil \
        requests
    
    success "Packages installed successfully"
}

# Configure Prometheus
setup_prometheus() {
    log "Setting up Prometheus..."
    
    # Create Prometheus configuration
    cat > /etc/prometheus/prometheus.yml << 'EOF'
# Prometheus configuration for UCG Monitoring Dashboard

global:
  scrape_interval: 30s
  evaluation_interval: 30s
  external_labels:
    monitor: 'ucg-monitoring'
    environment: 'production'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

# Load rules once and periodically evaluate them
rule_files:
  - "/etc/prometheus/rules/*.yml"

# Scrape configurations
scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s
    metrics_path: /metrics

  # UCG Monitoring Dashboard
  - job_name: 'ucg-monitoring'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 30s
    metrics_path: /metrics
    scrape_timeout: 10s

  # Node Exporter (system metrics)
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
    scrape_interval: 30s

  # Nginx metrics
  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']
    scrape_interval: 30s

  # Fluentd metrics
  - job_name: 'fluentd'
    static_configs:
      - targets: ['localhost:24231']
    scrape_interval: 60s
    metrics_path: /metrics

  # Custom health checks
  - job_name: 'health-checks'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 30s
    metrics_path: /api/health
    params:
      format: ['prometheus']

# Storage configuration
storage:
  tsdb:
    path: /var/lib/prometheus
    retention.time: 30d
    retention.size: 10GB
EOF

    # Create alert rules directory
    mkdir -p /etc/prometheus/rules
    
    # Create alert rules
    cat > /etc/prometheus/rules/ucg-monitoring.yml << 'EOF'
groups:
  - name: ucg-monitoring
    rules:
      # Service availability
      - alert: UCGMonitoringDown
        expr: up{job="ucg-monitoring"} == 0
        for: 1m
        labels:
          severity: critical
          service: ucg-monitoring
        annotations:
          summary: "UCG Monitoring Dashboard is down"
          description: "UCG Monitoring Dashboard has been down for more than 1 minute"

      # High CPU usage
      - alert: UCGMonitoringHighCPU
        expr: rate(process_cpu_seconds_total{job="ucg-monitoring"}[5m]) * 100 > 75
        for: 5m
        labels:
          severity: warning
          service: ucg-monitoring
        annotations:
          summary: "High CPU usage in UCG Monitoring"
          description: "CPU usage is {{ $value }}% for more than 5 minutes"

      # High memory usage
      - alert: UCGMonitoringHighMemory
        expr: process_resident_memory_bytes{job="ucg-monitoring"} / 1024 / 1024 > 500
        for: 5m
        labels:
          severity: warning
          service: ucg-monitoring
        annotations:
          summary: "High memory usage in UCG Monitoring"
          description: "Memory usage is {{ $value }}MB for more than 5 minutes"

      # High API response time
      - alert: UCGMonitoringSlowAPI
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="ucg-monitoring"}[5m])) > 2
        for: 3m
        labels:
          severity: warning
          service: ucg-monitoring
        annotations:
          summary: "Slow API responses in UCG Monitoring"
          description: "95th percentile response time is {{ $value }}s for more than 3 minutes"

      # High error rate
      - alert: UCGMonitoringHighErrorRate
        expr: rate(http_requests_total{job="ucg-monitoring",code=~"5.."}[5m]) / rate(http_requests_total{job="ucg-monitoring"}[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
          service: ucg-monitoring
        annotations:
          summary: "High error rate in UCG Monitoring"
          description: "Error rate is {{ $value | humanizePercentage }} for more than 2 minutes"

      # WebSocket connection issues
      - alert: UCGMonitoringWebSocketIssues
        expr: rate(websocket_connection_failures_total{job="ucg-monitoring"}[5m]) > 0.1
        for: 3m
        labels:
          severity: warning
          service: ucg-monitoring
        annotations:
          summary: "WebSocket connection issues in UCG Monitoring"
          description: "WebSocket failure rate is {{ $value }} failures/second for more than 3 minutes"

      # Disk space
      - alert: UCGMonitoringLowDiskSpace
        expr: (node_filesystem_avail_bytes{mountpoint="/var/log/ucg-monitoring"} / node_filesystem_size_bytes{mountpoint="/var/log/ucg-monitoring"}) * 100 < 20
        for: 5m
        labels:
          severity: warning
          service: ucg-monitoring
        annotations:
          summary: "Low disk space for UCG Monitoring logs"
          description: "Available disk space is {{ $value }}% for more than 5 minutes"

      # Log errors
      - alert: UCGMonitoringLogErrors
        expr: rate(log_entries_total{job="fluentd",level="ERROR"}[10m]) > 0.1
        for: 5m
        labels:
          severity: warning
          service: ucg-monitoring
        annotations:
          summary: "High error rate in UCG Monitoring logs"
          description: "Error log rate is {{ $value }} errors/second for more than 5 minutes"
EOF

    # Set permissions
    chown -R prometheus:prometheus /etc/prometheus
    chmod -R 644 /etc/prometheus/prometheus.yml
    chmod -R 644 /etc/prometheus/rules/
    
    # Enable and start Prometheus
    systemctl enable prometheus
    systemctl restart prometheus
    
    success "Prometheus configured and started"
}

# Configure Alertmanager
setup_alertmanager() {
    log "Setting up Alertmanager..."
    
    # Create Alertmanager configuration
    cat > /etc/alertmanager/alertmanager.yml << 'EOF'
# Alertmanager configuration for UCG Monitoring Dashboard

global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'monitoring@your-domain.com'
  smtp_auth_username: ''
  smtp_auth_password: ''

# Templates
templates:
  - '/etc/alertmanager/templates/*.tmpl'

# Route configuration
route:
  group_by: ['alertname', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      group_wait: 10s
      repeat_interval: 1h
    
    - match:
        severity: warning
      receiver: 'warning-alerts'
      group_wait: 30s
      repeat_interval: 4h

# Receivers
receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://localhost:8000/api/alerts/webhook'
        send_resolved: true

  - name: 'critical-alerts'
    email_configs:
      - to: 'admin@your-domain.com'
        subject: '[CRITICAL] UCG Monitoring Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Severity: {{ .Labels.severity }}
          Service: {{ .Labels.service }}
          Started: {{ .StartsAt }}
          {{ end }}
    
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#monitoring-alerts'
        username: 'UCG Monitoring'
        icon_emoji: ':rotating_light:'
        title: 'CRITICAL Alert - UCG Monitoring'
        text: |
          {{ range .Alerts }}
          *Alert:* {{ .Annotations.summary }}
          *Description:* {{ .Annotations.description }}
          *Severity:* {{ .Labels.severity }}
          *Service:* {{ .Labels.service }}
          *Started:* {{ .StartsAt }}
          {{ end }}
        send_resolved: true

  - name: 'warning-alerts'
    email_configs:
      - to: 'devops@your-domain.com'
        subject: '[WARNING] UCG Monitoring Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Severity: {{ .Labels.severity }}
          Service: {{ .Labels.service }}
          Started: {{ .StartsAt }}
          {{ end }}

# Inhibit rules
inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'service']
EOF

    # Create templates directory
    mkdir -p /etc/alertmanager/templates
    
    # Set permissions
    chown -R alertmanager:alertmanager /etc/alertmanager
    chmod -R 644 /etc/alertmanager/alertmanager.yml
    
    # Enable and start Alertmanager
    systemctl enable alertmanager
    systemctl restart alertmanager
    
    success "Alertmanager configured and started"
}

# Configure Grafana
setup_grafana() {
    log "Setting up Grafana..."
    
    # Configure Grafana
    cat > /etc/grafana/grafana.ini << 'EOF'
[DEFAULT]
instance_name = ucg-monitoring

[server]
protocol = http
http_addr = 127.0.0.1
http_port = 3000
domain = monitoring.your-domain.com
root_url = https://monitoring.your-domain.com/grafana/

[database]
type = sqlite3
path = /var/lib/grafana/grafana.db

[security]
admin_user = admin
admin_password = ${GRAFANA_ADMIN_PASSWORD}
secret_key = ${GRAFANA_SECRET_KEY}

[users]
allow_sign_up = false
allow_org_create = false
auto_assign_org = true
auto_assign_org_role = Viewer

[auth.anonymous]
enabled = false

[log]
mode = file
level = info
filters = rendering:debug

[log.file]
path = /var/log/grafana/grafana.log
max_lines = 1000000
max_size_shift = 28
daily_rotate = true
max_days = 7

[alerting]
enabled = true
execute_alerts = true

[metrics]
enabled = true
interval_seconds = 10

[tracing.jaeger]
address = localhost:14268
always_included_tag = tag1:value1
sampler_type = const
sampler_param = 1
EOF

    # Enable and start Grafana
    systemctl enable grafana-server
    systemctl restart grafana-server
    
    success "Grafana configured and started"
}

# Configure Node Exporter
setup_node_exporter() {
    log "Setting up Node Exporter..."
    
    # Create systemd service for node exporter
    cat > /etc/systemd/system/node-exporter.service << 'EOF'
[Unit]
Description=Node Exporter
After=network.target

[Service]
Type=simple
User=node-exporter
Group=node-exporter
ExecStart=/usr/bin/node_exporter \
    --web.listen-address=:9100 \
    --path.procfs=/proc \
    --path.sysfs=/sys \
    --collector.filesystem.ignored-mount-points="^/(sys|proc|dev|host|etc|rootfs/var/lib/docker/containers|rootfs/var/lib/docker/overlay2|rootfs/run/docker/netns|rootfs/var/lib/docker/aufs)($$|/)" \
    --collector.systemd \
    --collector.processes
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Create user for node exporter
    useradd -r -s /bin/false node-exporter || true
    
    # Enable and start node exporter
    systemctl daemon-reload
    systemctl enable node-exporter
    systemctl restart node-exporter
    
    success "Node Exporter configured and started"
}

# Configure Fluentd
setup_fluentd() {
    log "Setting up Fluentd..."
    
    # Copy Fluentd configuration
    cp "$PROJECT_ROOT/config/log_aggregation.conf" /etc/td-agent/td-agent.conf
    
    # Create necessary directories
    mkdir -p /var/log/fluentd/buffer
    mkdir -p /var/log/ucg-monitoring/aggregated
    
    # Set permissions
    chown -R td-agent:td-agent /var/log/fluentd
    chown -R td-agent:td-agent /var/log/ucg-monitoring/aggregated
    
    # Install required gems
    td-agent-gem install fluent-plugin-elasticsearch
    td-agent-gem install fluent-plugin-slack
    td-agent-gem install fluent-plugin-prometheus
    td-agent-gem install fluent-plugin-anomaly-detector
    
    # Enable and start td-agent
    systemctl enable td-agent
    systemctl restart td-agent
    
    success "Fluentd configured and started"
}

# Create monitoring scripts
create_monitoring_scripts() {
    log "Creating monitoring scripts..."
    
    # Create metrics collection script
    cat > /usr/local/bin/ucg-monitoring-metrics.py << 'EOF'
#!/usr/bin/env python3
"""
UCG Monitoring Dashboard Metrics Collector
Collects custom metrics and exposes them for Prometheus
"""

import time
import json
import psutil
import requests
from prometheus_client import start_http_server, Gauge, Counter, Histogram
from prometheus_client.core import CollectorRegistry

# Metrics registry
registry = CollectorRegistry()

# Define metrics
cpu_usage = Gauge('ucg_monitoring_cpu_usage_percent', 'CPU usage percentage', registry=registry)
memory_usage = Gauge('ucg_monitoring_memory_usage_bytes', 'Memory usage in bytes', registry=registry)
disk_usage = Gauge('ucg_monitoring_disk_usage_percent', 'Disk usage percentage', registry=registry)
websocket_connections = Gauge('ucg_monitoring_websocket_connections', 'Number of WebSocket connections', registry=registry)
class_analysis_duration = Histogram('ucg_monitoring_class_analysis_duration_seconds', 'Class analysis duration', registry=registry)
api_requests = Counter('ucg_monitoring_api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'], registry=registry)

def collect_system_metrics():
    """Collect system metrics"""
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_usage.set(cpu_percent)
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_usage.set(memory.used)
    
    # Disk usage
    disk = psutil.disk_usage('/var/log/ucg-monitoring')
    disk_percent = (disk.used / disk.total) * 100
    disk_usage.set(disk_percent)

def collect_application_metrics():
    """Collect application-specific metrics"""
    try:
        # Get health status
        response = requests.get('http://localhost:8000/api/health', timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            
            # WebSocket connections (if available in health data)
            if 'websocket_connections' in health_data:
                websocket_connections.set(health_data['websocket_connections'])
    
    except Exception as e:
        print(f"Error collecting application metrics: {e}")

def main():
    """Main metrics collection loop"""
    # Start Prometheus metrics server
    start_http_server(9091, registry=registry)
    print("Metrics server started on port 9091")
    
    while True:
        try:
            collect_system_metrics()
            collect_application_metrics()
            time.sleep(30)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error in metrics collection: {e}")
            time.sleep(30)

if __name__ == '__main__':
    main()
EOF

    chmod +x /usr/local/bin/ucg-monitoring-metrics.py
    
    # Create systemd service for metrics collector
    cat > /etc/systemd/system/ucg-monitoring-metrics.service << 'EOF'
[Unit]
Description=UCG Monitoring Metrics Collector
After=network.target ucg-monitoring.service
Requires=ucg-monitoring.service

[Service]
Type=simple
User=ucg-monitoring
Group=ucg-monitoring
ExecStart=/usr/local/bin/ucg-monitoring-metrics.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Enable and start metrics collector
    systemctl daemon-reload
    systemctl enable ucg-monitoring-metrics
    systemctl start ucg-monitoring-metrics
    
    success "Monitoring scripts created and started"
}

# Create alert notification script
create_alert_script() {
    log "Creating alert notification script..."
    
    cat > /usr/local/bin/ucg-monitoring-alert.sh << 'EOF'
#!/bin/bash

# UCG Monitoring Alert Handler
# Processes alerts and sends notifications

ALERT_TYPE="$1"
ALERT_MESSAGE="$2"
ALERT_SEVERITY="${3:-INFO}"

# Configuration
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL}"
EMAIL_TO="${ALERT_EMAIL_TO:-admin@your-domain.com}"
LOG_FILE="/var/log/ucg-monitoring/alerts.log"

# Logging
log_alert() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$ALERT_SEVERITY] $ALERT_TYPE: $ALERT_MESSAGE" >> "$LOG_FILE"
}

# Send Slack notification
send_slack() {
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        local color="good"
        local emoji=":information_source:"
        
        case "$ALERT_SEVERITY" in
            CRITICAL)
                color="danger"
                emoji=":rotating_light:"
                ;;
            WARNING)
                color="warning"
                emoji=":warning:"
                ;;
            ERROR)
                color="danger"
                emoji=":x:"
                ;;
        esac
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"username\": \"UCG Monitoring\",
                \"icon_emoji\": \"$emoji\",
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"$ALERT_TYPE\",
                    \"text\": \"$ALERT_MESSAGE\",
                    \"fields\": [{
                        \"title\": \"Severity\",
                        \"value\": \"$ALERT_SEVERITY\",
                        \"short\": true
                    }, {
                        \"title\": \"Time\",
                        \"value\": \"$(date)\",
                        \"short\": true
                    }]
                }]
            }" \
            "$SLACK_WEBHOOK"
    fi
}

# Send email notification
send_email() {
    if command -v mail >/dev/null 2>&1; then
        echo "$ALERT_MESSAGE" | mail -s "[$ALERT_SEVERITY] UCG Monitoring: $ALERT_TYPE" "$EMAIL_TO"
    fi
}

# Main execution
log_alert

case "$ALERT_SEVERITY" in
    CRITICAL|ERROR)
        send_slack
        send_email
        ;;
    WARNING)
        send_slack
        ;;
    *)
        # INFO level - just log
        ;;
esac
EOF

    chmod +x /usr/local/bin/ucg-monitoring-alert.sh
    
    success "Alert notification script created"
}

# Set up cron jobs for monitoring
setup_cron_jobs() {
    log "Setting up cron jobs..."
    
    # Create cron jobs for monitoring
    cat > /etc/cron.d/ucg-monitoring << 'EOF'
# UCG Monitoring Dashboard Cron Jobs

# Health check every 5 minutes
*/5 * * * * root /opt/ucg-monitoring/app/scripts_operations/monitoring/health_check.sh --quiet || /usr/local/bin/ucg-monitoring-alert.sh "Health Check Failed" "UCG Monitoring health check failed" "CRITICAL"

# Disk space check every hour
0 * * * * root df -h /var/log/ucg-monitoring | awk 'NR==2 {if(substr($5,1,length($5)-1) > 85) system("/usr/local/bin/ucg-monitoring-alert.sh \"Disk Space Warning\" \"Log disk usage is " $5 "\" \"WARNING\"")}'

# Log rotation check daily
0 2 * * * root find /var/log/ucg-monitoring -name "*.log" -size +100M -exec /usr/local/bin/ucg-monitoring-alert.sh "Large Log File" "Log file {} is larger than 100MB" "WARNING" \;

# Service status check every 10 minutes
*/10 * * * * root systemctl is-active --quiet ucg-monitoring || /usr/local/bin/ucg-monitoring-alert.sh "Service Down" "UCG Monitoring service is not running" "CRITICAL"

# Certificate expiry check (weekly)
0 0 * * 0 root /usr/local/bin/check-ssl-expiry.sh monitoring.your-domain.com 443 30 || /usr/local/bin/ucg-monitoring-alert.sh "SSL Certificate Expiry" "SSL certificate expires soon" "WARNING"
EOF

    success "Cron jobs configured"
}

# Create SSL certificate expiry check script
create_ssl_check() {
    log "Creating SSL certificate expiry check script..."
    
    cat > /usr/local/bin/check-ssl-expiry.sh << 'EOF'
#!/bin/bash

# SSL Certificate Expiry Check Script

HOSTNAME="$1"
PORT="${2:-443}"
WARNING_DAYS="${3:-30}"

if [[ -z "$HOSTNAME" ]]; then
    echo "Usage: $0 <hostname> [port] [warning_days]"
    exit 1
fi

# Get certificate expiry date
EXPIRY_DATE=$(echo | openssl s_client -servername "$HOSTNAME" -connect "$HOSTNAME:$PORT" 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)

if [[ -z "$EXPIRY_DATE" ]]; then
    echo "Failed to get certificate expiry date for $HOSTNAME:$PORT"
    exit 1
fi

# Convert to epoch time
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_UNTIL_EXPIRY=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))

echo "Certificate for $HOSTNAME expires in $DAYS_UNTIL_EXPIRY days ($EXPIRY_DATE)"

if [[ $DAYS_UNTIL_EXPIRY -le $WARNING_DAYS ]]; then
    echo "WARNING: Certificate expires in $DAYS_UNTIL_EXPIRY days"
    exit 1
fi

exit 0
EOF

    chmod +x /usr/local/bin/check-ssl-expiry.sh
    
    success "SSL certificate expiry check script created"
}

# Configure firewall for monitoring ports
configure_firewall() {
    log "Configuring firewall for monitoring ports..."
    
    # Allow monitoring ports
    ufw allow 9090/tcp comment "Prometheus"
    ufw allow 9093/tcp comment "Alertmanager"
    ufw allow 3000/tcp comment "Grafana"
    ufw allow 9100/tcp comment "Node Exporter"
    ufw allow 9091/tcp comment "Custom Metrics"
    
    success "Firewall configured for monitoring ports"
}

# Verify installation
verify_installation() {
    log "Verifying monitoring installation..."
    
    local services=(
        "prometheus"
        "alertmanager"
        "grafana-server"
        "node-exporter"
        "td-agent"
        "ucg-monitoring-metrics"
    )
    
    local failed_services=0
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            success "✓ $service is running"
        else
            error "✗ $service is not running"
            ((failed_services++))
        fi
    done
    
    # Check ports
    local ports=(
        "9090:Prometheus"
        "9093:Alertmanager"
        "3000:Grafana"
        "9100:Node Exporter"
        "24224:Fluentd"
        "9091:Custom Metrics"
    )
    
    for port_info in "${ports[@]}"; do
        local port="${port_info%:*}"
        local service="${port_info#*:}"
        
        if netstat -tuln | grep -q ":$port "; then
            success "✓ $service is listening on port $port"
        else
            warning "✗ $service is not listening on port $port"
        fi
    done
    
    if [[ $failed_services -eq 0 ]]; then
        success "All monitoring services are running successfully"
        return 0
    else
        error "$failed_services services failed to start"
        return 1
    fi
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [COMMAND]

Commands:
    install     Install and configure all monitoring components
    verify      Verify monitoring installation
    start       Start all monitoring services
    stop        Stop all monitoring services
    restart     Restart all monitoring services
    status      Show status of all monitoring services
    help        Show this help message

Examples:
    $0 install      # Full installation
    $0 verify       # Check installation
    $0 status       # Show service status

EOF
}

# Main function
main() {
    local command=${1:-help}
    
    case $command in
        install)
            check_root
            install_packages
            setup_prometheus
            setup_alertmanager
            setup_grafana
            setup_node_exporter
            setup_fluentd
            create_monitoring_scripts
            create_alert_script
            setup_cron_jobs
            create_ssl_check
            configure_firewall
            verify_installation
            ;;
        verify)
            verify_installation
            ;;
        start)
            check_root
            systemctl start prometheus alertmanager grafana-server node-exporter td-agent ucg-monitoring-metrics
            ;;
        stop)
            check_root
            systemctl stop prometheus alertmanager grafana-server node-exporter td-agent ucg-monitoring-metrics
            ;;
        restart)
            check_root
            systemctl restart prometheus alertmanager grafana-server node-exporter td-agent ucg-monitoring-metrics
            ;;
        status)
            systemctl status prometheus alertmanager grafana-server node-exporter td-agent ucg-monitoring-metrics
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"