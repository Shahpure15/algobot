#!/usr/bin/env python3
# scripts/setup.py
import os
import sys
from pathlib import Path

# Colors for Linux terminal
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def print_colored(message, color):
    """Print colored message if terminal supports it"""
    if sys.stdout.isatty():
        print(f"{color}{message}{Colors.NC}")
    else:
        print(message)

def print_success(message):
    print_colored(f"✅ {message}", Colors.GREEN)

def print_error(message):
    print_colored(f"❌ {message}", Colors.RED)

def print_warning(message):
    print_colored(f"⚠️ {message}", Colors.YELLOW)

def print_info(message):
    print_colored(f"ℹ️ {message}", Colors.BLUE)

def create_directories():
    """Create necessary directories"""
    directories = [
        'data/logs',
        'data/models',
        'data/historical',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print_success(f"Created directory: {directory}")

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print_warning(".env file not found")
        print_info("Creating .env file from template...")
        
        # Create .env from template
        template_content = """# Delta Exchange API Configuration
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

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=data/logs/bot.log

# Environment
ENVIRONMENT=development
DEBUG=false
"""
        
        with open('.env', 'w') as f:
            f.write(template_content)
        
        print_success(".env file created")
        print_warning("IMPORTANT: Please edit .env file and add your Delta Exchange API credentials")
        return False
    
    # Check if required variables are set
    required_vars = ['DELTA_API_KEY', 'DELTA_API_SECRET']
    missing_vars = []
    
    with open('.env', 'r') as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=your_" in content or f"{var}=" in content and f"{var}=\n" in content:
                missing_vars.append(var)
    
    if missing_vars:
        print_warning(f"Missing required variables in .env: {', '.join(missing_vars)}")
        return False
    
    print_success(".env file looks good")
    return True

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print_error("Python 3.8+ required")
        print(f"Current version: {sys.version}")
        return False
    
    print_success(f"Python version: {sys.version}")
    return True

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 ALGOBOT SETUP FOR LINUX")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Create directories
    print("\n1. Creating directories...")
    create_directories()
    
    # Check .env file
    print("\n2. Checking configuration...")
    env_ok = check_env_file()
    
    # Installation instructions
    print("\n3. Next steps:")
    print_info("Install dependencies:")
    print("   pip install -r requirements.txt")
    print("   # Or use the automated script:")
    print("   bash setup_linux.sh")
    
    if not env_ok:
        print_info("Edit .env file with your Delta Exchange API credentials:")
        print("   nano .env")
        print("   # Get API keys from: https://testnet.delta.exchange (for testnet)")
    
    print_info("Test connection:")
    print("   python scripts/test_connection.py")
    
    print_info("Start the bot:")
    print("   python src/main.py")
    print("   # Or use:")
    print("   bash run_linux.sh")
    
    print("\n" + "=" * 60)
    if env_ok:
        print_success("Setup complete! You can now run the bot.")
    else:
        print_warning("Setup incomplete. Please configure your API credentials.")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
