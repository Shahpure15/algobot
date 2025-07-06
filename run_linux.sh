#!/bin/bash

# AlgoBot Runner Script for Linux
# This script handles virtual environment activation and runs the bot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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
    echo -e "${YELLOW}ℹ️ $1${NC}"
}

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    print_error "Virtual environment not found. Run setup first:"
    echo "bash setup_linux.sh"
    exit 1
fi

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    print_error ".env file not found!"
    echo "Please create .env file with your Delta Exchange credentials"
    exit 1
fi

# Check if API keys are configured
if grep -q "your_api_key_here" .env; then
    print_warning "API keys not configured in .env file"
    echo "Please edit .env file with your actual Delta Exchange credentials"
    echo "nano .env"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import requests, pandas, numpy" 2>/dev/null; then
    print_error "Dependencies not installed. Installing now..."
    pip install -r requirements.txt
fi

# Run the bot
print_info "Starting AlgoBot..."
python src/main.py
