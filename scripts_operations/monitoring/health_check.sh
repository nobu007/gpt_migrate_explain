#!/bin/bash

# Health Check Script for UCG Monitoring Dashboard
# This script performs comprehensive health checks on the monitoring service

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="ucg-monitoring"
HOST=${MONITOR_HOST:-127.0.0.1}
PORT=${MONITOR_PORT:-8000}
TIMEOUT=${HEALTH_CHECK_TIMEOUT:-10}
LOG_FILE="/var/log/ucg-monitoring/health_check.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Exit codes
EXIT_OK=0
EXIT_WARNING=1
EXIT_CRITICAL=2
EXIT_UNKNOWN=3

# Global variables
OVERALL_STATUS=$EXIT_OK
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE" 2>/dev/null || echo "[$timestamp] [$level] $message"
}

info() {
    log "INFO" "$*"
    echo -e "${BLUE}[INFO]${NC} $*"
}

success() {
    log "SUCCESS" "$*"
    echo -e "${GREEN}[SUCCESS]${NC} $*"
    ((CHECKS_PASSED++))
}

warning() {
    log "WARNING" "$*"
    echo -e "${YELLOW}[WARNING]${NC} $*"
    ((CHECKS_WARNING++))
    if [[ $OVERALL_STATUS -eq $EXIT_OK ]]; then
        OVERALL_STATUS=$EXIT_WARNING
    fi
}

error() {
    log "ERROR" "$*"
    echo -e "${RED}[ERROR]${NC} $*" >&2
    ((CHECKS_FAILED++))
    OVERALL_STATUS=$EXIT_CRITICAL
}

# Check if service is running
check_service_running() {
    info "Checking if service is running..."
    
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        success "Service $SERVICE_NAME is active"
        return 0
    elif pgrep -f "uvicorn.*monitoring" > /dev/null; then
        success "Monitoring process is running (not as systemd service)"
        return 0
    else
        error "Service $SERVICE_NAME is not running"
        return 1
    fi
}

# Check HTTP endpoint
check_http_endpoint() {
    info "Checking HTTP endpoint at http://$HOST:$PORT..."
    
    local response
    local http_code
    
    if response=$(curl -s -w "%{http_code}" --max-time "$TIMEOUT" "http://$HOST:$PORT/" 2>/dev/null); then
        http_code="${response: -3}"
        
        if [[ "$http_code" =~ ^[23][0-9][0-9]$ ]]; then
            success "HTTP endpoint is responding (HTTP $http_code)"
            return 0
        else
            error "HTTP endpoint returned error code: $http_code"
            return 1
        fi
    else
        error "Failed to connect to HTTP endpoint"
        return 1
    fi
}

# Check health endpoint
check_health_endpoint() {
    info "Checking health endpoint..."
    
    local response
    local http_code
    
    if response=$(curl -s -w "%{http_code}" --max-time "$TIMEOUT" "http://$HOST:$PORT/api/health" 2>/dev/null); then
        http_code="${response: -3}"
        local body="${response%???}"
        
        if [[ "$http_code" == "200" ]]; then
            success "Health endpoint is healthy"
            
            # Parse JSON response if possible
            if command -v jq >/dev/null 2>&1; then
                local status=$(echo "$body" | jq -r '.status // "unknown"' 2>/dev/null)
                local uptime=$(echo "$body" | jq -r '.uptime // "unknown"' 2>/dev/null)
                info "Status: $status, Uptime: $uptime"
            fi
            
            return 0
        else
            error "Health endpoint returned error code: $http_code"
            return 1
        fi
    else
        error "Failed to connect to health endpoint"
        return 1
    fi
}

# Check WebSocket endpoint
check_websocket_endpoint() {
    info "Checking WebSocket endpoint..."
    
    # Check if wscat is available
    if ! command -v wscat >/dev/null 2>&1; then
        warning "wscat not available, skipping WebSocket check"
        return 0
    fi
    
    # Test WebSocket connection
    local ws_response
    if ws_response=$(timeout 5 wscat -c "ws://$HOST:$PORT/ws" -x '{"type":"ping"}' 2>&1); then
        if echo "$ws_response" | grep -q "pong"; then
            success "WebSocket endpoint is responding"
            return 0
        else
            warning "WebSocket connected but ping/pong failed"
            return 1
        fi
    else
        error "WebSocket connection failed"
        return 1
    fi
}

