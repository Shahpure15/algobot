#!/bin/bash

# AlgoBot Linux Setup Script
# Run this script to set up the trading bot on Linux

set -e  # Exit on any error

echo "========================================"
echo "ALGOBOT SETUP FOR LINUX"
echo "========================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_warning "This script should not be run as root"
    echo "Please run as a regular user with sudo privileges"
    exit 1
fi

# 1. Check Python installation
echo "1. Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [[ $PYTHON_MAJOR -ge 3 && $PYTHON_MINOR -ge 8 ]]; then
        print_success "Python $PYTHON_VERSION found"
        PYTHON_CMD="python3"
    else
        print_error "Python 3.8+ required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python3 not found. Please install Python 3.8+"
    echo "Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "Arch Linux: sudo pacman -S python python-pip"
    exit 1
fi

# 2. Check pip installation
echo
echo "2. Checking pip installation..."
if command -v pip3 &> /dev/null; then
    print_success "pip3 found"
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    print_success "pip found"
    PIP_CMD="pip"
else
    print_error "pip not found. Installing pip..."
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install python3-pip -y
    elif command -v yum &> /dev/null; then
        sudo yum install python3-pip -y
    elif command -v pacman &> /dev/null; then
        sudo pacman -S python-pip
    else
        print_error "Could not install pip. Please install manually"
        exit 1
    fi
    PIP_CMD="pip3"
fi

# 3. Install system dependencies
echo
echo "3. Installing system dependencies..."
if command -v apt &> /dev/null; then
    print_info "Detected Ubuntu/Debian system"
    sudo apt update
    sudo apt install -y build-essential python3-dev python3-venv wget curl git
    
    # Install TA-Lib dependencies
    print_info "Installing TA-Lib dependencies..."
    sudo apt install -y libta-dev || {
        print_warning "TA-Lib not available in repositories, will compile from source"
        # Install TA-Lib from source
        cd /tmp
        wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
        tar -xzf ta-lib-0.4.0-src.tar.gz
        cd ta-lib/
        ./configure --prefix=/usr
        make
        sudo make install
        cd - > /dev/null
        rm -rf /tmp/ta-lib*
    }
    
elif command -v yum &> /dev/null; then
    print_info "Detected CentOS/RHEL system"
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y python3-devel wget curl git
    
    # Install TA-Lib from source
    print_info "Installing TA-Lib from source..."
    cd /tmp
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    ./configure --prefix=/usr
    make
    sudo make install
    cd - > /dev/null
    rm -rf /tmp/ta-lib*
    
elif command -v pacman &> /dev/null; then
    print_info "Detected Arch Linux system"
    sudo pacman -S --needed base-devel python wget curl git
    
    # Install TA-Lib from AUR or source
    if command -v yay &> /dev/null; then
        yay -S ta-lib
    else
        print_info "Installing TA-Lib from source..."
        cd /tmp
        wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
        tar -xzf ta-lib-0.4.0-src.tar.gz
        cd ta-lib/
        ./configure --prefix=/usr
        make
        sudo make install
        cd - > /dev/null
        rm -rf /tmp/ta-lib*
    fi
else
    print_warning "Unknown Linux distribution. You may need to install dependencies manually"
    print_info "Required: build-essential, python3-dev, wget, curl, git, ta-lib"
fi

# 4. Create virtual environment
echo
echo "4. Creating Python virtual environment..."
if [[ ! -d "venv" ]]; then
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# 5. Activate virtual environment
echo
echo "5. Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# 6. Upgrade pip in virtual environment
echo
echo "6. Upgrading pip..."
pip install --upgrade pip
print_success "pip upgraded"

# 7. Install Python dependencies
echo
echo "7. Installing Python dependencies..."
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# 8. Run setup script
echo
echo "8. Running setup script..."
if [[ -f "scripts/setup.py" ]]; then
    python scripts/setup.py
    if [[ $? -eq 0 ]]; then
        print_success "Setup script completed"
    else
        print_error "Setup script failed"
        exit 1
    fi
else
    print_error "Setup script not found"
    exit 1
fi

# 9. Create necessary directories
echo
echo "9. Creating directories..."
mkdir -p data/{logs,models,historical}
mkdir -p logs
print_success "Directories created"

# 10. Set permissions
echo
echo "10. Setting permissions..."
chmod +x scripts/*.py
chmod +x run.py
chmod +x validate_setup.py
print_success "Permissions set"

# 11. Validate setup
echo
echo "11. Validating setup..."
if python validate_setup.py; then
    print_success "Setup validation passed"
else
    print_warning "Setup validation failed, but continuing..."
fi

# 12. Check if Docker is available
echo
echo "12. Checking Docker availability..."
if command -v docker &> /dev/null; then
    print_success "Docker found"
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose found"
    else
        print_warning "Docker Compose not found. Install with: sudo apt install docker-compose"
    fi
else
    print_warning "Docker not found. Install with: curl -fsSL https://get.docker.com | sh"
fi

echo
echo "========================================"
echo "SETUP COMPLETE!"
echo "========================================"
echo
echo "Next steps:"
echo "1. Edit .env file with your Delta Exchange API credentials:"
echo "   nano .env"
echo
echo "2. Test connection:"
echo "   source venv/bin/activate"
echo "   python scripts/test_connection.py"
echo
echo "3. Start the bot:"
echo "   source venv/bin/activate"
echo "   python src/main.py"
echo
echo "4. Or use Docker:"
echo "   docker-compose up -d"
echo
echo "5. Monitor logs:"
echo "   tail -f data/logs/bot.log"
echo
echo "Configuration file: .env"
echo "Documentation: README.md"
echo
print_success "AlgoBot setup completed successfully!"
echo
