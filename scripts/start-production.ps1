# Patent MVP System Production Startup Script for Windows PowerShell
# This script starts the patent analysis system in production mode using uv

param(
    [switch]$SkipChecks = $false,
    [string]$Port = "8000",
    [string]$Host = "0.0.0.0"
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Patent MVP System in Production Mode..." -ForegroundColor Green

# Check if uv is installed
try {
    $uvVersion = uv --version
    Write-Host "✅ uv is installed: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: uv is not installed. Please install uv first." -ForegroundColor Red
    Write-Host "Visit: https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Set production environment
$env:APP_ENV = "production"
$env:PYTHONPATH = Join-Path $PWD "src"

# Load production environment variables
$envFile = ".env.production"
if (Test-Path $envFile) {
    Write-Host "📋 Loading production environment variables..." -ForegroundColor Cyan
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
} else {
    Write-Host "⚠️  Warning: .env.production file not found. Using default settings." -ForegroundColor Yellow
}

# Validate required environment variables
$requiredVars = @("DATABASE_URL", "REDIS_URL")
foreach ($var in $requiredVars) {
    if (-not [Environment]::GetEnvironmentVariable($var)) {
        Write-Host "❌ Error: Required environment variable $var is not set." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Create necessary directories
Write-Host "📁 Creating necessary directories..." -ForegroundColor Cyan
$directories = @("logs", "reports\patent", "data\raw")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

if (-not $SkipChecks) {
    # Check database connectivity
    Write-Host "🔍 Checking database connectivity..." -ForegroundColor Cyan
    try {
        $dbCheck = uv run python -c @"
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
"@
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Database connectivity verified" -ForegroundColor Green
        } else {
            throw "Database check failed"
        }
    } catch {
        Write-Host "❌ Database connectivity check failed. Please check your database configuration." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }

    # Check Redis connectivity
    Write-Host "🔍 Checking Redis connectivity..." -ForegroundColor Cyan
    try {
        $redisCheck = uv run python -c @"
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
"@
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Redis connectivity verified" -ForegroundColor Green
        } else {
            throw "Redis check failed"
        }
    } catch {
        Write-Host "❌ Redis connectivity check failed. Please check your Redis configuration." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }

    # Validate agent configurations
    Write-Host "🤖 Validating agent configurations..." -ForegroundColor Cyan
    try {
        $configCheck = uv run python -c @"
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
"@
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Agent configurations validated" -ForegroundColor Green
        } else {
            throw "Configuration check failed"
        }
    } catch {
        Write-Host "❌ Agent configuration validation failed." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Start the application
Write-Host "🎯 Starting Patent MVP System..." -ForegroundColor Green
Write-Host "📊 Application will be available at: http://${Host}:${Port}" -ForegroundColor Cyan
Write-Host "📋 Health check endpoint: http://${Host}:${Port}/health" -ForegroundColor Cyan
Write-Host "📚 API documentation: http://${Host}:${Port}/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Use uv to run the application with production settings
try {
    uv run uvicorn src.multi_agent_service.main:app --host $Host --port $Port --workers 2 --access-log --log-level info
} catch {
    Write-Host "❌ Failed to start the application: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}