# Patent MVP System Production Startup Script for Windows PowerShell
# This script provides comprehensive production deployment for patent analysis system

param(
    [int]$Workers = 4,
    [string]$Host = "0.0.0.0",
    [int]$Port = 8000,
    [switch]$SkipChecks = $false,
    [switch]$UseDocker = $false,
    [switch]$Stop = $false,
    [switch]$Restart = $false,
    [switch]$Status = $false,
    [switch]$Help = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$LogFile = Join-Path $ProjectRoot "logs\startup.log"
$PidFile = Join-Path $ProjectRoot "logs\patent-mvp.pid"

# Color functions
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $LogFile -Value $logMessage -ErrorAction SilentlyContinue
}

function Write-Error-Custom {
    param([string]$Message)
    Write-ColorOutput "❌ ERROR: $Message" "Red"
    exit 1
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-ColorOutput "⚠️  WARNING: $Message" "Yellow"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" "Green"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "ℹ️  $Message" "Cyan"
}

# Help function
function Show-Help {
    @"
Patent MVP System Production Startup Script for Windows

Usage: .\start-patent-production.ps1 [OPTIONS]

Options:
    -Workers NUM            Number of uvicorn workers (default: 4)
    -Host HOST              Host to bind to (default: 0.0.0.0)
    -Port PORT              Port to bind to (default: 8000)
    -SkipChecks             Skip pre-startup checks
    -UseDocker              Use Docker deployment
    -Stop                   Stop running service
    -Restart                Restart service
    -Status                 Show service status
    -Help                   Show this help message

Examples:
    .\start-patent-production.ps1                           Start with default settings
    .\start-patent-production.ps1 -Workers 8 -Port 8080    Start with 8 workers on port 8080
    .\start-patent-production.ps1 -UseDocker               Start using Docker Compose
    .\start-patent-production.ps1 -Stop                    Stop the service
    .\start-patent-production.ps1 -Status                  Check service status

Environment Variables:
    UVICORN_WORKERS         Number of workers
    UVICORN_HOST           Host to bind to
    UVICORN_PORT           Port to bind to

"@
}

# Show help if requested
if ($Help) {
    Show-Help
    exit 0
}

# Change to project root
Set-Location $ProjectRoot

# Create necessary directories
$directories = @("logs", "reports\patent", "data\raw", "cache\patent", "tmp")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Handle different actions
if ($Stop) {
    Write-Info "Stopping Patent MVP System..."
    if ($UseDocker) {
        docker-compose down
    } else {
        if (Test-Path $PidFile) {
            $pid = Get-Content $PidFile
            try {
                Stop-Process -Id $pid -Force
                Write-Success "Service stopped (PID: $pid)"
                Remove-Item $PidFile -Force
            } catch {
                Write-Warning-Custom "Could not stop process $pid - it may have already stopped"
                Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
            }
        } else {
            Write-Warning-Custom "PID file not found, service may not be running"
        }
    }
    exit 0
}

if ($Status) {
    Write-Info "Checking Patent MVP System status..."
    if ($UseDocker) {
        docker-compose ps
    } else {
        if (Test-Path $PidFile) {
            $pid = Get-Content $PidFile
            try {
                $process = Get-Process -Id $pid -ErrorAction Stop
                Write-Success "Service is running (PID: $pid)"
                # Check if service is responding
                try {
                    $response = Invoke-WebRequest -Uri "http://${Host}:${Port}/health" -TimeoutSec 5 -UseBasicParsing
                    if ($response.StatusCode -eq 200) {
                        Write-Success "Service is healthy and responding"
                    } else {
                        Write-Warning-Custom "Service is running but not responding correctly to health checks"
                    }
                } catch {
                    Write-Warning-Custom "Service is running but not responding to health checks"
                }
            } catch {
                Write-Warning-Custom "Service is not running (stale PID file)"
                Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
            }
        } else {
            Write-Warning-Custom "Service is not running (no PID file)"
        }
    }
    exit 0
}

if ($Restart) {
    Write-Info "Restarting Patent MVP System..."
    & $MyInvocation.MyCommand.Path -Stop -UseDocker:$UseDocker
    Start-Sleep -Seconds 2
    & $MyInvocation.MyCommand.Path -Workers $Workers -Host $Host -Port $Port -SkipChecks:$SkipChecks -UseDocker:$UseDocker
    exit 0
}

# Main startup process
Write-ColorOutput "🚀 Starting Patent MVP System in Production Mode..." "Green"

# Check if already running
if ((Test-Path $PidFile)) {
    $pid = Get-Content $PidFile
    try {
        $process = Get-Process -Id $pid -ErrorAction Stop
        Write-Error-Custom "Service is already running (PID: $pid). Use -Stop or -Restart."
    } catch {
        # Process not running, remove stale PID file
        Remove-Item $PidFile -Force
    }
}

# Check if uv is installed
try {
    $uvVersion = uv --version
    Write-Success "uv is installed: $uvVersion"
} catch {
    Write-Error-Custom "uv is not installed. Please install uv first. Visit: https://docs.astral.sh/uv/getting-started/installation/"
}

# Set production environment
$env:APP_ENV = "production"
$env:PYTHONPATH = Join-Path $ProjectRoot "src"

