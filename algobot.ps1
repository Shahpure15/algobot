# AlgoBot Development Script for Windows
# This script provides commands for local development and deployment

# Define colors for console output
$GREEN = [System.ConsoleColor]::Green
$YELLOW = [System.ConsoleColor]::Yellow
$RED = [System.ConsoleColor]::Red
$BLUE = [System.ConsoleColor]::Cyan

# Display header
Write-Host "===================================" -ForegroundColor $BLUE
Write-Host "    AlgoBot Development Script     " -ForegroundColor $BLUE
Write-Host "===================================" -ForegroundColor $BLUE

# Function to display help menu
function Show-Help {
    Write-Host "Available commands:" -ForegroundColor $BLUE
    Write-Host "  start       - Start all services in development mode" -ForegroundColor $GREEN
    Write-Host "  build       - Build Docker images" -ForegroundColor $GREEN
    Write-Host "  deploy      - Deploy to production" -ForegroundColor $GREEN
    Write-Host "  test        - Run all tests" -ForegroundColor $GREEN
    Write-Host "  test:backend - Run backend tests" -ForegroundColor $GREEN
    Write-Host "  test:frontend - Run frontend tests" -ForegroundColor $GREEN
    Write-Host "  clean       - Remove all containers and volumes" -ForegroundColor $GREEN
    Write-Host "  logs        - Follow container logs" -ForegroundColor $GREEN
    Write-Host "  help        - Show this help message" -ForegroundColor $GREEN
}

# Function to start development environment
function Start-Dev {
    Write-Host "Starting all services in development mode..." -ForegroundColor $YELLOW
    docker-compose up -d
    Write-Host "Services started! Access:" -ForegroundColor $GREEN
    Write-Host "  Frontend: http://localhost:3000" -ForegroundColor $BLUE
    Write-Host "  Backend API: http://localhost:8000" -ForegroundColor $BLUE
    Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor $BLUE
}

# Function to build Docker images
function Build-Images {
    Write-Host "Building Docker images..." -ForegroundColor $YELLOW
    docker-compose build
    Write-Host "Docker images built successfully!" -ForegroundColor $GREEN
}

# Function to deploy to production
function Deploy-Prod {
    Write-Host "Deploying to production..." -ForegroundColor $YELLOW
    
    # Check if .env.prod exists
    if (-not (Test-Path .env.prod)) {
        Write-Host "Error: .env.prod file not found!" -ForegroundColor $RED
        Write-Host "Please create a .env.prod file with your production environment variables."
        return
    }
    
    # Run tests before deploying
    Write-Host "Running tests before deployment..." -ForegroundColor $BLUE
    Run-Tests
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Tests failed! Deployment aborted." -ForegroundColor $RED
        return
    }
    
    Write-Host "Tests passed! Continuing with deployment..." -ForegroundColor $BLUE
    docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
    
    Write-Host "Deployment completed successfully!" -ForegroundColor $GREEN
}

# Function to run all tests
function Run-Tests {
    Write-Host "Running all tests..." -ForegroundColor $YELLOW
    Run-BackendTests
    Run-FrontendTests
}

# Function to run backend tests
function Run-BackendTests {
    Write-Host "Running backend tests..." -ForegroundColor $YELLOW
    docker-compose run --rm backend pytest
}

# Function to run frontend tests
function Run-FrontendTests {
    Write-Host "Running frontend tests..." -ForegroundColor $YELLOW
    docker-compose run --rm frontend npm test
}

# Function to clean up all containers and volumes
function Clean-Env {
    Write-Host "Cleaning up Docker resources..." -ForegroundColor $YELLOW
    docker-compose down -v
    Write-Host "Cleanup completed!" -ForegroundColor $GREEN
}

# Function to follow container logs
function Follow-Logs {
    Write-Host "Following container logs... (Ctrl+C to exit)" -ForegroundColor $YELLOW
    docker-compose logs -f
}

# Parse command line arguments
$command = $args[0]

switch ($command) {
    "start" { Start-Dev }
    "build" { Build-Images }
    "deploy" { Deploy-Prod }
    "test" { Run-Tests }
    "test:backend" { Run-BackendTests }
    "test:frontend" { Run-FrontendTests }
    "clean" { Clean-Env }
    "logs" { Follow-Logs }
    default { Show-Help }
}
