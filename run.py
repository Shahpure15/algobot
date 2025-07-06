#!/usr/bin/env python3
# run.py - Simple script to run the bot on Linux/Unix systems
import sys
import os
from pathlib import Path

# Add current directory and src to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / 'src'))

def check_requirements():
    """Check if all requirements are met"""
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        print(f"Current version: {sys.version}")
        return False
    
    # Check if .env exists
    if not Path('.env').exists():
        print("❌ .env file not found!")
        print("Please create .env file with your Delta Exchange credentials")
        print("Run: python scripts/setup.py")
        return False
    
    # Check if API keys are configured
    try:
        with open('.env', 'r') as f:
            content = f.read()
            if 'DELTA_API_KEY=your_' in content:
                print("❌ API keys not configured!")
                print("Please edit .env file with your actual Delta Exchange credentials")
                return False
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False
    
    return True

def main():
    """Main entry point"""
    print("🚀 Starting AlgoBot...")
    
    # Check requirements
    if not check_requirements():
        return 1
    
    # Import and run
    try:
        from src.main import main as bot_main
        return bot_main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        print("Or run setup: bash setup_linux.sh")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
