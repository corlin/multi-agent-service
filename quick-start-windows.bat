@echo off
REM Quick Start Script for Patent MVP System on Windows 10
REM This script provides a menu-driven interface for common operations

setlocal enabledelayedexpansion

:MENU
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                Patent MVP System - Windows 10                ║
echo ║                     Quick Start Menu                         ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🚀 Choose an option:
echo.
echo [1] 🛠️  Setup Development Environment
echo [2] 🏃 Start Development Server
echo [3] 🎯 Start Production Server  
echo [4] 🧪 Run Tests
echo [5] 🐳 Start with Docker
echo [6] 📦 Install/Update Dependencies
echo [7] 🔧 Format Code
echo [8] 📊 View System Status
echo [9] 📚 Open Documentation
echo [0] ❌ Exit
echo.
set /p choice="Enter your choice (0-9): "

if "%choice%"=="1" goto SETUP
if "%choice%"=="2" goto DEV_START
if "%choice%"=="3" goto PROD_START
if "%choice%"=="4" goto RUN_TESTS
if "%choice%"=="5" goto DOCKER_START
if "%choice%"=="6" goto INSTALL_DEPS
if "%choice%"=="7" goto FORMAT_CODE
if "%choice%"=="8" goto SYSTEM_STATUS
if "%choice%"=="9" goto OPEN_DOCS
if "%choice%"=="0" goto EXIT

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:SETUP
echo.
echo 🛠️  Setting up development environment...
call scripts\setup-windows.bat
pause
goto MENU

:DEV_START
echo.
echo 🏃 Starting development server...
call scripts\start-development.bat
pause
goto MENU

:PROD_START
echo.
echo 🎯 Starting production server...
call scripts\start-production.bat
pause
goto MENU

:RUN_TESTS
echo.
echo 🧪 Running tests...
echo.
echo Choose test type:
echo [1] All tests
echo [2] Unit tests only
echo [3] Integration tests only
echo [4] Performance tests
echo [5] Patent-specific tests
echo.
set /p test_choice="Enter choice (1-5): "

if "%test_choice%"=="1" (
    uv run pytest tests/ -v
) else if "%test_choice%"=="2" (
    uv run pytest tests/test_*.py -v -k "not integration"
) else if "%test_choice%"=="3" (
    uv run pytest tests/ -v -k "integration"
) else if "%test_choice%"=="4" (
    uv run pytest tests/performance/ -v
) else if "%test_choice%"=="5" (
    uv run pytest tests/ -v -k "patent"
) else (
    echo Invalid choice
)
pause
goto MENU

:DOCKER_START
echo.
echo 🐳 Starting with Docker...
echo.
echo Choose Docker mode:
echo [1] Development mode
echo [2] Production mode
echo [3] With Jupyter notebook
echo.
set /p docker_choice="Enter choice (1-3): "

if "%docker_choice%"=="1" (
    docker-compose -f docker-compose.windows.yml up -d
    echo ✅ Development environment started
    echo 📊 Application: http://localhost:8000
    echo 📋 Health check: http://localhost:8000/health
) else if "%docker_choice%"=="2" (
    docker-compose -f docker-compose.yml up -d
    echo ✅ Production environment started
) else if "%docker_choice%"=="3" (
    docker-compose -f docker-compose.windows.yml --profile jupyter up -d
    echo ✅ Development environment with Jupyter started
    echo 📊 Application: http://localhost:8000
    echo 📓 Jupyter: http://localhost:8888
) else (
    echo Invalid choice
)
pause
goto MENU

:INSTALL_DEPS
echo.
echo 📦 Installing/updating dependencies...
uv sync --dev
if %errorlevel% equ 0 (
    echo ✅ Dependencies updated successfully
) else (
    echo ❌ Failed to update dependencies
)
pause
goto MENU

:FORMAT_CODE
echo.
echo 🔧 Formatting code...
echo.
echo Running black formatter...
uv run black src/
echo.
echo Running isort import sorter...
uv run isort src/
echo.
echo Running mypy type checker...
uv run mypy src/
echo.
echo ✅ Code formatting completed
pause
goto MENU

:SYSTEM_STATUS
echo.
echo 📊 System Status Check...
echo.

REM Check Python
python --version >nul 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo ✅ Python: %%i
) else (
    echo ❌ Python: Not installed
)

REM Check uv
uv --version >nul 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('uv --version 2^>^&1') do echo ✅ uv: %%i
) else (
    echo ❌ uv: Not installed
)

REM Check Docker
docker --version >nul 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=3" %%i in ('docker --version 2^>^&1') do echo ✅ Docker: %%i
) else (
    echo ⚠️  Docker: Not available
)

REM Check Redis
redis-cli ping >nul 2>nul
if %errorlevel% equ 0 (
    echo ✅ Redis: Running
) else (
    echo ⚠️  Redis: Not running
)

REM Check project structure
if exist "src\" (
    echo ✅ Source code: Present
) else (
    echo ❌ Source code: Missing
)

if exist "uv.lock" (
    echo ✅ Dependencies: Locked
) else (
    echo ⚠️  Dependencies: Not locked
)

echo.
pause
goto MENU

:OPEN_DOCS
echo.
echo 📚 Opening documentation...
echo.
echo Choose documentation:
echo [1] Local API docs (requires running server)
echo [2] Project README
echo [3] Requirements document
echo [4] Design document
echo [5] Tasks document
echo.
set /p doc_choice="Enter choice (1-5): "

if "%doc_choice%"=="1" (
    start http://localhost:8000/docs
) else if "%doc_choice%"=="2" (
    start README.md
) else if "%doc_choice%"=="3" (
    start .kiro\specs\patent-mvp-system\requirements.md
) else if "%doc_choice%"=="4" (
    start .kiro\specs\patent-mvp-system\design.md
) else if "%doc_choice%"=="5" (
    start .kiro\specs\patent-mvp-system\tasks.md
) else (
    echo Invalid choice
)
pause
goto MENU

:EXIT
echo.
echo 👋 Thank you for using Patent MVP System!
echo.
exit /b 0