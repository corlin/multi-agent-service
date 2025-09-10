# Patent MVP System Environment Validation Script for Windows PowerShell
# This script validates the deployment environment for patent analysis system

param(
    [switch]$Help = $false
)

# Set error action preference
$ErrorActionPreference = "Continue"

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Color functions
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Message"
    Write-Host $logMessage -ForegroundColor $Color
}

function Write-Error-Custom {
    param([string]$Message)
    Write-ColorOutput "❌ ERROR: $Message" "Red"
    return $false
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
Patent MVP System Environment Validation Script for Windows

Usage: .\validate-environment.ps1 [OPTIONS]

Options:
    -Help                   Show this help message

This script validates:
    - uv installation and functionality
    - Python installation and version
    - System dependencies
    - Docker installation (optional)
    - Project structure
    - Python dependencies
    - Environment configuration
    - Port availability
    - File permissions

Examples:
    .\validate-environment.ps1              Run full environment validation

"@
}

# Show help if requested
if ($Help) {
    Show-Help
    exit 0
}

# Validation functions
function Test-UvInstallation {
    Write-Info "Validating uv installation..."
    
    try {
        $uvVersion = uv --version
        Write-Success "uv is installed: $uvVersion"
        
        # Check if uv can create virtual environments
        try {
            uv venv --help | Out-Null
            Write-Success "uv virtual environment support available"
        } catch {
            Write-Warning-Custom "uv virtual environment support may be limited"
        }
        
        return $true
    } catch {
        Write-Error-Custom "uv is not installed. Please install uv first."
        Write-Host "Visit: https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Yellow
        return $false
    }
}

function Test-PythonInstallation {
    Write-Info "Validating Python installation..."
    
    try {
        $pythonVersion = python --version 2>$null
        if (-not $pythonVersion) {
            $pythonVersion = python3 --version 2>$null
        }
        
        if (-not $pythonVersion) {
            Write-Error-Custom "Python is not installed or not in PATH"
            return $false
        }
        
        Write-Success "Python is installed: $pythonVersion"
        
        # Check Python version (require 3.12+)
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $majorVersion = [int]$matches[1]
            $minorVersion = [int]$matches[2]
            
            if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 12)) {
                Write-Error-Custom "Python 3.12+ is required, found $pythonVersion"
                return $false
            }
            
            Write-Success "Python version meets requirements (3.12+)"
        }
        
        return $true
    } catch {
        Write-Error-Custom "Failed to check Python installation: $_"
        return $false
    }
}

function Test-SystemDependencies {
    Write-Info "Validating system dependencies..."
    
    $missingDeps = @()
    
    # Check for required system tools
    $requiredTools = @("git", "curl")
    
    foreach ($tool in $requiredTools) {
        try {
            & $tool --version 2>$null | Out-Null
            if ($LASTEXITCODE -ne 0) {
                $missingDeps += $tool
            }
        } catch {
            $missingDeps += $tool
        }
    }
    
    if ($missingDeps.Count -gt 0) {
        Write-Error-Custom "Missing required system tools: $($missingDeps -join ', ')"
        Write-Host "Please install them:" -ForegroundColor Yellow
        Write-Host "  Git: https://git-scm.com/download/win" -ForegroundColor Yellow
        Write-Host "  curl: Usually included with Windows 10+ or install via chocolatey" -ForegroundColor Yellow
        return $false
    }
    
    Write-Success "All required system dependencies are installed"
    return $true
}

function Test-DockerInstallation {
    Write-Info "Validating Docker installation (optional)..."
    
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Success "Docker is installed: $dockerVersion"
            
            # Check if Docker daemon is running
            try {
                docker info 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "Docker daemon is running"
                } else {
                    Write-Warning-Custom "Docker is installed but daemon is not running"
                }
            } catch {
                Write-Warning-Custom "Docker daemon status unknown"
            }
            
            # Check Docker Compose
            try {
                $composeVersion = docker-compose --version 2>$null
                if ($composeVersion) {
                    Write-Success "Docker Compose is installed: $composeVersion"
                } else {
                    Write-Warning-Custom "Docker Compose is not installed"
                }
            } catch {
                Write-Warning-Custom "Docker Compose is not installed"
            }
        } else {
            Write-Info "Docker is not installed (optional for development)"
        }
    } catch {
        Write-Info "Docker is not installed (optional for development)"
    }
    
    return $true
}

