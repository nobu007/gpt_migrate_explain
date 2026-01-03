#!/bin/bash

# Production Start Script for UCG Monitoring Dashboard
# This script starts the monitoring dashboard in production mode

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SERVICE_NAME="ucg-monitoring"
USER="ucg-monitoring"
VENV_PATH="/opt/ucg-monitoring/venv"
APP_PATH="/opt/ucg-monitoring/app"
CONFIG_PATH="/etc/ucg-monitoring"
LOG_PATH="/var/log/ucg-monitoring"
PID_FILE="/var/run/ucg-monitoring.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root"
        exit 1
    fi
}

# Check if user exists
check_user() {
    if ! id "$USER" &>/dev/null; then
        error "User '$USER' does not exist. Please create it first."
        exit 1
    fi
}

# Check if directories exist
check_directories() {
    local dirs=("$APP_PATH" "$CONFIG_PATH" "$LOG_PATH" "$VENV_PATH")
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            error "Directory '$dir' does not exist"
            exit 1
        fi
    done
}

# Check if configuration files exist
check_config() {
    local configs=("$CONFIG_PATH/.env" "$CONFIG_PATH/monitoring.yaml")
    
    for config in "${configs[@]}"; do
        if [[ ! -f "$config" ]]; then
            error "Configuration file '$config' does not exist"
            exit 1
        fi
    done
}

# Check if virtual environment is set up
check_venv() {
    if [[ ! -f "$VENV_PATH/bin/python" ]]; then
        error "Virtual environment not found at '$VENV_PATH'"
        exit 1
    fi
    
    if [[ ! -f "$VENV_PATH/bin/pip" ]]; then
        error "pip not found in virtual environment"
        exit 1
    fi
}

# Check if required Python packages are installed
check_dependencies() {
    log "Checking Python dependencies..."
    
    local required_packages=("fastapi" "uvicorn" "psutil" "pyyaml")
    
    for package in "${required_packages[@]}"; do
        if ! "$VENV_PATH/bin/python" -c "import $package" 2>/dev/null; then
            error "Required package '$package' is not installed"
            exit 1
        fi
    done
    
    success "All required packages are installed"
}

# Check if port is available
check_port() {
    local port=${MONITOR_PORT:-8000}
    
    if netstat -tuln | grep -q ":$port "; then
        warning "Port $port is already in use"
        return 1
    fi
    
    return 0
}

# Load environment variables
load_env() {
    if [[ -f "$CONFIG_PATH/.env" ]]; then
        log "Loading environment variables from $CONFIG_PATH/.env"
        set -a
        source "$CONFIG_PATH/.env"
        set +a
    else
        warning "Environment file not found, using defaults"
    fi
}

# Pre-flight checks
preflight_checks() {
    log "Running pre-flight checks..."
    
    check_root
    check_user
    check_directories
    check_config
    check_venv
    load_env
    check_dependencies
    
    if ! check_port; then
        error "Port check failed. Another service may be running."
        exit 1
    fi
    
    success "All pre-flight checks passed"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    sudo mkdir -p "$LOG_PATH"
    sudo mkdir -p "/var/lib/ucg-monitoring"
    sudo mkdir -p "/var/backups/ucg-monitoring"
    
    sudo chown "$USER:$USER" "$LOG_PATH"
    sudo chown "$USER:$USER" "/var/lib/ucg-monitoring"
    sudo chown "$USER:$USER" "/var/backups/ucg-monitoring"
    
    success "Directories created"
}

# Set up logging
setup_logging() {
    log "Setting up logging..."
    
    local log_file="$LOG_PATH/monitoring.log"
    
    # Create log file if it doesn't exist
    if [[ ! -f "$log_file" ]]; then
        sudo -u "$USER" touch "$log_file"
    fi
    
    # Set proper permissions
    sudo chown "$USER:$USER" "$log_file"
    sudo chmod 644 "$log_file"
    
    success "Logging configured"
}

