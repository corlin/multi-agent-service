#!/bin/bash

# Patent MVP System Production Startup Script with uv optimization
# This script provides comprehensive production deployment for patent analysis system

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/startup.log"
PID_FILE="$PROJECT_ROOT/logs/patent-mvp.pid"

# Default values
WORKERS=${UVICORN_WORKERS:-4}
HOST=${UVICORN_HOST:-0.0.0.0}
PORT=${UVICORN_PORT:-8000}
SKIP_CHECKS=${SKIP_CHECKS:-false}
USE_DOCKER=${USE_DOCKER:-false}

# Functions
log() {
    echo -e "${2:-$NC}$(date '+%Y-%m-%d %H:%M:%S') - $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    log "❌ ERROR: $1" "$RED"
    exit 1
}

warning() {
    log "⚠️  WARNING: $1" "$YELLOW"
}

success() {
    log "✅ $1" "$GREEN"
}

info() {
    log "ℹ️  $1" "$BLUE"
}

# Help function
show_help() {
    cat << EOF
Patent MVP System Production Startup Script

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -w, --workers NUM       Number of uvicorn workers (default: 4)
    -H, --host HOST         Host to bind to (default: 0.0.0.0)
    -p, --port PORT         Port to bind to (default: 8000)
    -s, --skip-checks       Skip pre-startup checks
    -d, --docker            Use Docker deployment
    --stop                  Stop running service
    --restart               Restart service
    --status                Show service status

Examples:
    $0                      Start with default settings
    $0 -w 8 -p 8080        Start with 8 workers on port 8080
    $0 --docker            Start using Docker Compose
    $0 --stop              Stop the service
    $0 --status            Check service status

Environment Variables:
    UVICORN_WORKERS         Number of workers
    UVICORN_HOST           Host to bind to
    UVICORN_PORT           Port to bind to
    SKIP_CHECKS            Skip pre-startup checks
    USE_DOCKER             Use Docker deployment

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -H|--host)
            HOST="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -s|--skip-checks)
            SKIP_CHECKS=true
            shift
            ;;
        -d|--docker)
            USE_DOCKER=true
            shift
            ;;
        --stop)
            ACTION=stop
            shift
            ;;
        --restart)
            ACTION=restart
            shift
            ;;
        --status)
            ACTION=status
            shift
            ;;
        *)
            error "Unknown option: $1. Use --help for usage information."
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

# Create necessary directories
mkdir -p logs reports/patent data/raw cache/patent tmp

# Handle different actions
case ${ACTION:-start} in
    stop)
        info "Stopping Patent MVP System..."
        if [[ "$USE_DOCKER" == "true" ]]; then
            docker-compose down
        else
            if [[ -f "$PID_FILE" ]]; then
                PID=$(cat "$PID_FILE")
                if kill -0 "$PID" 2>/dev/null; then
                    kill "$PID"
                    success "Service stopped (PID: $PID)"
                    rm -f "$PID_FILE"
                else
                    warning "Service was not running"
                    rm -f "$PID_FILE"
                fi
            else
                warning "PID file not found, service may not be running"
            fi
        fi
        exit 0
        ;;
    status)
        info "Checking Patent MVP System status..."
        if [[ "$USE_DOCKER" == "true" ]]; then
            docker-compose ps
        else
            if [[ -f "$PID_FILE" ]]; then
                PID=$(cat "$PID_FILE")
                if kill -0 "$PID" 2>/dev/null; then
                    success "Service is running (PID: $PID)"
                    # Check if service is responding
                    if curl -f "http://$HOST:$PORT/health" >/dev/null 2>&1; then
                        success "Service is healthy and responding"
                    else
                        warning "Service is running but not responding to health checks"
                    fi
                else
                    warning "Service is not running (stale PID file)"
                    rm -f "$PID_FILE"
                fi
            else
                warning "Service is not running (no PID file)"
            fi
        fi
        exit 0
        ;;
    restart)
        info "Restarting Patent MVP System..."
        $0 --stop
        sleep 2
        $0 "${@:1:$#-1}"  # Pass all arguments except --restart
        exit 0
        ;;
esac

# Main startup process
log "🚀 Starting Patent MVP System in Production Mode..." "$GREEN"

