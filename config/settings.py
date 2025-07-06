# config/settings.py
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ExchangeConfig:
    """Exchange configuration"""
    api_key: str
    api_secret: str
    testnet: bool = True
    base_url: Optional[str] = None
    
    def __post_init__(self):
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret are required")

@dataclass
class TradingConfig:
    """Trading configuration"""
    symbol: str = "BTCUSDT_PERP"
    timeframe: str = "5m"
    position_size: float = 0.01
    max_position_size: float = 0.1
    risk_per_trade: float = 0.02  # 2% risk per trade
    max_daily_loss: float = 0.05  # 5% max daily loss
    stop_loss_pct: float = 0.02   # 2% stop loss
    take_profit_pct: float = 0.04  # 4% take profit
    max_open_positions: int = 3
    
@dataclass
class MLConfig:
    """Machine learning configuration"""
    model_path: str = "data/models/"
    retrain_interval_hours: int = 24
    min_confidence: float = 0.65
    lookback_period: int = 200
    feature_columns: list = None
    
    def __post_init__(self):
        if self.feature_columns is None:
            self.feature_columns = [
                'ema_9', 'ema_21', 'ema_200', 'rsi', 'atr', 'volume', 'vol_avg'
            ]

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "sqlite:///data/trading_bot.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    file_path: str = "data/logs/bot.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.exchange = ExchangeConfig(
            api_key=os.getenv("DELTA_API_KEY", ""),
            api_secret=os.getenv("DELTA_API_SECRET", ""),
            testnet=os.getenv("DELTA_TESTNET", "true").lower() == "true"
        )
        
        self.trading = TradingConfig(
            symbol=os.getenv("TRADING_SYMBOL", "BTCUSDT_PERP"),
            timeframe=os.getenv("TRADING_TIMEFRAME", "5m"),
            position_size=float(os.getenv("POSITION_SIZE", "0.01")),
            max_position_size=float(os.getenv("MAX_POSITION_SIZE", "0.1")),
            risk_per_trade=float(os.getenv("RISK_PER_TRADE", "0.02")),
            max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", "0.05")),
            stop_loss_pct=float(os.getenv("STOP_LOSS_PCT", "0.02")),
            take_profit_pct=float(os.getenv("TAKE_PROFIT_PCT", "0.04")),
            max_open_positions=int(os.getenv("MAX_OPEN_POSITIONS", "3"))
        )
        
        self.ml = MLConfig(
            model_path=os.getenv("MODEL_PATH", "data/models/"),
            retrain_interval_hours=int(os.getenv("RETRAIN_INTERVAL", "24")),
            min_confidence=float(os.getenv("MIN_CONFIDENCE", "0.65")),
            lookback_period=int(os.getenv("LOOKBACK_PERIOD", "200"))
        )
        
        self.database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///data/trading_bot.db"),
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )
        
        self.logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file_path=os.getenv("LOG_FILE", "data/logs/bot.log")
        )
        
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
    
    def validate(self) -> None:
        """Validate configuration"""
        errors = []
        
        # Validate exchange config
        if not self.exchange.api_key:
            errors.append("DELTA_API_KEY is required")
        if not self.exchange.api_secret:
            errors.append("DELTA_API_SECRET is required")
        
        # Validate trading config
        if self.trading.position_size <= 0:
            errors.append("Position size must be positive")
        if self.trading.max_position_size <= self.trading.position_size:
            errors.append("Max position size must be greater than position size")
        if self.trading.risk_per_trade <= 0 or self.trading.risk_per_trade > 1:
            errors.append("Risk per trade must be between 0 and 1")
        
        # Validate ML config
        if self.ml.min_confidence < 0 or self.ml.min_confidence > 1:
            errors.append("Min confidence must be between 0 and 1")
        if self.ml.lookback_period < 50:
            errors.append("Lookback period must be at least 50")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'exchange': self.exchange.__dict__,
            'trading': self.trading.__dict__,
            'ml': self.ml.__dict__,
            'database': self.database.__dict__,
            'logging': self.logging.__dict__,
            'environment': self.environment,
            'debug': self.debug
        }

# Global configuration instance
config = Config()

# .env.example template
# Copy this to .env and fill with your actual values
"""
DELTA_API_KEY=your_api_key_here
DELTA_API_SECRET=your_api_secret_here
DELTA_TESTNET=true

TRADING_SYMBOL=BTCUSDT_PERP
TRADING_TIMEFRAME=5m
POSITION_SIZE=0.01
MAX_POSITION_SIZE=0.1
RISK_PER_TRADE=0.02
MAX_DAILY_LOSS=0.05
STOP_LOSS_PCT=0.02
TAKE_PROFIT_PCT=0.04
MAX_OPEN_POSITIONS=3

MODEL_PATH=data/models/
RETRAIN_INTERVAL=24
MIN_CONFIDENCE=0.65
LOOKBACK_PERIOD=200

DATABASE_URL=sqlite:///data/trading_bot.db
DB_ECHO=false

LOG_LEVEL=INFO
LOG_FILE=data/logs/bot.log

ENVIRONMENT=development
DEBUG=false
"""