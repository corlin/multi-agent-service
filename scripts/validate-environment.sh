#!/bin/bash

# Patent MVP System Environment Validation Script
# This script validates the deployment environment for patent analysis system

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Functions
log() {
    echo -e "${2:-$NC}$(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

error() {
    log "❌ ERROR: $1" "$RED"
    return 1
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

# Validation functions
validate_uv() {
    info "Validating uv installation..."
    
    if ! command -v uv &> /dev/null; then
        error "uv is not installed. Please install uv first."
        echo "Visit: https://docs.astral.sh/uv/getting-started/installation/"
        return 1
    fi
    
    UV_VERSION=$(uv --version)
    success "uv is installed: $UV_VERSION"
    
    # Check if uv can create virtual environments
    if uv venv --help &> /dev/null; then
        success "uv virtual environment support available"
    else
        warning "uv virtual environment support may be limited"
    fi
    
    return 0
}

validate_python() {
    info "Validating Python installation..."
    
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        error "Python is not installed or not in PATH"
        return 1
    fi
    
    # Get Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
    else
        PYTHON_VERSION=$(python --version)
    fi
    
    success "Python is installed: $PYTHON_VERSION"
    
    # Check Python version (require 3.12+)
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | sed 's/Python \([0-9]\+\)\.\([0-9]\+\).*/\1/')
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | sed 's/Python \([0-9]\+\)\.\([0-9]\+\).*/\2/')
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
        error "Python 3.12+ is required, found $PYTHON_VERSION"
        return 1
    fi
    
    success "Python version meets requirements (3.12+)"
    return 0
}

validate_system_dependencies() {
    info "Validating system dependencies..."
    
    local missing_deps=()
    
    # Check for required system packages
    local required_packages=(
        "curl"
        "git"
    )
    
    for package in "${required_packages[@]}"; do
        if ! command -v "$package" &> /dev/null; then
            missing_deps+=("$package")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        error "Missing required system packages: ${missing_deps[*]}"
        echo "Please install them using your system package manager:"
        echo "  Ubuntu/Debian: sudo apt-get install ${missing_deps[*]}"
        echo "  CentOS/RHEL: sudo yum install ${missing_deps[*]}"
        echo "  macOS: brew install ${missing_deps[*]}"
        return 1
    fi
    
    success "All required system dependencies are installed"
    return 0
}

validate_docker() {
    info "Validating Docker installation (optional)..."
    
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        success "Docker is installed: $DOCKER_VERSION"
        
        # Check if Docker daemon is running
        if docker info &> /dev/null; then
            success "Docker daemon is running"
        else
            warning "Docker is installed but daemon is not running"
        fi
        
        # Check Docker Compose
        if command -v docker-compose &> /dev/null; then
            COMPOSE_VERSION=$(docker-compose --version)
            success "Docker Compose is installed: $COMPOSE_VERSION"
        else
            warning "Docker Compose is not installed"
        fi
    else
        info "Docker is not installed (optional for development)"
    fi
    
    return 0
}

