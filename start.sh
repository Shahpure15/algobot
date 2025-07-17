#!/bin/bash

# Development startup script for the Trading Bot Dashboard

echo "🚀 Starting Algo Trading Bot Dashboard..."
echo "========================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your Delta Exchange credentials."
fi

# Stop any existing containers
echo "🧹 Stopping any existing containers..."
docker-compose down

# Build and start the application
echo "🔨 Building and starting the application..."
docker-compose up --build -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker-compose ps

# Test the API
echo "🧪 Testing API connectivity..."
sleep 5

# Check if backend is responding
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running at http://localhost:8000"
else
    echo "❌ Backend is not responding"
fi

# Check if frontend is responding
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running at http://localhost:3000"
else
    echo "❌ Frontend is not responding"
fi

echo ""
echo "🎉 Application started successfully!"
echo "========================================"
echo "📊 Dashboard: http://localhost:3000"
echo "🔧 API Documentation: http://localhost:8000/docs"
echo "💚 Health Check: http://localhost:8000/health"
echo ""
echo "📋 Useful commands:"
echo "  docker-compose logs -f        # View logs"
echo "  docker-compose down           # Stop services"
echo "  docker-compose restart        # Restart services"
echo "  python test_api.py            # Test API endpoints"
echo ""
echo "🔧 To configure Delta Exchange:"
echo "  1. Edit the .env file with your API credentials"
echo "  2. Restart the application: docker-compose restart"
echo "  3. Connect via the dashboard UI"
echo "========================================"
