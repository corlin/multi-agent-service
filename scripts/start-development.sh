#!/bin/bash

# Patent MVP System Development Startup Script
# This script starts the patent analysis system in development mode using uv

set -e

echo "🛠️  Starting Patent MVP System in Development Mode..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first."
    echo "Visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Set development environment
export APP_ENV=development
export PYTHONPATH="$(pwd)/src"

# Load development environment variables
if [ -f ".env.development" ]; then
    echo "📋 Loading development environment variables..."
    set -a
    source .env.development
    set +a
else
    echo "⚠️  Warning: .env.development file not found. Creating default..."
    cp .env.example .env.development 2>/dev/null || echo "No .env.example found"
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
if [ ! -d ".venv" ] || [ ! -f "uv.lock" ]; then
    echo "🔄 Installing dependencies with uv..."
    uv sync --dev
else
    echo "✅ Dependencies already installed"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs reports/patent data/raw tests/temp

# Start development services (if using docker-compose)
if command -v docker-compose &> /dev/null && [ -f "docker-compose.dev.yml" ]; then
    echo "🐳 Starting development services (PostgreSQL, Redis)..."
    docker-compose -f docker-compose.dev.yml up -d postgres redis
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to be ready..."
    sleep 5
    
    # Check if services are running
    if docker-compose -f docker-compose.dev.yml ps postgres | grep -q "Up"; then
        echo "✅ PostgreSQL is running"
    else
        echo "⚠️  PostgreSQL may not be ready yet"
    fi
    
    if docker-compose -f docker-compose.dev.yml ps redis | grep -q "Up"; then
        echo "✅ Redis is running"
    else
        echo "⚠️  Redis may not be ready yet"
    fi
fi

# Run tests to ensure everything is working
echo "🧪 Running quick health check tests..."
if uv run pytest tests/test_startup.py -v --tb=short 2>/dev/null; then
    echo "✅ Health check tests passed"
else
    echo "⚠️  Some health check tests failed, but continuing..."
fi

# Validate configurations
echo "🤖 Validating development configurations..."
uv run python -c "
try:
    from src.multi_agent_service.core.config_manager import ConfigManager
    config_manager = ConfigManager()
    print('✅ Configuration manager initialized successfully')
except Exception as e:
    print(f'⚠️  Configuration warning: {e}')
" || echo "⚠️  Configuration validation had issues, but continuing..."

# Start the application with hot reload
echo "🎯 Starting Patent MVP System in Development Mode..."
echo "📊 Application will be available at: http://localhost:8000"
echo "📋 Health check endpoint: http://localhost:8000/health"
echo "📚 API documentation: http://localhost:8000/docs"
echo "🔄 Hot reload is enabled - changes will be automatically detected"
echo ""
echo "💡 Development Tips:"
echo "   - Use 'uv run pytest' to run tests"
echo "   - Use 'uv run black src/' to format code"
echo "   - Use 'uv run mypy src/' for type checking"
echo "   - Press Ctrl+C to stop the server"
echo ""

# Use uv to run the application with development settings
exec uv run uvicorn src.multi_agent_service.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir src \
    --reload-dir config \
    --log-level debug \
    --access-log