# Load production environment variables
$envFile = ".env.production"
if (Test-Path $envFile) {
    Write-Info "Loading production environment variables..."
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
    Write-Success "Production environment loaded"
} else {
    Write-Warning-Custom ".env.production file not found. Using default settings."
}

# Override with command line parameters
if ($env:UVICORN_WORKERS) { $Workers = [int]$env:UVICORN_WORKERS }
if ($env:UVICORN_HOST) { $Host = $env:UVICORN_HOST }
if ($env:UVICORN_PORT) { $Port = [int]$env:UVICORN_PORT }

# Docker deployment
if ($UseDocker) {
    Write-Info "Starting Patent MVP System using Docker Compose..."
    
    # Check if Docker is available
    try {
        docker --version | Out-Null
    } catch {
        Write-Error-Custom "Docker is not installed or not in PATH"
    }
    
    try {
        docker-compose --version | Out-Null
    } catch {
        Write-Error-Custom "Docker Compose is not installed or not in PATH"
    }
    
    # Build and start services
    Write-Info "Building Docker images..."
    docker-compose build --no-cache
    
    Write-Info "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    Write-Info "Waiting for services to be ready..."
    Start-Sleep -Seconds 10
    
    # Check service health
    try {
        $response = Invoke-WebRequest -Uri "http://${Host}:${Port}/health" -TimeoutSec 30 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Success "Patent MVP System is running with Docker"
            Write-Info "Application available at: http://${Host}:${Port}"
            Write-Info "API documentation: http://${Host}:${Port}/docs"
            Write-Info "Use 'docker-compose logs -f' to view logs"
            Write-Info "Use '.\start-patent-production.ps1 -Stop -UseDocker' to stop services"
        } else {
            Write-Error-Custom "Service health check failed"
        }
    } catch {
        Write-Error-Custom "Service health check failed: $_"
    }
    
    exit 0
}

# Native deployment with uv
if (-not $SkipChecks) {
    # Validate required environment variables
    $requiredVars = @("DATABASE_URL", "REDIS_URL")
    foreach ($var in $requiredVars) {
        if (-not [Environment]::GetEnvironmentVariable($var)) {
            Write-Error-Custom "Required environment variable $var is not set"
        }
    }
    Write-Success "Required environment variables validated"

    # Check database connectivity
    Write-Info "Checking database connectivity..."
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
        return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False

result = asyncio.run(check_db())
sys.exit(0 if result else 1)
"@
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Database connectivity verified"
        } else {
            Write-Error-Custom "Database connectivity check failed. Please check your database configuration."
        }
    } catch {
        Write-Error-Custom "Database connectivity check failed: $_"
    }

    # Check Redis connectivity
    Write-Info "Checking Redis connectivity..."
    try {
        $redisCheck = uv run python -c @"
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
"@
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Redis connectivity verified"
        } else {
            Write-Error-Custom "Redis connectivity check failed. Please check your Redis configuration."
        }
    } catch {
        Write-Error-Custom "Redis connectivity check failed: $_"
    }

    # Run database migrations
    Write-Info "Running database migrations..."
    if (Test-Path "alembic.ini") {
        try {
            uv run alembic upgrade head
            Write-Success "Database migrations completed"
        } catch {
            Write-Warning-Custom "Database migrations failed: $_"
        }
    } else {
        Write-Info "No alembic configuration found, skipping migrations"
    }

    # Validate agent configurations
    Write-Info "Validating agent configurations..."
    try {
        $configCheck = uv run python -c @"
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
"@
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Agent configurations validated"
        } else {
            Write-Error-Custom "Agent configuration validation failed"
        }
    } catch {
        Write-Error-Custom "Agent configuration validation failed: $_"
    }
}

# Start the application
Write-Info "Starting Patent MVP System..."
Write-Success "Application will be available at: http://${Host}:${Port}"
Write-Success "Health check endpoint: http://${Host}:${Port}/health"
Write-Success "API documentation: http://${Host}:${Port}/docs"
Write-Info "Workers: $Workers"
Write-Info "Log file: $LogFile"

# Start uvicorn with uv
try {
    $process = Start-Process -FilePath "uv" -ArgumentList @(
        "run", "uvicorn", "src.multi_agent_service.main:app",
        "--host", $Host,
        "--port", $Port,
        "--workers", $Workers,
        "--access-log",
        "--log-level", "info"
    ) -PassThru -NoNewWindow

    # Save PID
    $process.Id | Out-File -FilePath $PidFile -Encoding utf8
    Write-Success "Patent MVP System started successfully (PID: $($process.Id))"

    # Wait a moment and check if the process is still running
    Start-Sleep -Seconds 3
    if (-not $process.HasExited) {
        Write-Success "Service is running and healthy"
        Write-Info "Use '.\start-patent-production.ps1 -Stop' to stop the service"
        Write-Info "Use '.\start-patent-production.ps1 -Status' to check service status"
        Write-Info "Use 'Get-Content $LogFile -Wait' to view logs"
        
        # Keep the script running to monitor the process
        Write-Info "Press Ctrl+C to stop the service"
        try {
            $process.WaitForExit()
        } catch {
            Write-Info "Service monitoring interrupted"
        } finally {
            if (Test-Path $PidFile) {
                Remove-Item $PidFile -Force
            }
        }
    } else {
        Write-Error-Custom "Service failed to start. Check logs for details: $LogFile"
    }
} catch {
    Write-Error-Custom "Failed to start service: $_"
}