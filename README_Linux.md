# AlgoBot Linux Setup and Commands

Complete guide for running AlgoBot on Linux systems.

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone <your-repo-url> AlgoBot
cd AlgoBot

# 2. Run setup script
bash setup_linux.sh

# 3. Configure API keys
nano .env

# 4. Test connection
source venv/bin/activate
python scripts/test_connection.py

# 5. Start bot
bash run_linux.sh
```

## 📋 System Requirements

- **OS**: Ubuntu 18.04+, CentOS 7+, Debian 10+, or similar
- **Python**: 3.8+
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 10GB minimum
- **Network**: Stable internet connection

## 🛠 Installation Methods

### Method 1: Automated Setup (Recommended)

```bash
# Download and run setup script
bash setup_linux.sh
```

### Method 2: Manual Setup

#### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y build-essential python3-dev python3-pip python3-venv wget curl git

# Install TA-Lib
sudo apt install -y libta-dev || {
    # Install from source if not available
    cd /tmp
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    ./configure --prefix=/usr
    make
    sudo make install
    cd -
}
```

**CentOS/RHEL:**
```bash
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python3-devel python3-pip wget curl git

# Install TA-Lib from source
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd -
```

**Arch Linux:**
```bash
sudo pacman -S --needed base-devel python python-pip wget curl git

# Install TA-Lib
yay -S ta-lib  # or install from source
```

#### Step 2: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit with your credentials
nano .env
```

### Method 3: Docker Deployment

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Logout and login again

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Deploy with Docker
bash deploy_docker_linux.sh
```

## ⚙️ Configuration

### Edit Configuration File

```bash
nano .env
```

**Required Settings:**
```bash
# Delta Exchange API
DELTA_API_KEY=your_actual_api_key
DELTA_API_SECRET=your_actual_api_secret
DELTA_TESTNET=true  # Start with testnet

# Trading Settings
TRADING_SYMBOL=BTCUSDT_PERP
POSITION_SIZE=0.01
RISK_PER_TRADE=0.02
```

### Test Configuration

```bash
# Validate setup
python validate_setup.py

# Test connection
source venv/bin/activate
python scripts/test_connection.py
```

## 🚀 Running the Bot

### Option 1: Direct Execution

```bash
# Activate virtual environment
source venv/bin/activate

# Run bot
python src/main.py
```

### Option 2: Using Run Script

```bash
# Make executable
chmod +x run_linux.sh

# Run
bash run_linux.sh
```

### Option 3: Background Execution

```bash
# Using nohup
nohup bash run_linux.sh > bot.log 2>&1 &

# Check process
ps aux | grep python
```

### Option 4: Screen/Tmux (Recommended)

```bash
# Install screen
sudo apt install screen  # Ubuntu/Debian
sudo yum install screen  # CentOS/RHEL

# Start screen session
screen -S algobot

# Run bot
source venv/bin/activate
python src/main.py

# Detach: Ctrl+A, then D
# Reattach: screen -r algobot
```

### Option 5: Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f algobot

# Stop
docker-compose down
```

## 📊 Monitoring

### View Logs

```bash
# Real-time logs
tail -f data/logs/bot.log

# Docker logs
docker-compose logs -f algobot

# Last 100 lines
tail -100 data/logs/bot.log
```

### Health Checks

```bash
# Check bot health
curl http://localhost:8000/health

# Check bot status
curl http://localhost:8000/status

# Check system resources
htop
df -h
free -h
```

### Web Interfaces

- **Bot API**: http://localhost:8000
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090

## 🔧 Maintenance

### Update Bot

```bash
# Pull latest code
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart bot
pkill -f 'python src/main.py'
bash run_linux.sh
```

### Clean Logs

```bash
# Remove old logs
find data/logs -name "*.log.*" -mtime +7 -delete

# Compress current logs
gzip data/logs/bot.log
```

### Backup Data

```bash
# Create backup
tar -czf backup-$(date +%Y%m%d).tar.gz .env data/models/ data/logs/

# Automated backup script
echo "0 2 * * * cd /path/to/AlgoBot && tar -czf backup-\$(date +\%Y\%m\%d).tar.gz .env data/" | crontab -
```

## 🔒 Security

### Firewall Setup

```bash
# Enable UFW
sudo ufw enable

