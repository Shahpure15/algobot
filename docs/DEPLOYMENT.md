# Deployment Guide

## Quick Start Deployment

### 1. Initial Setup

```bash
# Clone repository
git clone <your-repo-url>
cd AlgoBot

# Run setup script
python scripts/setup.py

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Delta Exchange

1. **Create Delta Exchange Account**
   - Go to https://www.delta.exchange
   - Complete account creation and KYC
   - **Start with testnet**: https://testnet.delta.exchange

2. **Generate API Keys**
   - Login to Delta Exchange
   - Go to Account Settings → API Management
   - Create new API key with permissions:
     - ✅ Read Account
     - ✅ Place Orders
     - ✅ Cancel Orders
     - ✅ View Positions
   - **Save your API secret** (shown only once)

3. **Update .env file**
   ```bash
   DELTA_API_KEY=your_actual_api_key_here
   DELTA_API_SECRET=your_actual_api_secret_here
   DELTA_TESTNET=true  # Start with testnet
   ```

### 3. Test Connection

```bash
# Test your Delta Exchange connection
python scripts/test_connection.py
```

Expected output:
```
✅ Connection successful
✅ Balance data retrieved
✅ Trading symbol BTCUSDT_PERP found
✅ ALL TESTS PASSED!
```

### 4. Start Bot

```bash
# Direct execution
python src/main.py

# Or using run script
python run.py
```

## Docker Deployment

### 1. Quick Docker Setup

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f algobot

# Stop
docker-compose down
```

### 2. Production Docker Setup

```bash
# Copy environment file
cp .env.example .env

# Edit with your credentials
nano .env

# Build production image
docker build -t algobot:latest .

# Run with proper configuration
docker run -d \
  --name algobot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -p 8000:8000 \
  algobot:latest
```

## Cloud Deployment

### AWS Deployment

#### 1. EC2 Setup

```bash
# Launch EC2 instance (Ubuntu 22.04)
# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# Clone repository
git clone <your-repo-url>
cd AlgoBot

# Configure environment
nano .env

# Deploy
docker-compose up -d
```

#### 2. ECS Deployment

```bash
# Create task definition
aws ecs register-task-definition --cli-input-json file://aws/task-definition.json

# Create service
aws ecs create-service \
  --cluster algobot-cluster \
  --service-name algobot-service \
  --task-definition algobot:1 \
  --desired-count 1
```

### Google Cloud Deployment

#### 1. Cloud Run Setup

```bash
# Build image
gcloud builds submit --tag gcr.io/YOUR_PROJECT/algobot

# Deploy to Cloud Run
gcloud run deploy algobot \
  --image gcr.io/YOUR_PROJECT/algobot \
  --platform managed \
  --region us-central1 \
  --env-vars-file .env.yaml
```

#### 2. GKE Deployment

```bash
# Create cluster
gcloud container clusters create algobot-cluster \
  --zone us-central1-a \
  --num-nodes 1

# Apply Kubernetes manifests
kubectl apply -f k8s/
```

### Azure Deployment

#### 1. Container Instances

```bash
# Create resource group
az group create --name algobot-rg --location eastus

# Create container instance
az container create \
  --resource-group algobot-rg \
  --name algobot \
  --image your-registry/algobot:latest \
  --environment-variables $(cat .env | tr '\n' ' ')
```

### VPS Deployment

#### 1. Basic VPS Setup

```bash
# Connect to VPS
ssh user@your-vps-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone and deploy
git clone <your-repo-url>
cd AlgoBot
nano .env  # Configure
docker-compose up -d
```

## Monitoring Setup

### 1. Grafana Dashboard

```bash
# Access Grafana
http://your-server:3000
# Login: admin/admin123

# Import dashboard
# Dashboard ID: 1860 (Node Exporter)
```

### 2. Log Monitoring

```bash
# Real-time logs
docker-compose logs -f algobot

# Log rotation setup
sudo nano /etc/logrotate.d/algobot
```

### 3. Alerting

```bash
# Email alerts (example)
# Configure in config/alerts.yaml
```

## Security Best Practices

### 1. API Key Security

- ✅ Use environment variables
- ✅ Never commit keys to Git
- ✅ Use different keys for testnet/mainnet
- ✅ Rotate keys regularly
- ✅ Use IP whitelisting if available

### 2. Server Security

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Setup firewall
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 8000  # Bot API
sudo ufw allow 3000  # Grafana

# Install fail2ban
sudo apt install fail2ban
```

### 3. SSL/TLS Setup

```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Configure nginx proxy
sudo nano /etc/nginx/sites-available/algobot
```

## Maintenance

### 1. Regular Updates

```bash
# Update code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### 2. Database Maintenance

```bash
# Backup database
docker exec algobot-postgres pg_dump -U algobot algobot > backup.sql

# Restore database
docker exec -i algobot-postgres psql -U algobot algobot < backup.sql
```

### 3. Log Management

```bash
# Compress old logs
gzip data/logs/bot.log.1

# Clean old logs
find data/logs -name "*.log.*" -mtime +7 -delete
```

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   ```bash
   # Check credentials
   python scripts/test_connection.py
   
   # Verify network
   ping api.delta.exchange
   ```

2. **Docker Issues**
   ```bash
   # Check container status
   docker ps
   
   # View logs
   docker logs algobot
   
   # Restart container
   docker restart algobot
   ```

3. **Permission Issues**
   ```bash
   # Fix data directory permissions
   sudo chown -R $USER:$USER data/
   chmod -R 755 data/
   ```

### Health Checks

```bash
# Check bot health
curl http://localhost:8000/health

# Check bot status
curl http://localhost:8000/status

# Check system resources
docker stats algobot
```

## Performance Optimization

### 1. System Resources

```bash
# Monitor resources
htop
df -h
free -h

# Optimize Docker
echo '{"log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "3"}}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

### 2. Database Optimization

```bash
# PostgreSQL tuning
# Edit postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
```

### 3. Network Optimization

```bash
# Optimize network settings
echo 'net.core.rmem_max = 16777216' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 16777216' >> /etc/sysctl.conf
sysctl -p
```

## Scaling

### 1. Horizontal Scaling

```bash
# Multiple instances
docker-compose scale algobot=3

# Load balancer setup
# Configure nginx or HAProxy
```

### 2. Vertical Scaling

```bash
# Increase container resources
docker update --memory=2g --cpus=2 algobot
```

## Backup Strategy

### 1. Automated Backups

```bash
# Setup cron job
0 2 * * * /home/user/AlgoBot/scripts/backup.sh
```

### 2. Configuration Backup

```bash
# Backup important files
tar -czf backup-$(date +%Y%m%d).tar.gz \
  .env \
  data/models/ \
  data/logs/ \
  config/
```

## Disaster Recovery

### 1. Recovery Plan

1. **Stop bot immediately**
2. **Assess damage**
3. **Restore from backup**
4. **Verify configuration**
5. **Test connections**
6. **Resume trading**

### 2. Emergency Procedures

```bash
# Emergency stop
docker-compose down
pkill -f "python src/main.py"

# Emergency position closure
python scripts/emergency_close.py
```

---

**Important**: Always test your deployment thoroughly in a testnet environment before using real funds.
