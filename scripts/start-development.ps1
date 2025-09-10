# Patent MVP System Development Startup Script for Windows PowerShell
# This script starts the patent analysis system in development mode using uv

param(
    [string]$Port = "8000",
    [string]$Host = "0.0.0.0",
    [switch]$SkipTests = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🛠️  Starting Patent MVP System in Development Mode..." -ForegroundColor Green

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

# Set development environment
$env:APP_ENV = "development"
$env:PYTHONPATH = Join-Path $PWD "src"

# Load development environment variables
$envFile = ".env.development"
if (Test-Path $envFile) {
    Write-Host "📋 Loading development environment variables..." -ForegroundColor Cyan
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
} else {
    Write-Host "⚠️  Warning: .env.development file not found. Creating default..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env.development"
    }
}

# Install dependencies if needed
Write-Host "📦 Checking dependencies..." -ForegroundColor Cyan
if (-not (Test-Path ".venv") -or -not (Test-Path "uv.lock")) {
    Write-Host "🔄 Installing dependencies with uv..." -ForegroundColor Yellow
    try {
        uv sync --dev
        Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install dependencies: $_" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
}

# Create necessary directories
Write-Host "📁 Creating necessary directories..." -ForegroundColor Cyan
$directories = @("logs", "reports\patent", "data\raw", "tests\temp")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Run quick health check tests
if (-not $SkipTests) {
    Write-Host "🧪 Running quick health check tests..." -ForegroundColor Cyan
    try {
        uv run pytest tests/test_startup.py -v --tb=short 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Health check tests passed" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Some health check tests failed, but continuing..." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Could not run health check tests, but continuing..." -ForegroundColor Yellow
    }
}

# Validate configurations
Write-Host "🤖 Validating development configurations..." -ForegroundColor Cyan
try {
    $configCheck = uv run python -c @"
try:
    from src.multi_agent_service.core.config_manager import ConfigManager
    config_manager = ConfigManager()
    print('✅ Configuration manager initialized successfully')
except Exception as e:
    print(f'⚠️  Configuration warning: {e}')
"@
    Write-Host "✅ Configuration validation completed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Configuration validation had issues, but continuing..." -ForegroundColor Yellow
}

# Check if Redis is available (optional for development)
Write-Host "🔍 Checking Redis availability..." -ForegroundColor Cyan
try {
    $redisCheck = redis-cli ping 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Redis is running" -ForegroundColor Green
    } else {
        throw "Redis not available"
    }
} catch {
    Write-Host "⚠️  Redis is not running. You can:" -ForegroundColor Yellow
    Write-Host "   1. Install Redis for Windows from: https://github.com/microsoftarchive/redis/releases" -ForegroundColor Yellow
    Write-Host "   2. Use Docker: docker run -d -p 6379:6379 redis:alpine" -ForegroundColor Yellow
    Write-Host "   3. Continue without Redis (some features may be limited)" -ForegroundColor Yellow
}

# Start the application with hot reload
Write-Host "🎯 Starting Patent MVP System in Development Mode..." -ForegroundColor Green
Write-Host "📊 Application will be available at: http://${Host}:${Port}" -ForegroundColor Cyan
Write-Host "📋 Health check endpoint: http://${Host}:${Port}/health" -ForegroundColor Cyan
Write-Host "📚 API documentation: http://${Host}:${Port}/docs" -ForegroundColor Cyan
Write-Host "🔄 Hot reload is enabled - changes will be automatically detected" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Development Tips:" -ForegroundColor Yellow
Write-Host "   - Use 'uv run pytest' to run tests" -ForegroundColor Yellow
Write-Host "   - Use 'uv run black src/' to format code" -ForegroundColor Yellow
Write-Host "   - Use 'uv run mypy src/' for type checking" -ForegroundColor Yellow
Write-Host "   - Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Use uv to run the application with development settings
try {
    uv run uvicorn src.multi_agent_service.main:app --host $Host --port $Port --reload --reload-dir src --reload-dir config --log-level debug --access-log
} catch {
    Write-Host "❌ Failed to start the application: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}