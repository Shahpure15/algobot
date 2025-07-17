@echo off
rem Development startup script for the Trading Bot Dashboard (Windows)

echo 🚀 Starting Algo Trading Bot Dashboard...
echo ========================================

rem Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker first.
    exit /b 1
)

rem Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose.
    exit /b 1
)

rem Create .env file from example if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from .env.example...
    copy .env.example .env
    echo ✅ .env file created. Please edit it with your Delta Exchange credentials.
)

rem Stop any existing containers
echo 🧹 Stopping any existing containers...
docker-compose down

rem Build and start the application
echo 🔨 Building and starting the application...
docker-compose up --build -d

rem Wait for services to start
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul

rem Check service status
echo 🔍 Checking service status...
docker-compose ps

rem Test the API
echo 🧪 Testing API connectivity...
timeout /t 5 /nobreak >nul

rem Check if backend is responding
curl -s http://localhost:8000/health >nul
if %errorlevel% equ 0 (
    echo ✅ Backend is running at http://localhost:8000
) else (
    echo ❌ Backend is not responding
)

rem Check if frontend is responding
curl -s http://localhost:3000 >nul
if %errorlevel% equ 0 (
    echo ✅ Frontend is running at http://localhost:3000
) else (
    echo ❌ Frontend is not responding
)

echo.
echo 🎉 Application started successfully!
echo ========================================
echo 📊 Dashboard: http://localhost:3000
echo 🔧 API Documentation: http://localhost:8000/docs
echo 💚 Health Check: http://localhost:8000/health
echo.
echo 📋 Useful commands:
echo   docker-compose logs -f        # View logs
echo   docker-compose down           # Stop services
echo   docker-compose restart        # Restart services
echo   python test_api.py            # Test API endpoints
echo.
echo 🔧 To configure Delta Exchange:
echo   1. Edit the .env file with your API credentials
echo   2. Restart the application: docker-compose restart
echo   3. Connect via the dashboard UI
echo ========================================

pause