function Test-ProjectStructure {
    Write-Info "Validating project structure..."
    
    Set-Location $ProjectRoot
    
    $requiredFiles = @(
        "pyproject.toml",
        "src\multi_agent_service\main.py",
        "config\agents.json",
        "config\workflows.json"
    )
    
    $missingFiles = @()
    
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            $missingFiles += $file
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Error-Custom "Missing required project files: $($missingFiles -join ', ')"
        return $false
    }
    
    Write-Success "Project structure is valid"
    
    # Check for required directories
    $requiredDirs = @(
        "src\multi_agent_service",
        "config",
        "templates",
        "logs",
        "reports",
        "data"
    )
    
    foreach ($dir in $requiredDirs) {
        if (-not (Test-Path $dir)) {
            Write-Info "Creating missing directory: $dir"
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Success "All required directories exist"
    return $true
}

function Test-Dependencies {
    Write-Info "Validating Python dependencies..."
    
    Set-Location $ProjectRoot
    
    # Check if uv.lock exists
    if (-not (Test-Path "uv.lock")) {
        Write-Warning-Custom "uv.lock not found, dependencies may not be locked"
    } else {
        Write-Success "uv.lock found"
    }
    
    # Try to sync dependencies (dry run)
    try {
        uv sync --dry-run 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Dependencies can be resolved"
        } else {
            Write-Error-Custom "Dependency resolution failed"
            Write-Host "Try running: uv sync" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Error-Custom "Failed to check dependencies: $_"
        return $false
    }
    
    return $true
}

function Test-EnvironmentFiles {
    Write-Info "Validating environment configuration..."
    
    Set-Location $ProjectRoot
    
    # Check for environment files
    if (Test-Path ".env.example") {
        Write-Success ".env.example found"
    } else {
        Write-Warning-Custom ".env.example not found"
    }
    
    if (Test-Path ".env.development") {
        Write-Success ".env.development found"
    } else {
        Write-Info "Creating .env.development from .env.example"
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env.development"
            Write-Success ".env.development created"
        } else {
            Write-Warning-Custom ".env.development not created (no .env.example)"
        }
    }
    
    if (Test-Path ".env.production") {
        Write-Success ".env.production found"
    } else {
        Write-Warning-Custom ".env.production not found (created by deployment script)"
    }
    
    return $true
}

function Test-PortAvailability {
    Write-Info "Validating port availability..."
    
    $ports = @(8000, 5432, 6379)
    $occupiedPorts = @()
    
    foreach ($port in $ports) {
        try {
            $connection = New-Object System.Net.Sockets.TcpClient
            $connection.Connect("localhost", $port)
            $connection.Close()
            $occupiedPorts += $port
        } catch {
            # Port is available (connection failed)
        }
    }
    
    if ($occupiedPorts.Count -gt 0) {
        Write-Warning-Custom "The following ports are already in use: $($occupiedPorts -join ', ')"
        Write-Host "This may cause conflicts during deployment." -ForegroundColor Yellow
        Write-Host "Consider stopping services using these ports or changing configuration." -ForegroundColor Yellow
    } else {
        Write-Success "All required ports (8000, 5432, 6379) are available"
    }
    
    return $true
}

function Test-FilePermissions {
    Write-Info "Validating file permissions..."
    
    Set-Location $ProjectRoot
    
    # Check write permissions for required directories
    $writeDirs = @(
        "logs",
        "reports",
        "data",
        "cache",
        "tmp"
    )
    
    foreach ($dir in $writeDirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        
        try {
            $testFile = Join-Path $dir "test_write_permission.tmp"
            "test" | Out-File -FilePath $testFile -Force
            Remove-Item $testFile -Force
            Write-Success "Write permission OK for $dir"
        } catch {
            Write-Error-Custom "No write permission for $dir"
            return $false
        }
    }
    
    # Check PowerShell execution policy
    $executionPolicy = Get-ExecutionPolicy
    if ($executionPolicy -eq "Restricted") {
        Write-Warning-Custom "PowerShell execution policy is Restricted. You may need to run:"
        Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    } else {
        Write-Success "PowerShell execution policy allows script execution ($executionPolicy)"
    }
    
    return $true
}

# Main validation function
function Start-Validation {
    Write-ColorOutput "🔍 Starting Patent MVP System Environment Validation..." "Green"
    Write-Host ""
    
    $validationErrors = 0
    
    # Run all validations
    if (-not (Test-UvInstallation)) { $validationErrors++ }
    Write-Host ""
    
    if (-not (Test-PythonInstallation)) { $validationErrors++ }
    Write-Host ""
    
    if (-not (Test-SystemDependencies)) { $validationErrors++ }
    Write-Host ""
    
    if (-not (Test-DockerInstallation)) { $validationErrors++ }
    Write-Host ""
    
    if (-not (Test-ProjectStructure)) { $validationErrors++ }
    Write-Host ""
    
    if (-not (Test-Dependencies)) { $validationErrors++ }
    Write-Host ""
    
    if (-not (Test-EnvironmentFiles)) { $validationErrors++ }
    Write-Host ""
    
    if (-not (Test-PortAvailability)) { $validationErrors++ }
    Write-Host ""
    
    if (-not (Test-FilePermissions)) { $validationErrors++ }
    Write-Host ""
    
    # Summary
    if ($validationErrors -eq 0) {
        Write-Success "🎉 Environment validation completed successfully!"
        Write-Success "Your system is ready for Patent MVP System deployment."
        Write-Host ""
        Write-Info "Next steps:"
        Write-Host "  1. Run '.\scripts\start-development.ps1' for development" -ForegroundColor Cyan
        Write-Host "  2. Run '.\scripts\start-patent-production.ps1' for production" -ForegroundColor Cyan
        Write-Host "  3. Run '.\scripts\start-patent-production.ps1 -UseDocker' for Docker deployment" -ForegroundColor Cyan
        return $true
    } else {
        Write-Error-Custom "❌ Environment validation failed with $validationErrors error(s)"
        Write-Error-Custom "Please fix the issues above before deploying the Patent MVP System."
        return $false
    }
}

# Run validation
$result = Start-Validation
if (-not $result) {
    exit 1
}