# Check API endpoints
check_api_endpoints() {
    info "Checking API endpoints..."
    
    local endpoints=(
        "/api/dashboard"
        "/api/class-analysis"
        "/api/modules"
        "/api/alerts"
    )
    
    local failed_endpoints=0
    
    for endpoint in "${endpoints[@]}"; do
        local response
        local http_code
        
        if response=$(curl -s -w "%{http_code}" --max-time "$TIMEOUT" "http://$HOST:$PORT$endpoint" 2>/dev/null); then
            http_code="${response: -3}"
            
            if [[ "$http_code" =~ ^[23][0-9][0-9]$ ]]; then
                info "✓ $endpoint (HTTP $http_code)"
            else
                warning "✗ $endpoint (HTTP $http_code)"
                ((failed_endpoints++))
            fi
        else
            error "✗ $endpoint (connection failed)"
            ((failed_endpoints++))
        fi
    done
    
    if [[ $failed_endpoints -eq 0 ]]; then
        success "All API endpoints are responding"
        return 0
    elif [[ $failed_endpoints -lt ${#endpoints[@]} ]]; then
        warning "$failed_endpoints/${#endpoints[@]} API endpoints failed"
        return 1
    else
        error "All API endpoints failed"
        return 1
    fi
}

# Check resource usage
check_resource_usage() {
    info "Checking resource usage..."
    
    # Get process info
    local pid
    if pid=$(pgrep -f "uvicorn.*monitoring" | head -1); then
        local cpu_usage=$(ps -p "$pid" -o %cpu --no-headers 2>/dev/null | tr -d ' ')
        local mem_usage=$(ps -p "$pid" -o %mem --no-headers 2>/dev/null | tr -d ' ')
        local mem_rss=$(ps -p "$pid" -o rss --no-headers 2>/dev/null | tr -d ' ')
        
        info "CPU Usage: ${cpu_usage}%"
        info "Memory Usage: ${mem_usage}% (${mem_rss}KB)"
        
        # Check thresholds
        if (( $(echo "$cpu_usage > 50" | bc -l 2>/dev/null || echo 0) )); then
            warning "High CPU usage: ${cpu_usage}%"
        fi
        
        if (( $(echo "$mem_usage > 80" | bc -l 2>/dev/null || echo 0) )); then
            warning "High memory usage: ${mem_usage}%"
        fi
        
        success "Resource usage within acceptable limits"
        return 0
    else
        error "Could not find monitoring process"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    info "Checking disk space..."
    
    local paths=(
        "/var/log/ucg-monitoring"
        "/var/lib/ucg-monitoring"
        "/var/backups/ucg-monitoring"
    )
    
    for path in "${paths[@]}"; do
        if [[ -d "$path" ]]; then
            local usage=$(df "$path" | awk 'NR==2 {print $5}' | sed 's/%//')
            
            if [[ $usage -gt 90 ]]; then
                error "Disk usage critical for $path: ${usage}%"
            elif [[ $usage -gt 80 ]]; then
                warning "Disk usage high for $path: ${usage}%"
            else
                info "Disk usage OK for $path: ${usage}%"
            fi
        else
            warning "Directory $path does not exist"
        fi
    done
    
    success "Disk space check completed"
    return 0
}

# Check log files
check_log_files() {
    info "Checking log files..."
    
    local log_files=(
        "/var/log/ucg-monitoring/monitoring.log"
        "/var/log/ucg-monitoring/error.log"
    )
    
    for log_file in "${log_files[@]}"; do
        if [[ -f "$log_file" ]]; then
            local size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null || echo 0)
            local size_mb=$((size / 1024 / 1024))
            
            if [[ $size_mb -gt 100 ]]; then
                warning "Log file $log_file is large: ${size_mb}MB"
            else
                info "Log file $log_file size: ${size_mb}MB"
            fi
            
            # Check for recent errors
            if grep -q "ERROR\|CRITICAL" "$log_file" 2>/dev/null; then
                local error_count=$(grep -c "ERROR\|CRITICAL" "$log_file" 2>/dev/null || echo 0)
                if [[ $error_count -gt 10 ]]; then
                    warning "Found $error_count errors in $log_file"
                else
                    info "Found $error_count errors in $log_file"
                fi
            fi
        else
            warning "Log file $log_file does not exist"
        fi
    done
    
    success "Log file check completed"
    return 0
}

# Check configuration files
check_configuration() {
    info "Checking configuration files..."
    
    local config_files=(
        "/etc/ucg-monitoring/.env"
        "/etc/ucg-monitoring/monitoring.yaml"
        "/etc/ucg-monitoring/logging_production.yaml"
    )
    
    for config_file in "${config_files[@]}"; do
        if [[ -f "$config_file" ]]; then
            info "✓ $config_file exists"
            
            # Check permissions
            local perms=$(stat -c "%a" "$config_file" 2>/dev/null || echo "unknown")
            if [[ "$config_file" == *".env" && "$perms" != "600" ]]; then
                warning "Environment file has insecure permissions: $perms"
            fi
        else
            error "Configuration file missing: $config_file"
        fi
    done
    
    success "Configuration check completed"
    return 0
}

# Performance test
performance_test() {
    info "Running performance test..."
    
    local start_time=$(date +%s.%N)
    local response
    local http_code
    
    if response=$(curl -s -w "%{http_code}" --max-time "$TIMEOUT" "http://$HOST:$PORT/api/dashboard" 2>/dev/null); then
        local end_time=$(date +%s.%N)
        local duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "unknown")
        
        http_code="${response: -3}"
        
        if [[ "$http_code" == "200" ]]; then
            info "Dashboard API response time: ${duration}s"
            
            if (( $(echo "$duration > 2.0" | bc -l 2>/dev/null || echo 0) )); then
                warning "Slow API response time: ${duration}s"
            else
                success "API response time acceptable: ${duration}s"
            fi
        else
            error "Performance test failed with HTTP $http_code"
            return 1
        fi
    else
        error "Performance test failed - no response"
        return 1
    fi
    
    return 0
}

# Generate summary report
generate_summary() {
    echo
    echo "=================================="
    echo "Health Check Summary"
    echo "=================================="
    echo "Timestamp: $(date)"
    echo "Host: $HOST:$PORT"
    echo
    echo "Results:"
    echo "  ✓ Passed: $CHECKS_PASSED"
    echo "  ⚠ Warning: $CHECKS_WARNING"
    echo "  ✗ Failed: $CHECKS_FAILED"
    echo
    
    case $OVERALL_STATUS in
        $EXIT_OK)
            echo -e "${GREEN}Overall Status: HEALTHY${NC}"
            ;;
        $EXIT_WARNING)
            echo -e "${YELLOW}Overall Status: WARNING${NC}"
            ;;
        $EXIT_CRITICAL)
            echo -e "${RED}Overall Status: CRITICAL${NC}"
            ;;
        *)
            echo -e "${RED}Overall Status: UNKNOWN${NC}"
            ;;
    esac
    
    echo "=================================="
}

