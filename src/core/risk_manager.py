# src/core/risk_manager.py
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from src.utils.logger import get_logger
from config.settings import config

@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    side: str  # 'buy' or 'sell'
    size: float
    entry_price: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    current_price: Optional[float] = None
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized PnL"""
        if not self.current_price:
            return 0.0
        
        if self.side == 'buy':
            return (self.current_price - self.entry_price) * self.size
        else:
            return (self.entry_price - self.current_price) * self.size
    
    @property
    def pnl_percentage(self) -> float:
        """Calculate PnL as percentage"""
        if not self.current_price:
            return 0.0
        
        return (self.unrealized_pnl / (self.entry_price * self.size)) * 100

@dataclass
class TradeSignal:
    """Represents a trading signal"""
    symbol: str
    side: str
    confidence: float
    timestamp: datetime
    price: float
    features: Dict

class RiskManager:
    """Comprehensive risk management system"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.positions: List[Position] = []
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_balance = 0.0
        self.daily_trades = 0
        self.last_reset = datetime.now().date()
        self.balance = 0.0
        self.initial_balance = 0.0
        self.trade_history: List[Dict] = []
        self.circuit_breaker_active = False
        
    def update_balance(self, balance: float) -> None:
        """Update current balance and track peak"""
        self.balance = balance
        if self.initial_balance == 0:
            self.initial_balance = balance
            
        if balance > self.peak_balance:
            self.peak_balance = balance
            
        # Calculate drawdown
        if self.peak_balance > 0:
            current_drawdown = (self.peak_balance - balance) / self.peak_balance
            self.max_drawdown = max(self.max_drawdown, current_drawdown)
    
    def add_position(self, position: Position) -> None:
        """Add a new position"""
        self.positions.append(position)
        self.logger.info(f"Added position: {position.symbol} {position.side} {position.size}")
    
    def remove_position(self, symbol: str, side: str) -> Optional[Position]:
        """Remove a position"""
        for i, pos in enumerate(self.positions):
            if pos.symbol == symbol and pos.side == side:
                removed_pos = self.positions.pop(i)
                self.logger.info(f"Removed position: {symbol} {side}")
                return removed_pos
        return None
    
    def update_position_prices(self, symbol: str, current_price: float) -> None:
        """Update current prices for all positions of a symbol"""
        for position in self.positions:
            if position.symbol == symbol:
                position.current_price = current_price
    
    def calculate_position_size(self, signal: TradeSignal, account_balance: float) -> float:
        """Calculate position size based on risk management rules"""
        # Reset daily counters if needed
        self._reset_daily_counters()
        
        # Check circuit breaker
        if self.circuit_breaker_active:
            self.logger.warning("Circuit breaker active - no new positions")
            return 0.0
        
        # Check daily loss limit
        if self.daily_pnl <= -config.trading.max_daily_loss * account_balance:
            self.logger.warning("Daily loss limit reached")
            self.circuit_breaker_active = True
            return 0.0
        
        # Check maximum open positions
        if len(self.positions) >= config.trading.max_open_positions:
            self.logger.warning("Maximum open positions reached")
            return 0.0
        
        # Calculate base position size
        risk_amount = account_balance * config.trading.risk_per_trade
        
        # Adjust for confidence
        confidence_multiplier = min(signal.confidence / config.ml.min_confidence, 1.5)
        adjusted_risk = risk_amount * confidence_multiplier
        
        # Calculate position size based on stop loss
        if signal.side == 'buy':
            stop_loss_price = signal.price * (1 - config.trading.stop_loss_pct)
        else:
            stop_loss_price = signal.price * (1 + config.trading.stop_loss_pct)
        
        price_diff = abs(signal.price - stop_loss_price)
        position_size = adjusted_risk / price_diff
        
        # Apply maximum position size limit
        max_size = config.trading.max_position_size * account_balance / signal.price
        position_size = min(position_size, max_size)
        
        self.logger.info(f"Calculated position size: {position_size:.6f} for {signal.symbol}")
        return position_size
    
    def should_execute_trade(self, signal: TradeSignal) -> bool:
        """Determine if a trade should be executed"""
        # Reset daily counters if needed
        self._reset_daily_counters()
        
        # Check circuit breaker
        if self.circuit_breaker_active:
            return False
        
        # Check confidence threshold
        if signal.confidence < config.ml.min_confidence:
            self.logger.info(f"Signal confidence too low: {signal.confidence:.3f}")
            return False
        
        # Check daily loss limit
        if self.daily_pnl <= -config.trading.max_daily_loss * self.balance:
            self.logger.warning("Daily loss limit reached")
            return False
        
        # Check maximum open positions
        if len(self.positions) >= config.trading.max_open_positions:
            self.logger.warning("Maximum open positions reached")
            return False
        
        # Check if we already have a position in this symbol
        existing_position = self._get_position(signal.symbol)
        if existing_position:
            self.logger.info(f"Already have position in {signal.symbol}")
            return False
        
        # Check maximum drawdown
        if self.max_drawdown > 0.15:  # 15% max drawdown
            self.logger.warning(f"High drawdown detected: {self.max_drawdown:.2%}")
            return False
        
        return True
    
    def check_exit_conditions(self, position: Position) -> Tuple[bool, str]:
        """Check if position should be closed"""
        if not position.current_price:
            return False, "No current price"
        
        # Check stop loss
        if position.stop_loss:
            if position.side == 'buy' and position.current_price <= position.stop_loss:
                return True, "Stop loss triggered"
            elif position.side == 'sell' and position.current_price >= position.stop_loss:
                return True, "Stop loss triggered"
        
        # Check take profit
        if position.take_profit:
            if position.side == 'buy' and position.current_price >= position.take_profit:
                return True, "Take profit triggered"
            elif position.side == 'sell' and position.current_price <= position.take_profit:
                return True, "Take profit triggered"
        
        # Check time-based exit (e.g., hold for max 24 hours)
        if datetime.now() - position.entry_time > timedelta(hours=24):
            return True, "Time-based exit"
        
        # Check percentage-based exit
        if position.pnl_percentage <= -5.0:  # 5% loss
            return True, "Percentage loss limit"
        
        return False, "No exit condition met"
    
    def calculate_stop_loss_take_profit(self, signal: TradeSignal) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        if signal.side == 'buy':
            stop_loss = signal.price * (1 - config.trading.stop_loss_pct)
            take_profit = signal.price * (1 + config.trading.take_profit_pct)
        else:
            stop_loss = signal.price * (1 + config.trading.stop_loss_pct)
            take_profit = signal.price * (1 - config.trading.take_profit_pct)
        
        return stop_loss, take_profit
    
    def record_trade(self, symbol: str, side: str, size: float, entry_price: float, 
                    exit_price: float, pnl: float, reason: str) -> None:
        """Record completed trade"""
        trade = {
            'symbol': symbol,
            'side': side,
            'size': size,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_percentage': (pnl / (entry_price * size)) * 100,
            'reason': reason,
            'timestamp': datetime.now()
        }
        
        self.trade_history.append(trade)
        self.daily_pnl += pnl
        self.daily_trades += 1
        
        self.logger.info(f"Trade recorded: {symbol} {side} PnL: {pnl:.4f} ({reason})")
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        total_exposure = sum(pos.size * pos.entry_price for pos in self.positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions)
        
        return {
            'balance': self.balance,
            'daily_pnl': self.daily_pnl,
            'unrealized_pnl': total_unrealized_pnl,
            'total_exposure': total_exposure,
            'max_drawdown': self.max_drawdown,
            'open_positions': len(self.positions),
            'daily_trades': self.daily_trades,
            'circuit_breaker_active': self.circuit_breaker_active,
            'exposure_ratio': total_exposure / self.balance if self.balance > 0 else 0
        }
    
    def _get_position(self, symbol: str) -> Optional[Position]:
        """Get position by symbol"""
        for position in self.positions:
            if position.symbol == symbol:
                return position
        return None
    
    def _reset_daily_counters(self) -> None:
        """Reset daily counters if new day"""
        current_date = datetime.now().date()
        if current_date != self.last_reset:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.circuit_breaker_active = False
            self.last_reset = current_date
            self.logger.info("Daily counters reset")
    
    def emergency_close_all(self) -> List[Position]:
        """Emergency close all positions"""
        positions_to_close = self.positions.copy()
        self.positions.clear()
        self.circuit_breaker_active = True
        self.logger.critical("Emergency close all positions triggered")
        return positions_to_close
    
    def get_position_summary(self) -> Dict:
        """Get summary of all positions"""
        if not self.positions:
            return {'total_positions': 0, 'total_pnl': 0.0, 'positions': []}
        
        positions_data = []
        total_pnl = 0.0
        
        for pos in self.positions:
            pos_data = {
                'symbol': pos.symbol,
                'side': pos.side,
                'size': pos.size,
                'entry_price': pos.entry_price,
                'current_price': pos.current_price,
                'unrealized_pnl': pos.unrealized_pnl,
                'pnl_percentage': pos.pnl_percentage,
                'entry_time': pos.entry_time,
                'stop_loss': pos.stop_loss,
                'take_profit': pos.take_profit
            }
            positions_data.append(pos_data)
            total_pnl += pos.unrealized_pnl
        
        return {
            'total_positions': len(self.positions),
            'total_pnl': total_pnl,
            'positions': positions_data
        }