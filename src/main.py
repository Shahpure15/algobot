# src/main.py
import sys
import signal
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.bot import AlgoTradingBot
from src.utils.logger import get_logger
from config.settings import config

# Global bot instance for signal handler
bot = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    if bot:
        bot.stop()
    sys.exit(0)

def main():
    """Main entry point"""
    global bot
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    # Handle SIGHUP on Linux (terminal hangup)
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, signal_handler)
    
    try:
        # Create bot instance
        bot = AlgoTradingBot()
        
        # Initialize bot
        print("Initializing AlgoBot...")
        if not bot.initialize():
            print("❌ Failed to initialize bot. Check logs for details.")
            return 1
        
        # Display startup information
        print("=" * 60)
        print("🚀 ALGOBOT STARTED SUCCESSFULLY")
        print("=" * 60)
        print(f"📊 Trading Symbol: {config.trading.symbol}")
        print(f"⏰ Timeframe: {config.trading.timeframe}")
        print(f"🌐 Environment: {config.environment}")
        print(f"🧪 Testnet: {config.exchange.testnet}")
        print(f"💰 Position Size: {config.trading.position_size}")
        print(f"⚠️  Risk per Trade: {config.trading.risk_per_trade * 100}%")
        print("=" * 60)
        print("🔄 Bot is running... Press Ctrl+C to stop")
        print("📊 Monitor: http://localhost:8000/health")
        print("📝 Logs: data/logs/bot.log")
        print("=" * 60)
        
        # Start trading
        bot.start()
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        if bot:
            bot.stop()
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        if bot:
            bot.stop()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