# Check if already running
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    error "Service is already running (PID: $(cat "$PID_FILE")). Use --stop or --restart."
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    error "uv is not installed. Please install uv first. Visit: https://docs.astral.sh/uv/getting-started/installation/"
fi

UV_VERSION=$(uv --version)
success "uv is installed: $UV_VERSION"

# Set production environment
export APP_ENV=production
export PYTHONPATH="$PROJECT_ROOT/src"

# Load production environment variables
if [[ -f ".env.production" ]]; then
    info "Loading production environment variables..."
    set -a
    source .env.production
    set +a
    success "Production environment loaded"
else
    warning ".env.production file not found. Using default settings."
fi

# Docker deployment
if [[ "$USE_DOCKER" == "true" ]]; then
    info "Starting Patent MVP System using Docker Compose..."
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed or not in PATH"
    fi
    
    # Build and start services
    info "Building Docker images..."
    docker-compose build --no-cache
    
    info "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    info "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    if docker-compose exec -T patent-service curl -f http://localhost:8000/health >/dev/null 2>&1; then
        success "Patent MVP System is running with Docker"
        info "Application available at: http://$HOST:$PORT"
        info "API documentation: http://$HOST:$PORT/docs"
        info "Use 'docker-compose logs -f' to view logs"
        info "Use '$0 --stop --docker' to stop services"
    else
        error "Service health check failed"
    fi
    
    exit 0
fi

# Native deployment with uv
if [[ "$SKIP_CHECKS" != "true" ]]; then
    # Validate required environment variables
    required_vars=("DATABASE_URL" "REDIS_URL")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            error "Required environment variable $var is not set"
        fi
    done
    success "Required environment variables validated"

    # Check database connectivity
    info "Checking database connectivity..."
    if uv run python -c "
import asyncio
import sys
from src.multi_agent_service.infrastructure.database import Database

async def check_db():
    try:
        db = Database()
        await db.connect()
        await db.disconnect()
        return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False

result = asyncio.run(check_db())
sys.exit(0 if result else 1)
" 2>/dev/null; then
        success "Database connectivity verified"
    else
        error "Database connectivity check failed. Please check your database configuration."
    fi

    # Check Redis connectivity
    info "Checking Redis connectivity..."
    if uv run python -c "
import redis
import sys
import os

try:
    r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    r.ping()
    sys.exit(0)
except Exception as e:
    print(f'Redis connection failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
        success "Redis connectivity verified"
    else
        error "Redis connectivity check failed. Please check your Redis configuration."
    fi

    # Run database migrations
    info "Running database migrations..."
    if [[ -f "alembic.ini" ]]; then
        uv run alembic upgrade head
        success "Database migrations completed"
    else
        info "No alembic configuration found, skipping migrations"
    fi

    # Validate agent configurations
    info "Validating agent configurations..."
    if uv run python -c "
import sys
from src.multi_agent_service.core.config_manager import ConfigManager

try:
    config_manager = ConfigManager()
    agents = config_manager.load_agents_config()
    workflows = config_manager.load_workflows_config()
    print(f'Loaded {len(agents)} agents and {len(workflows)} workflows')
    sys.exit(0)
except Exception as e:
    print(f'Configuration validation failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
        success "Agent configurations validated"
    else
        error "Agent configuration validation failed"
    fi
fi

# Start the application
info "Starting Patent MVP System..."
success "Application will be available at: http://$HOST:$PORT"
success "Health check endpoint: http://$HOST:$PORT/health"
success "API documentation: http://$HOST:$PORT/docs"
info "Workers: $WORKERS"
info "Log file: $LOG_FILE"

# Start uvicorn with uv and capture PID
uv run uvicorn src.multi_agent_service.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --loop uvloop \
    --http httptools \
    --access-log \
    --log-level info \
    --no-use-colors \
    --log-config logging.conf 2>&1 | tee -a "$LOG_FILE" &

# Save PID
echo $! > "$PID_FILE"
success "Patent MVP System started successfully (PID: $!)"

# Wait a moment and check if the process is still running
sleep 3
if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    success "Service is running and healthy"
    info "Use '$0 --stop' to stop the service"
    info "Use '$0 --status' to check service status"
    info "Use 'tail -f $LOG_FILE' to view logs"
else
    error "Service failed to start. Check logs for details: $LOG_FILE"
fi