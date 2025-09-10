@echo off
REM Patent MVP System Development Startup Script for Windows
REM This script starts the patent analysis system in development mode using uv

setlocal enabledelayedexpansion

echo 🛠️  Starting Patent MVP System in Development Mode...

REM Check if uv is installed
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: uv is not installed. Please install uv first.
    echo Visit: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

REM Set development environment
set APP_ENV=development
set PYTHONPATH=%cd%\src

REM Load development environment variables
if exist ".env.development" (
    echo 📋 Loading development environment variables...
    for /f "usebackq tokens=1,2 delims==" %%a in (".env.development") do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" (
            set "%%a=%%b"
        )
    )
) else (
    echo ⚠️  Warning: .env.development file not found. Creating default...
    if exist ".env.example" copy ".env.example" ".env.development" >nul
)

REM Install dependencies if needed
echo 📦 Checking dependencies...
if not exist ".venv" (
    echo 🔄 Installing dependencies with uv...
    uv sync --dev
) else (
    echo ✅ Dependencies already installed
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "reports\patent" mkdir reports\patent
if not exist "data\raw" mkdir data\raw
if not exist "tests\temp" mkdir tests\temp

REM Run quick health check tests
echo 🧪 Running quick health check tests...
uv run pytest tests/test_startup.py -v --tb=short >nul 2>nul
if %errorlevel% equ 0 (
    echo ✅ Health check tests passed
) else (
    echo ⚠️  Some health check tests failed, but continuing...
)

REM Validate configurations
echo 🤖 Validating development configurations...
uv run python -c "try: from src.multi_agent_service.core.config_manager import ConfigManager; config_manager = ConfigManager(); print('✅ Configuration manager initialized successfully'); except Exception as e: print(f'⚠️  Configuration warning: {e}')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Configuration validation had issues, but continuing...
)

REM Start the application with hot reload
echo 🎯 Starting Patent MVP System in Development Mode...
echo 📊 Application will be available at: http://localhost:8000
echo 📋 Health check endpoint: http://localhost:8000/health
echo 📚 API documentation: http://localhost:8000/docs
echo 🔄 Hot reload is enabled - changes will be automatically detected
echo.
echo 💡 Development Tips:
echo    - Use 'uv run pytest' to run tests
echo    - Use 'uv run black src/' to format code
echo    - Use 'uv run mypy src/' for type checking
echo    - Press Ctrl+C to stop the server
echo.

REM Use uv to run the application with development settings
uv run uvicorn src.multi_agent_service.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir src --reload-dir config --log-level debug --access-log

pause