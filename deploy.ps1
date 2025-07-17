# One-command deployment script for AlgoBot (Windows PowerShell)

# Display banner
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  AlgoBot One-Command Deployment" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "This script will deploy the AlgoBot platform with a single command."
Write-Host ""

# Check if docker and docker-compose are installed
$dockerInstalled = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)
if (-not $dockerInstalled) {
    Write-Host "Error: Docker is required." -ForegroundColor Red
    Write-Host "Please install Docker Desktop first."
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "Please edit the .env file with your configuration."
    Write-Host "Then run this script again."
    exit 0
}

# Pull the latest code if this is a git repository
if (Test-Path .git) {
    Write-Host "Pulling latest code..." -ForegroundColor Yellow
    git pull
}

# Run tests
Write-Host "Running tests..." -ForegroundColor Yellow
docker-compose -f docker-compose.yml run --rm backend pytest

# If tests failed, ask for confirmation to continue
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed. Do you want to continue with deployment? (y/N)" -ForegroundColor Red
    $continueDeployment = Read-Host
    if ($continueDeployment -ne "y" -and $continueDeployment -ne "Y") {
        Write-Host "Deployment aborted."
        exit 1
    }
}

# Build and start the application
Write-Host "Building and starting the application..." -ForegroundColor Yellow
docker-compose -f docker-compose.yml up -d --build

# Wait for services to be ready
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if services are running
$servicesUp = docker-compose ps | Select-String -Pattern "Up" -Quiet
if (-not $servicesUp) {
    Write-Host "Error: Some services failed to start." -ForegroundColor Red
    docker-compose logs
    exit 1
}

# Display access information
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Green
Write-Host "  AlgoBot successfully deployed!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host "You can access AlgoBot at:"
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view logs, run: docker-compose logs -f"
Write-Host "To stop the application, run: docker-compose down"

exit 0