# Main health check function
run_health_checks() {
    info "Starting health checks for UCG Monitoring Dashboard..."
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
    
    # Run all checks
    check_service_running
    check_http_endpoint
    check_health_endpoint
    check_websocket_endpoint
    check_api_endpoints
    check_resource_usage
    check_disk_space
    check_log_files
    check_configuration
    performance_test
    
    # Generate summary
    generate_summary
    
    return $OVERALL_STATUS
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --host HOST         Host to check (default: $HOST)
    --port PORT         Port to check (default: $PORT)
    --timeout SECONDS   Request timeout (default: $TIMEOUT)
    --quiet             Suppress output (exit code only)
    --verbose           Verbose output
    --help              Show this help message

Exit Codes:
    0   All checks passed (HEALTHY)
    1   Some checks failed with warnings (WARNING)
    2   Critical checks failed (CRITICAL)
    3   Unknown error (UNKNOWN)

Examples:
    $0                          # Run all health checks
    $0 --host 192.168.1.100     # Check remote host
    $0 --quiet                  # Silent mode for monitoring
    $0 --timeout 30             # Longer timeout

EOF
}

# Parse command line arguments
QUIET=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --quiet)
            QUIET=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Run health checks
if [[ "$QUIET" == "true" ]]; then
    run_health_checks >/dev/null 2>&1
    exit $?
else
    run_health_checks
    exit $?
fi