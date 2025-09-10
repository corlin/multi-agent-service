#!/bin/bash

# Patent MVP System Production Startup Script
# This script starts the patent analysis system in production mode using uv

set -e

echo "🚀 Starting Patent MVP System in Production Mode..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first."
    echo "Visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Set production environment
export APP_ENV=production
export PYTHONPATH="$(pwd)/src"

# Load production environment variables
if [ -f ".env.production" ]; then
    echo "📋 Loading production environment variables..."
    set -a
    source .env.production
    set +a
else
    echo "⚠️  Warning: .env.production file not found. Using default settings."
fi

# Validate required environment variables
required_vars=("DATABASE_URL" "REDIS_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set."
        exit 1
    fi
done

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs reports/patent data/raw

# Check database connectivity
echo "🔍 Checking database connectivity..."
if ! uv run python -c "
import asyncio
import sys
from src.multi_agent_service.infrastructure.database import Database

async def check_db():
    try:
        db = Database()
        await db.connect()
        await db.disconnect()
        print('✅ Database connection successful')
        return True
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False

result = asyncio.run(check_db())
sys.exit(0 if result else 1)
"; then
    echo "✅ Database connectivity verified"
else
    echo "❌ Database connectivity check failed. Please check your database configuration."
    exit 1
fi

# Check Redis connectivity
echo "🔍 Checking Redis connectivity..."
if ! uv run python -c "
import redis
import sys
import os

try:
    r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    r.ping()
    print('✅ Redis connection successful')
    sys.exit(0)
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    sys.exit(1)
"; then
    echo "✅ Redis connectivity verified"
else
    echo "❌ Redis connectivity check failed. Please check your Redis configuration."
    exit 1
fi

# Run database migrations (if any)
echo "🔄 Running database migrations..."
if [ -f "alembic.ini" ]; then
    uv run alembic upgrade head
    echo "✅ Database migrations completed"
else
    echo "ℹ️  No alembic configuration found, skipping migrations"
fi

# Validate agent configurations
echo "🤖 Validating agent configurations..."
if ! uv run python -c "
import sys
from src.multi_agent_service.core.config_manager import ConfigManager

try:
    config_manager = ConfigManager()
    agents = config_manager.load_agents_config()
    workflows = config_manager.load_workflows_config()
    print(f'✅ Loaded {len(agents)} agents and {len(workflows)} workflows')
    sys.exit(0)
except Exception as e:
    print(f'❌ Configuration validation failed: {e}')
    sys.exit(1)
"; then
    echo "✅ Agent configurations validated"
else
    echo "❌ Agent configuration validation failed."
    exit 1
fi

# Start the application
echo "🎯 Starting Patent MVP System..."
echo "📊 Application will be available at: http://0.0.0.0:8000"
echo "📋 Health check endpoint: http://0.0.0.0:8000/health"
echo "📚 API documentation: http://0.0.0.0:8000/docs"

# Use uv to run the application with production settings
exec uv run uvicorn src.multi_agent_service.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers ${UVICORN_WORKERS:-4} \
    --loop uvloop \
    --http httptools \
    --access-log \
    --log-level info \
    --no-use-colors