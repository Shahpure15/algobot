#!/bin/bash

# Quick Linux Commands for AlgoBot
# This file contains all the essential commands for running AlgoBot on Linux

echo "=========================================="
echo "ALGOBOT LINUX COMMANDS REFERENCE"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_section() {
    echo -e "\n${BLUE}$1${NC}"
    echo "----------------------------------------"
}

print_command() {
    echo -e "${GREEN}$1${NC}"
    echo "$2"
    echo
}

print_section "1. INITIAL SETUP"
print_command "# Download and setup AlgoBot" "
git clone <your-repo-url> AlgoBot
cd AlgoBot
bash setup_linux.sh"

print_section "2. MANUAL SETUP COMMANDS"
print_command "# Install system dependencies (Ubuntu/Debian)" "
sudo apt update
sudo apt install -y build-essential python3-dev python3-pip python3-venv wget curl git
sudo apt install -y libta-dev || {
    # Install TA-Lib from source if not available
    cd /tmp
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    ./configure --prefix=/usr
    make
    sudo make install
    cd -
}"

print_command "# Install system dependencies (CentOS/RHEL)" "
sudo yum groupinstall -y 'Development Tools'
sudo yum install -y python3-devel python3-pip wget curl git
# Install TA-Lib from source
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd -"

print_command "# Create virtual environment" "
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip"

print_command "# Install Python dependencies" "
pip install -r requirements.txt"

print_section "3. CONFIGURATION"
print_command "# Edit configuration file" "
nano .env
# Add your Delta Exchange API credentials:
# DELTA_API_KEY=your_actual_api_key
# DELTA_API_SECRET=your_actual_api_secret"

print_command "# Test connection" "
source venv/bin/activate
python scripts/test_connection.py"

print_command "# Validate setup" "
python validate_setup.py"

print_section "4. RUNNING THE BOT"
print_command "# Run directly" "
source venv/bin/activate
python src/main.py"

print_command "# Run with script" "
bash run_linux.sh"

print_command "# Run in background" "
nohup bash run_linux.sh > bot.log 2>&1 &"

print_command "# Run with screen (recommended)" "
screen -S algobot
source venv/bin/activate
python src/main.py
# Press Ctrl+A, then D to detach
# screen -r algobot to reattach"

print_section "5. DOCKER DEPLOYMENT"
print_command "# Install Docker" "
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker \$USER
# Logout and login again"

print_command "# Install Docker Compose" "
sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose"

print_command "# Deploy with Docker" "
docker-compose up -d"

print_command "# View Docker logs" "
docker-compose logs -f algobot"

print_section "6. MONITORING"
print_command "# View real-time logs" "
tail -f data/logs/bot.log"

print_command "# Check bot status" "
curl http://localhost:8000/health"

print_command "# Monitor system resources" "
htop
df -h
free -h"

print_section "7. MAINTENANCE"
print_command "# Update bot" "
git pull origin main
source venv/bin/activate
pip install -r requirements.txt"

print_command "# Restart bot" "
pkill -f 'python src/main.py'
bash run_linux.sh"

print_command "# Clean logs" "
find data/logs -name '*.log.*' -mtime +7 -delete"

print_section "8. TROUBLESHOOTING"
print_command "# Check running processes" "
ps aux | grep python"

print_command "# Kill bot process" "
pkill -f 'python src/main.py'"

print_command "# Check network connectivity" "
ping api.delta.exchange
curl -I https://api.delta.exchange"

print_command "# Check disk space" "
df -h
du -sh data/"

print_command "# Check memory usage" "
free -h
cat /proc/meminfo"

print_section "9. SYSTEMD SERVICE (OPTIONAL)"
print_command "# Create systemd service file" "
sudo tee /etc/systemd/system/algobot.service > /dev/null <<EOF
[Unit]
Description=AlgoBot Trading Bot
After=network.target

[Service]
Type=simple
User=\$USER
WorkingDirectory=/home/\$USER/AlgoBot
ExecStart=/home/\$USER/AlgoBot/venv/bin/python /home/\$USER/AlgoBot/src/main.py
Restart=always
RestartSec=10
Environment=PATH=/home/\$USER/AlgoBot/venv/bin

[Install]
WantedBy=multi-user.target
EOF"

print_command "# Enable and start service" "
sudo systemctl daemon-reload
sudo systemctl enable algobot
sudo systemctl start algobot
sudo systemctl status algobot"

print_section "10. SECURITY"
print_command "# Setup firewall" "
sudo ufw enable
sudo ufw allow 22      # SSH
sudo ufw allow 8000    # Bot API
sudo ufw allow 3000    # Grafana"

print_command "# Secure API keys" "
chmod 600 .env
# Never commit .env to git"

print_command "# Regular backups" "
tar -czf backup-\$(date +%Y%m%d).tar.gz .env data/models/ data/logs/"

echo
echo "=========================================="
echo "QUICK START SUMMARY"
echo "=========================================="
echo
echo "1. bash setup_linux.sh"
echo "2. nano .env  # Add your API keys"
echo "3. python scripts/test_connection.py"
echo "4. bash run_linux.sh"
echo
echo "For production: use Docker or systemd service"
echo "For development: use screen or tmux"
echo
