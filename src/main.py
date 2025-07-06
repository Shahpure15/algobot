# src/main.py
import sys
import signal
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.core.bot import AlgoTradingBot
from src.utils.logger import get_logger
from config.settings import config

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nShutdown signal received. Stopping bot...")
    if 'bot' in globals():
        bot.stop()
    sys.exit(0)

def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create bot instance
    bot = AlgoTradingBot()
    
    try:
        # Initialize bot
        if not bot.initialize():
            print("Failed to initialize bot. Check logs for details.")
            return 1
        
        # Start trading
        print("Starting AlgoTradingBot...")
        print(f"Trading Symbol: {config.trading.symbol}")
        print(f"Environment: {config.environment}")
        print(f"Testnet: {config.exchange.testnet}")
        print("Press Ctrl+C to stop the bot")
        
        # Make bot available to signal handler
        globals()['bot'] = bot
        
        # Start bot
        bot.start()
        
    except Exception as e:
        print(f"Error starting bot: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