# Start the monitoring service
start_service() {
    log "Starting UCG Monitoring Dashboard..."
    
    local host=${MONITOR_HOST:-127.0.0.1}
    local port=${MONITOR_PORT:-8000}
    local workers=${MONITOR_WORKERS:-4}
    local log_level=${MONITOR_LOG_LEVEL:-info}
    
    # Change to application directory
    cd "$APP_PATH"
    
    # Start with uvicorn for production
    log "Starting uvicorn server..."
    log "Host: $host"
    log "Port: $port"
    log "Workers: $workers"
    log "Log Level: $log_level"
    
    # Use nohup to run in background
    nohup sudo -u "$USER" "$VENV_PATH/bin/uvicorn" \
        src.core.ai_activity_adapter.monitoring.web_app:app \
        --host "$host" \
        --port "$port" \
        --workers "$workers" \
        --log-level "$log_level" \
        --access-log \
        --log-config "$CONFIG_PATH/logging_production.yaml" \
        --env-file "$CONFIG_PATH/.env" \
        --pid-file "$PID_FILE" \
        > "$LOG_PATH/startup.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # Wait a moment for startup
    sleep 3
    
    # Check if process is still running
    if kill -0 $pid 2>/dev/null; then
        success "Service started successfully (PID: $pid)"
        log "Dashboard available at: http://$host:$port"
        log "API documentation: http://$host:$port/docs"
        log "Health check: http://$host:$port/api/health"
    else
        error "Service failed to start"
        cat "$LOG_PATH/startup.log"
        exit 1
    fi
}

# Health check
health_check() {
    log "Performing health check..."
    
    local host=${MONITOR_HOST:-127.0.0.1}
    local port=${MONITOR_PORT:-8000}
    local max_attempts=10
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "http://$host:$port/api/health" > /dev/null; then
            success "Health check passed"
            return 0
        fi
        
        log "Health check attempt $attempt/$max_attempts failed, retrying in 2 seconds..."
        sleep 2
        ((attempt++))
    done
    
    error "Health check failed after $max_attempts attempts"
    return 1
}

# Display service status
show_status() {
    log "Service Status:"
    
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 $pid 2>/dev/null; then
            success "Service is running (PID: $pid)"
            
            # Show resource usage
            local cpu_usage=$(ps -p $pid -o %cpu --no-headers)
            local mem_usage=$(ps -p $pid -o %mem --no-headers)
            local mem_rss=$(ps -p $pid -o rss --no-headers)
            
            log "CPU Usage: ${cpu_usage}%"
            log "Memory Usage: ${mem_usage}% (${mem_rss}KB)"
            
            # Show listening ports
            log "Listening on:"
            netstat -tuln | grep ":${MONITOR_PORT:-8000} " || true
            
        else
            warning "PID file exists but process is not running"
            rm -f "$PID_FILE"
        fi
    else
        warning "Service is not running (no PID file)"
    fi
}

# Show logs
show_logs() {
    local lines=${1:-50}
    
    log "Showing last $lines lines of logs:"
    
    if [[ -f "$LOG_PATH/monitoring.log" ]]; then
        tail -n "$lines" "$LOG_PATH/monitoring.log"
    else
        warning "Log file not found"
    fi
}

# Stop service
stop_service() {
    log "Stopping UCG Monitoring Dashboard..."
    
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        
        if kill -0 $pid 2>/dev/null; then
            log "Sending TERM signal to process $pid"
            kill -TERM $pid
            
            # Wait for graceful shutdown
            local count=0
            while kill -0 $pid 2>/dev/null && [[ $count -lt 30 ]]; do
                sleep 1
                ((count++))
            done
            
            # Force kill if still running
            if kill -0 $pid 2>/dev/null; then
                warning "Process still running, sending KILL signal"
                kill -KILL $pid
            fi
            
            success "Service stopped"
        else
            warning "Process not running"
        fi
        
        rm -f "$PID_FILE"
    else
        warning "PID file not found"
    fi
}

# Restart service
restart_service() {
    log "Restarting UCG Monitoring Dashboard..."
    stop_service
    sleep 2
    start_service
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [COMMAND]

Commands:
    start       Start the monitoring service
    stop        Stop the monitoring service
    restart     Restart the monitoring service
    status      Show service status
    logs        Show service logs (default: 50 lines)
    logs N      Show last N lines of logs
    health      Perform health check
    check       Run pre-flight checks only
    help        Show this help message

Examples:
    $0 start                # Start the service
    $0 status               # Check service status
    $0 logs 100             # Show last 100 log lines
    $0 restart              # Restart the service

Environment Variables:
    MONITOR_HOST            Host to bind to (default: 127.0.0.1)
    MONITOR_PORT            Port to listen on (default: 8000)
    MONITOR_WORKERS         Number of workers (default: 4)
    MONITOR_LOG_LEVEL       Log level (default: info)

Configuration:
    Environment file: $CONFIG_PATH/.env
    Config file: $CONFIG_PATH/monitoring.yaml
    Log file: $LOG_PATH/monitoring.log
    PID file: $PID_FILE

EOF
}

# Main function
main() {
    local command=${1:-help}
    
    case $command in
        start)
            preflight_checks
            create_directories
            setup_logging
            start_service
            health_check
            show_status
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            health_check
            show_status
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "${2:-50}"
            ;;
        health)
            health_check
            ;;
        check)
            preflight_checks
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