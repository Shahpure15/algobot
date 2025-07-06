#!/usr/bin/env python
# validate_setup.py - Comprehensive setup validation
import sys
import os
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Check Python version"""
    print("1. Checking Python version...")
    if sys.version_info < (3, 8):
        print("   ❌ Python 3.8+ required")
        return False
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependencies():
    """Check if all dependencies are installed"""
    print("\n2. Checking dependencies...")
    
    required_packages = [
        'requests', 'pandas', 'numpy', 'websocket-client', 
        'python-dotenv', 'scikit-learn', 'joblib', 'pyyaml'
    ]
    
    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - missing")
            missing.append(package)
    
    if missing:
        print(f"\n   Install missing packages: pip install {' '.join(missing)}")
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
    print("ALGOBOT SETUP VALIDATION")
    print("=" * 60)
    
    checks = [
        check_python_version,
        check_dependencies,
        check_directories,
        check_files,
        check_configuration,
        test_imports,
        check_docker,
        run_connection_test
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Check failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All checks passed! Your bot is ready to run.")
        print("\nNext steps:")
        print("1. Start bot: python src/main.py")
        print("2. Or with Docker: docker-compose up -d")
        print("3. Monitor logs: tail -f data/logs/bot.log")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Run setup: python scripts/setup.py")
        print("- Configure .env file with your API credentials")
        return 1

if __name__ == "__main__":
    sys.exit(main())
