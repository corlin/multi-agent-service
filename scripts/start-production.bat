@echo off
REM Patent MVP System Production Startup Script for Windows
REM This script starts the patent analysis system in production mode using uv

setlocal enabledelayedexpansion

echo 🚀 Starting Patent MVP System in Production Mode...

REM Check if uv is installed
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: uv is not installed. Please install uv first.
    echo Visit: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

REM Set production environment
set APP_ENV=production
set PYTHONPATH=%cd%\src

REM Load production environment variables
if exist ".env.production" (
    echo 📋 Loading production environment variables...
    for /f "usebackq tokens=1,2 delims==" %%a in (".env.production") do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" (
            set "%%a=%%b"
        )
    )
) else (
    echo ⚠️  Warning: .env.production file not found. Using default settings.
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "reports\patent" mkdir reports\patent
if not exist "data\raw" mkdir data\raw

REM Check database connectivity
echo 🔍 Checking database connectivity...
uv run python -c "import asyncio; import sys; from src.multi_agent_service.infrastructure.database import Database; async def check_db(): try: db = Database(); await db.connect(); await db.disconnect(); print('✅ Database connection successful'); return True; except Exception as e: print(f'❌ Database connection failed: {e}'); return False; result = asyncio.run(check_db()); sys.exit(0 if result else 1)"
if %errorlevel% neq 0 (
    echo ❌ Database connectivity check failed. Please check your database configuration.
    pause
    exit /b 1
)
echo ✅ Database connectivity verified

REM Check Redis connectivity
echo 🔍 Checking Redis connectivity...
uv run python -c "import redis; import sys; import os; r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0')); r.ping(); print('✅ Redis connection successful')"
if %errorlevel% neq 0 (
    echo ❌ Redis connectivity check failed. Please check your Redis configuration.
    pause
    exit /b 1
)
echo ✅ Redis connectivity verified

REM Validate agent configurations
echo 🤖 Validating agent configurations...
uv run python -c "import sys; from src.multi_agent_service.core.config_manager import ConfigManager; config_manager = ConfigManager(); agents = config_manager.load_agents_config(); workflows = config_manager.load_workflows_config(); print(f'✅ Loaded {len(agents)} agents and {len(workflows)} workflows')"
if %errorlevel% neq 0 (
    echo ❌ Agent configuration validation failed.
    pause
    exit /b 1
)
echo ✅ Agent configurations validated

REM Start the application
echo 🎯 Starting Patent MVP System...
echo 📊 Application will be available at: http://localhost:8000
echo 📋 Health check endpoint: http://localhost:8000/health
echo 📚 API documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Use uv to run the application with production settings
uv run uvicorn src.multi_agent_service.main:app --host 0.0.0.0 --port 8000 --workers 2 --access-log --log-level info

pause