validate_project_structure() {
    info "Validating project structure..."
    
    cd "$PROJECT_ROOT"
    
    local required_files=(
        "pyproject.toml"
        "src/multi_agent_service/main.py"
        "config/agents.json"
        "config/workflows.json"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        error "Missing required project files: ${missing_files[*]}"
        return 1
    fi
    
    success "Project structure is valid"
    
    # Check for required directories
    local required_dirs=(
        "src/multi_agent_service"
        "config"
        "templates"
        "logs"
        "reports"
        "data"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            info "Creating missing directory: $dir"
            mkdir -p "$dir"
        fi
    done
    
    success "All required directories exist"
    return 0
}

validate_dependencies() {
    info "Validating Python dependencies..."
    
    cd "$PROJECT_ROOT"
    
    # Check if uv.lock exists
    if [ ! -f "uv.lock" ]; then
        warning "uv.lock not found, dependencies may not be locked"
    else
        success "uv.lock found"
    fi
    
    # Try to sync dependencies
    if uv sync --dry-run &> /dev/null; then
        success "Dependencies can be resolved"
    else
        error "Dependency resolution failed"
        echo "Try running: uv sync"
        return 1
    fi
    
    return 0
}

validate_environment_files() {
    info "Validating environment configuration..."
    
    cd "$PROJECT_ROOT"
    
    # Check for environment files
    if [ -f ".env.example" ]; then
        success ".env.example found"
    else
        warning ".env.example not found"
    fi
    
    if [ -f ".env.development" ]; then
        success ".env.development found"
    else
        info "Creating .env.development from .env.example"
        if [ -f ".env.example" ]; then
            cp ".env.example" ".env.development"
            success ".env.development created"
        else
            warning ".env.development not created (no .env.example)"
        fi
    fi
    
    if [ -f ".env.production" ]; then
        success ".env.production found"
    else
        warning ".env.production not found (created by deployment script)"
    fi
    
    return 0
}

validate_ports() {
    info "Validating port availability..."
    
    local ports=(8000 5432 6379)
    local occupied_ports=()
    
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            occupied_ports+=("$port")
        elif ss -tuln 2>/dev/null | grep -q ":$port "; then
            occupied_ports+=("$port")
        elif lsof -i ":$port" &>/dev/null; then
            occupied_ports+=("$port")
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        warning "The following ports are already in use: ${occupied_ports[*]}"
        echo "This may cause conflicts during deployment."
        echo "Consider stopping services using these ports or changing configuration."
    else
        success "All required ports (8000, 5432, 6379) are available"
    fi
    
    return 0
}

validate_permissions() {
    info "Validating file permissions..."
    
    cd "$PROJECT_ROOT"
    
    # Check write permissions for required directories
    local write_dirs=(
        "logs"
        "reports"
        "data"
        "cache"
        "tmp"
    )
    
    for dir in "${write_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
        fi
        
        if [ -w "$dir" ]; then
            success "Write permission OK for $dir"
        else
            error "No write permission for $dir"
            return 1
        fi
    done
    
    # Check execute permissions for scripts
    local script_files=(
        "scripts/start-development.sh"
        "scripts/start-production.sh"
        "scripts/start-patent-production.sh"
        "scripts/docker-healthcheck.sh"
    )
    
    for script in "${script_files[@]}"; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                success "Execute permission OK for $script"
            else
                warning "No execute permission for $script"
                chmod +x "$script" 2>/dev/null || true
            fi
        fi
    done
    
    return 0
}

# Main validation function
main() {
    log "🔍 Starting Patent MVP System Environment Validation..." "$GREEN"
    echo ""
    
    local validation_errors=0
    
    # Run all validations
    validate_uv || ((validation_errors++))
    echo ""
    
    validate_python || ((validation_errors++))
    echo ""
    
    validate_system_dependencies || ((validation_errors++))
    echo ""
    
    validate_docker || ((validation_errors++))
    echo ""
    
    validate_project_structure || ((validation_errors++))
    echo ""
    
    validate_dependencies || ((validation_errors++))
    echo ""
    
    validate_environment_files || ((validation_errors++))
    echo ""
    
    validate_ports || ((validation_errors++))
    echo ""
    
    validate_permissions || ((validation_errors++))
    echo ""
    
    # Summary
    if [ $validation_errors -eq 0 ]; then
        success "🎉 Environment validation completed successfully!"
        success "Your system is ready for Patent MVP System deployment."
        echo ""
        info "Next steps:"
        echo "  1. Run './scripts/start-development.sh' for development"
        echo "  2. Run './scripts/start-patent-production.sh' for production"
        echo "  3. Run './scripts/start-patent-production.sh --docker' for Docker deployment"
    else
        error "❌ Environment validation failed with $validation_errors error(s)"
        error "Please fix the issues above before deploying the Patent MVP System."
        return 1
    fi
}

# Run validation
main "$@"