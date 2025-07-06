#!/usr/bin/env python
# run.py - Simple script to run the bot
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

# Check if .env exists
if not Path('.env').exists():
    print("❌ .env file not found!")
    print("Run: python scripts/setup.py")
    sys.exit(1)

# Import and run
try:
    from src.main import main
    sys.exit(main())
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
