#!/bin/bash
# One-command deployment script for AlgoBot

# Display banner
echo "====================================================="
echo "  AlgoBot One-Command Deployment"
echo "====================================================="
echo "This script will deploy the AlgoBot platform with a single command."
echo ""

# Check if docker and docker-compose are installed
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker and Docker Compose are required."
    echo "Please install Docker and Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit the .env file with your configuration."
    echo "Then run this script again."
    exit 0
fi

# Pull the latest code if this is a git repository
if [ -d .git ]; then
    echo "Pulling latest code..."
    git pull
fi

# Run tests
echo "Running tests..."
docker-compose -f docker-compose.yml run --rm backend pytest

# If tests failed, ask for confirmation to continue
if [ $? -ne 0 ]; then
    echo "Tests failed. Do you want to continue with deployment? (y/N)"
    read -r continue_deploy
    if [[ ! "$continue_deploy" =~ ^[Yy]$ ]]; then
        echo "Deployment aborted."
        exit 1
    fi
fi

# Build and start the application
echo "Building and starting the application..."
docker-compose -f docker-compose.yml up -d --build

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "Error: Some services failed to start."
    docker-compose logs
    exit 1
fi

# Display access information
echo ""
echo "====================================================="
echo "  AlgoBot successfully deployed!"
echo "====================================================="
echo "You can access AlgoBot at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Documentation: http://localhost:8000/docs"
echo ""
echo "To view logs, run: docker-compose logs -f"
echo "To stop the application, run: docker-compose down"

exit 0