# Allow necessary ports
sudo ufw allow 22      # SSH
sudo ufw allow 8000    # Bot API
sudo ufw allow 3000    # Grafana (if needed)

# Check status
sudo ufw status
```

### Secure API Keys

```bash
# Set proper permissions
chmod 600 .env

# Never commit .env to git
echo ".env" >> .gitignore
```

### System Updates

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install security updates
sudo apt install unattended-upgrades
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Check virtual environment
   which python
   source venv/bin/activate
   
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

2. **Permission Denied**
   ```bash
   # Fix permissions
   chmod +x *.sh
   chmod +x scripts/*.py
   ```

3. **Port Already in Use**
   ```bash
   # Find process using port
   sudo netstat -tlnp | grep :8000
   
   # Kill process
   sudo kill -9 <PID>
   ```

4. **TA-Lib Installation Issues**
   ```bash
   # Install from source
   cd /tmp
   wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
   tar -xzf ta-lib-0.4.0-src.tar.gz
   cd ta-lib/
   ./configure --prefix=/usr
   make
   sudo make install
   ```

### Debug Commands

```bash
# Check running processes
ps aux | grep python

# Check system resources
htop
df -h
free -h

# Check network
ping api.delta.exchange
curl -I https://api.delta.exchange

# Check logs
tail -f data/logs/bot.log
journalctl -u algobot -f  # If using systemd
```

## 🏭 Production Setup

### Systemd Service

```bash
# Create service file
sudo tee /etc/systemd/system/algobot.service > /dev/null <<EOF
[Unit]
Description=AlgoBot Trading Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/AlgoBot
ExecStart=/home/$USER/AlgoBot/venv/bin/python /home/$USER/AlgoBot/src/main.py
Restart=always
RestartSec=10
Environment=PATH=/home/$USER/AlgoBot/venv/bin

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable algobot
sudo systemctl start algobot

# Check status
sudo systemctl status algobot
```

### Process Management

```bash
# Start service
sudo systemctl start algobot

# Stop service
sudo systemctl stop algobot

# Restart service
sudo systemctl restart algobot

# View logs
journalctl -u algobot -f
```

### Monitoring Setup

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Setup log rotation
sudo tee /etc/logrotate.d/algobot > /dev/null <<EOF
/home/$USER/AlgoBot/data/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    sharedscripts
}
EOF
```

## 📚 Advanced Usage

### Custom Scripts

```bash
# Create custom start script
cat > start_bot.sh << 'EOF'
#!/bin/bash
cd /path/to/AlgoBot
source venv/bin/activate
python src/main.py
EOF

chmod +x start_bot.sh
```

### Environment Variables

```bash
# Set environment variables
export DELTA_API_KEY="your_key"
export DELTA_API_SECRET="your_secret"

# Or create a script
cat > set_env.sh << 'EOF'
#!/bin/bash
export DELTA_API_KEY="your_key"
export DELTA_API_SECRET="your_secret"
export TRADING_SYMBOL="BTCUSDT_PERP"
EOF

source set_env.sh
```

### Multiple Instances

```bash
# Run multiple bots with different configs
cp .env .env.btc
cp .env .env.eth

# Edit each config
nano .env.btc  # Set TRADING_SYMBOL=BTCUSDT_PERP
nano .env.eth  # Set TRADING_SYMBOL=ETHUSDT_PERP

# Run with different configs
ENV_FILE=.env.btc python src/main.py &
ENV_FILE=.env.eth python src/main.py &
```

## 🆘 Emergency Procedures

### Emergency Stop

```bash
# Stop all bot processes
pkill -f 'python src/main.py'

# Stop Docker containers
docker-compose down

# Stop systemd service
sudo systemctl stop algobot
```

### Emergency Position Closure

```bash
# Run emergency closure script
python scripts/emergency_close.py
```

### Recovery

```bash
# Check last known state
tail -100 data/logs/bot.log

# Restore from backup
tar -xzf backup-YYYYMMDD.tar.gz

# Restart bot
bash run_linux.sh
```

---

## 📞 Support

For issues and questions:
1. Check the logs: `tail -f data/logs/bot.log`
2. Run connection test: `python scripts/test_connection.py`
3. Validate setup: `python validate_setup.py`
4. Check system resources: `htop`

**Remember**: Always start with testnet and small position sizes!
