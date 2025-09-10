#!/bin/bash

# Docker Health Check Script for Patent MVP System
# This script performs comprehensive health checks for the containerized application

set -e

# Configuration
HEALTH_ENDPOINT="http://localhost:8000/health"
TIMEOUT=10
MAX_RETRIES=3

echo "🏥 Running Docker health check for Patent MVP System..."

# Function to check HTTP endpoint
check_http_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    
    echo "🔍 Checking endpoint: $url"
    
    for i in $(seq 1 $MAX_RETRIES); do
        if response=$(curl -s -w "%{http_code}" -o /tmp/health_response --max-time $TIMEOUT "$url" 2>/dev/null); then
            status_code="${response: -3}"
            
            if [ "$status_code" = "$expected_status" ]; then
                echo "✅ Endpoint $url returned status $status_code"
                return 0
            else
                echo "⚠️  Endpoint $url returned status $status_code (expected $expected_status)"
            fi
        else
            echo "❌ Failed to connect to $url (attempt $i/$MAX_RETRIES)"
        fi
        
        if [ $i -lt $MAX_RETRIES ]; then
            sleep 2
        fi
    done
    
    return 1
}

# Function to check database connectivity
check_database() {
    echo "🔍 Checking database connectivity..."
    
    if uv run python -c "
import asyncio
import sys
import os
from src.multi_agent_service.infrastructure.database import Database

async def check_db():
    try:
        db = Database()
        await db.connect()
        await db.disconnect()
        return True
    except Exception as e:
        print(f'Database error: {e}', file=sys.stderr)
        return False

result = asyncio.run(check_db())
sys.exit(0 if result else 1)
" 2>/dev/null; then
        echo "✅ Database connectivity OK"
        return 0
    else
        echo "❌ Database connectivity failed"
        return 1
    fi
}

# Function to check Redis connectivity
check_redis() {
    echo "🔍 Checking Redis connectivity..."
    
    if uv run python -c "
import redis
import sys
import os

try:
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    r = redis.from_url(redis_url, socket_timeout=5)
    r.ping()
    sys.exit(0)
except Exception as e:
    print(f'Redis error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
        echo "✅ Redis connectivity OK"
        return 0
    else
        echo "❌ Redis connectivity failed"
        return 1
    fi
}

# Function to check agent registry
check_agent_registry() {
    echo "🔍 Checking agent registry..."
    
    if uv run python -c "
import sys
try:
    from src.multi_agent_service.agents.registry import AgentRegistry
    registry = AgentRegistry()
    agent_count = len(registry.list_agents())
    print(f'Loaded {agent_count} agents')
    sys.exit(0)
except Exception as e:
    print(f'Agent registry error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
        echo "✅ Agent registry OK"
        return 0
    else
        echo "❌ Agent registry check failed"
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    echo "🔍 Checking disk space..."
    
    # Check available disk space (require at least 1GB free)
    available_space=$(df /app | tail -1 | awk '{print $4}')
    required_space=1048576  # 1GB in KB
    
    if [ "$available_space" -gt "$required_space" ]; then
        echo "✅ Sufficient disk space available ($(($available_space / 1024))MB free)"
        return 0
    else
        echo "❌ Insufficient disk space ($(($available_space / 1024))MB free, need at least 1GB)"
        return 1
    fi
}

# Function to check memory usage
check_memory() {
    echo "🔍 Checking memory usage..."
    
    # Check if memory usage is reasonable (less than 90%)
    memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    
    if [ "$memory_usage" -lt 90 ]; then
        echo "✅ Memory usage OK (${memory_usage}%)"
        return 0
    else
        echo "⚠️  High memory usage (${memory_usage}%)"
        return 1
    fi
}

# Main health check execution
main() {
    local exit_code=0
    
    echo "🏥 Starting comprehensive health check..."
    echo "⏰ Timestamp: $(date)"
    echo ""
    
    # Core application health check
    if ! check_http_endpoint "$HEALTH_ENDPOINT"; then
        echo "❌ Main health endpoint check failed"
        exit_code=1
    fi
    
    # Database connectivity
    if ! check_database; then
        echo "❌ Database health check failed"
        exit_code=1
    fi
    
    # Redis connectivity
    if ! check_redis; then
        echo "❌ Redis health check failed"
        exit_code=1
    fi
    
    # Agent registry
    if ! check_agent_registry; then
        echo "⚠️  Agent registry check failed (non-critical)"
        # Don't fail the health check for agent registry issues
    fi
    
    # System resources
    if ! check_disk_space; then
        echo "❌ Disk space check failed"
        exit_code=1
    fi
    
    if ! check_memory; then
        echo "⚠️  Memory usage check warning (non-critical)"
        # Don't fail for memory warnings
    fi
    
    echo ""
    if [ $exit_code -eq 0 ]; then
        echo "✅ All critical health checks passed"
        echo "🎉 Patent MVP System is healthy"
    else
        echo "❌ Some critical health checks failed"
        echo "🚨 Patent MVP System is unhealthy"
    fi
    
    exit $exit_code
}

# Run the health check
main "$@"