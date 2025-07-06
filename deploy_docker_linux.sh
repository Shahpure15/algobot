#!/bin/bash

# Docker deployment script for Linux
# This script sets up AlgoBot with Docker on Linux

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

echo "========================================"
echo "ALGOBOT DOCKER DEPLOYMENT FOR LINUX"
echo "========================================"

# 1. Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_warning "Docker not found. Installing Docker..."
    
    # Install Docker
    curl -fsSL https://get.docker.com | sh
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    print_success "Docker installed"
    print_warning "Please logout and login again to apply Docker group permissions"
    print_info "Then run this script again"
    exit 0
fi

# 2. Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose not found. Installing..."
    
    # Install Docker Compose
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    sudo curl -L "https://github.com/docker/compose/releases/download/$DOCKER_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    print_success "Docker Compose installed"
fi

# 3. Check Docker daemon
if ! docker info &> /dev/null; then
    print_error "Docker daemon not running. Starting Docker..."
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# 4. Check .env file
if [[ ! -f ".env" ]]; then
    print_error ".env file not found!"
    print_info "Creating .env file template..."
    
    cat > .env << EOF
# Delta Exchange API Configuration
DELTA_API_KEY=your_api_key_here
DELTA_API_SECRET=your_api_secret_here
DELTA_TESTNET=true

# Trading Configuration
TRADING_SYMBOL=BTCUSDT_PERP
TRADING_TIMEFRAME=5m
POSITION_SIZE=0.01
MAX_POSITION_SIZE=0.1
RISK_PER_TRADE=0.02
MAX_DAILY_LOSS=0.05
STOP_LOSS_PCT=0.02
TAKE_PROFIT_PCT=0.04
MAX_OPEN_POSITIONS=3

# Machine Learning Configuration
MODEL_PATH=data/models/
RETRAIN_INTERVAL=24
MIN_CONFIDENCE=0.65
LOOKBACK_PERIOD=200

# Database Configuration
DATABASE_URL=sqlite:///data/trading_bot.db
DB_ECHO=false
POSTGRES_USER=algobot
POSTGRES_PASSWORD=algobot123
POSTGRES_DB=algobot

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=data/logs/bot.log

# Environment
ENVIRONMENT=development
DEBUG=false

# Optional: Grafana Configuration
GRAFANA_PASSWORD=admin123
EOF

    print_warning "Please edit .env file with your Delta Exchange API credentials"
    print_info "nano .env"
    exit 0
fi

# 5. Check if API keys are configured
if grep -q "your_api_key_here" .env; then
    print_warning "API keys not configured in .env file"
    print_info "Please edit .env file with your actual Delta Exchange credentials"
    print_info "nano .env"
    exit 0
fi

# 6. Create necessary directories
print_info "Creating directories..."
mkdir -p data/{logs,models,historical}
mkdir -p logs
print_success "Directories created"

# 7. Build and start containers
print_info "Building and starting containers..."
docker-compose up -d

# 8. Wait for containers to be ready
print_info "Waiting for containers to be ready..."
sleep 30

# 9. Check container status
print_info "Checking container status..."
docker-compose ps

# 10. Test bot health
print_info "Testing bot health..."
if curl -s http://localhost:8000/health > /dev/null; then
    print_success "Bot is healthy"
else
    print_warning "Bot health check failed, checking logs..."
    docker-compose logs --tail=20 algobot
fi

echo
echo "========================================"
echo "DOCKER DEPLOYMENT COMPLETE!"
echo "========================================"
echo
echo "Services:"
echo "- AlgoBot: http://localhost:8000"
echo "- Grafana: http://localhost:3000 (admin/admin123)"
echo "- Prometheus: http://localhost:9090"
echo "- PostgreSQL: localhost:5432"
echo "- Redis: localhost:6379"
echo
echo "Useful commands:"
echo "- View logs: docker-compose logs -f algobot"
echo "- Stop: docker-compose down"
echo "- Restart: docker-compose restart algobot"
echo "- Update: docker-compose pull && docker-compose up -d"
echo
print_success "AlgoBot Docker deployment completed!"
