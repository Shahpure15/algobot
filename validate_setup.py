#!/usr/bin/env python3
# validate_setup.py - Comprehensive setup validation for Linux
import sys
import os
import subprocess
import importlib
from pathlib import Path

# Colors for Linux terminal
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

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

def check_python_version():
    """Check Python version"""
    print_info("Checking Python version...")
    if sys.version_info < (3, 8):
        print_error("Python 3.8+ required")
        print(f"Current version: {sys.version}")
        return False
    print_success(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependencies():
    """Check if all dependencies are installed"""
    print_info("Checking dependencies...")
    
    required_packages = [
        'requests', 'pandas', 'numpy', 'websocket-client', 
        'python-dotenv', 'scikit-learn', 'joblib', 'pyyaml'
    ]
    
    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print_success(package)
        except ImportError:
            print_error(f"{package} - missing")
            missing.append(package)
    
    if missing:
        print_warning(f"Install missing packages: pip install {' '.join(missing)}")
        return False
    
    return True

def check_directories():
    """Check if required directories exist"""
    print("\n3. Checking directories...")
    
    required_dirs = [
        'src', 'src/core', 'src/exchanges', 'src/exchanges/delta',
        'src/data', 'src/ml', 'src/utils', 'config', 'scripts',
        'data', 'data/logs', 'data/models', 'data/historical'
    ]
    
    all_exist = True
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"   ✅ {directory}")
        else:
            print(f"   ❌ {directory} - missing")
            all_exist = False
    
    return all_exist

def check_files():
    """Check if required files exist"""
    print("\n4. Checking required files...")
    
    required_files = [
        'src/main.py', 'src/core/bot.py', 'src/core/strategy.py',
        'src/core/risk_manager.py', 'src/exchanges/delta/auth.py',
        'src/exchanges/delta/clients.py', 'src/exchanges/delta/websocket.py',
        'src/data/indicators.py', 'src/ml/predictor.py',
        'src/utils/logger.py', 'src/utils/exceptions.py',
        'config/settings.py', 'requirements.txt', 'Dockerfile',
        'docker-compose.yml', 'scripts/test_connection.py'
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - missing")
            all_exist = False
    
    return all_exist

def check_configuration():
    """Check configuration"""
    print("\n5. Checking configuration...")
    
    # Check .env file
    if not Path('.env').exists():
        print("   ❌ .env file missing")
        print("   Create .env file with your Delta Exchange credentials")
        return False
    
    print("   ✅ .env file exists")
    
    # Check if API keys are set
    with open('.env', 'r') as f:
        content = f.read()
        if 'DELTA_API_KEY=your_' in content:
            print("   ⚠️  API keys not configured")
            return False
    
    print("   ✅ API keys configured")
    return True

def test_imports():
    """Test if main modules can be imported"""
    print("\n6. Testing imports...")
    
    sys.path.append(str(Path(__file__).parent))
    
    try:
        from src.utils.logger import get_logger
        print("   ✅ Logger import")
    except ImportError as e:
        print(f"   ❌ Logger import failed: {e}")
        return False
    
    try:
        from src.utils.exceptions import TradingBotException
        print("   ✅ Exceptions import")
    except ImportError as e:
        print(f"   ❌ Exceptions import failed: {e}")
        return False
    
    try:
        from config.settings import config
        print("   ✅ Config import")
    except ImportError as e:
        print(f"   ❌ Config import failed: {e}")
        return False
    
    try:
        from src.exchanges.delta.auth import DeltaAuthenticator
        print("   ✅ Delta auth import")
    except ImportError as e:
        print(f"   ❌ Delta auth import failed: {e}")
        return False
    
    try:
        from src.exchanges.delta.clients import DeltaExchangeClient
        print("   ✅ Delta client import")
    except ImportError as e:
        print(f"   ❌ Delta client import failed: {e}")
        return False
    
    return True

def check_docker():
    """Check Docker setup"""
    print("\n7. Checking Docker setup...")
    
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {result.stdout.strip()}")
        else:
            print("   ❌ Docker not available")
            return False
    except FileNotFoundError:
        print("   ❌ Docker not installed")
        return False
    
    try:
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {result.stdout.strip()}")
        else:
            print("   ❌ Docker Compose not available")
            return False
    except FileNotFoundError:
        print("   ❌ Docker Compose not installed")
        return False
    
    return True

def run_connection_test():
    """Run connection test if possible"""
    print("\n8. Running connection test...")
    
    try:
        result = subprocess.run([sys.executable, 'scripts/test_connection.py'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ Connection test passed")
            return True
        else:
            print("   ❌ Connection test failed")
            print(f"   Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("   ⚠️  Connection test timed out")
        return False
    except Exception as e:
        print(f"   ⚠️  Connection test error: {e}")
        return False

def main():
    """Main validation function"""
    print("=" * 60)
    print("🚀 ALGOBOT SETUP VALIDATION FOR LINUX")
    print("=" * 60)
    
    # Add current directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Required Files", check_files),
        ("Configuration", check_configuration),
        ("Module Imports", test_imports),
        ("Docker Setup", check_docker),
        ("Connection Test", run_connection_test)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            print(f"\n{len(results) + 1}. {check_name}")
            print("-" * 40)
            result = check_func()
            results.append(result)
        except Exception as e:
            print_error(f"Check failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print_success("All checks passed! Your bot is ready to run on Linux.")
        print("\n🚀 Next steps:")
        print("1. Start bot: python src/main.py")
        print("2. Or with script: bash run_linux.sh")
        print("3. Or with Docker: docker-compose up -d")
        print("4. Monitor logs: tail -f data/logs/bot.log")
        return 0
    else:
        print_error("Some checks failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Run setup: bash setup_linux.sh")
        print("- Configure .env file with your API credentials")
        return 1

if __name__ == "__main__":
    sys.exit(main())
