@echo off
REM Patent MVP System Windows Setup Script
REM This script sets up the development environment on Windows 10

setlocal enabledelayedexpansion

echo 🪟 Setting up Patent MVP System on Windows 10...

REM Check if Python is installed
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: Python is not installed or not in PATH.
    echo Please install Python 3.12+ from https://python.org
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python version: %PYTHON_VERSION%

REM Check if uv is installed
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo 📦 Installing uv package manager...
    
    REM Try to install uv using pip
    python -m pip install uv
    if %errorlevel% neq 0 (
        echo ❌ Failed to install uv using pip.
        echo Please install uv manually from: https://docs.astral.sh/uv/getting-started/installation/
        pause
        exit /b 1
    )
    
    echo ✅ uv installed successfully
) else (
    echo ✅ uv is already installed
)

REM Create project directories
echo 📁 Creating project directories...
if not exist "logs" mkdir logs
if not exist "reports" mkdir reports
if not exist "reports\patent" mkdir reports\patent
if not exist "data" mkdir data
if not exist "data\raw" mkdir data\raw
if not exist "tests\temp" mkdir tests\temp
if not exist "config\backup" mkdir config\backup

REM Install project dependencies
echo 📦 Installing project dependencies...
uv sync --dev
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed successfully

REM Create environment files if they don't exist
if not exist ".env.development" (
    echo 📝 Creating development environment file...
    copy ".env.development" ".env.development.backup" >nul 2>nul
    echo # Development Environment Configuration > .env.development
    echo APP_ENV=development >> .env.development
    echo LOG_LEVEL=DEBUG >> .env.development
    echo DEBUG=true >> .env.development
    echo DATABASE_URL=sqlite:///./patent_dev.db >> .env.development
    echo REDIS_URL=redis://localhost:6379/0 >> .env.development
    echo ✅ Development environment file created
)

REM Check if Redis is available (optional for development)
echo 🔍 Checking Redis availability...
redis-cli ping >nul 2>nul
if %errorlevel% equ 0 (
    echo ✅ Redis is running
) else (
    echo ⚠️  Redis is not running. You can:
    echo    1. Install Redis for Windows from: https://github.com/microsoftarchive/redis/releases
    echo    2. Use Docker: docker run -d -p 6379:6379 redis:alpine
    echo    3. Continue without Redis (some features may be limited)
)

REM Run initial tests
echo 🧪 Running initial tests...
uv run pytest tests/ -x --tb=short >nul 2>nul
if %errorlevel% equ 0 (
    echo ✅ Initial tests passed
) else (
    echo ⚠️  Some tests failed, but setup can continue
)

REM Create desktop shortcuts (optional)
echo 🔗 Creating shortcuts...

REM Create start development shortcut
echo @echo off > start-dev.bat
echo cd /d "%cd%" >> start-dev.bat
echo call scripts\start-development.bat >> start-dev.bat

REM Create start production shortcut
echo @echo off > start-prod.bat
echo cd /d "%cd%" >> start-prod.bat
echo call scripts\start-production.bat >> start-prod.bat

REM Create run tests shortcut
echo @echo off > run-tests.bat
echo cd /d "%cd%" >> run-tests.bat
echo uv run pytest tests/ -v >> run-tests.bat
echo pause >> run-tests.bat

echo ✅ Shortcuts created: start-dev.bat, start-prod.bat, run-tests.bat

REM Display setup summary
echo.
echo 🎉 Setup completed successfully!
echo.
echo 📋 Next steps:
echo    1. Configure your environment variables in .env.development
echo    2. Start development server: start-dev.bat
echo    3. Open browser: http://localhost:8000
echo    4. View API docs: http://localhost:8000/docs
echo.
echo 🛠️  Development commands:
echo    - Start development: start-dev.bat
echo    - Start production: start-prod.bat
echo    - Run tests: run-tests.bat
echo    - Format code: uv run black src/
echo    - Type check: uv run mypy src/
echo.
echo 📚 Documentation:
echo    - Project README: README.md
echo    - API Documentation: http://localhost:8000/docs (after starting)
echo.

pause