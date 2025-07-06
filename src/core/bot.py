# src/core/bot.py
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from src.utils.logger import get_logger, setup_logger
from src.exchanges.delta.clients import DeltaExchangeClient
from src.exchanges.delta.websocket import DeltaWebSocketClient
from src.core.strategy import TradingStrategy
from src.core.risk_manager import RiskManager, Position, TradeSignal
from src.data.indicators import TechnicalIndicators
from src.utils.exceptions import TradingBotException
from config.settings import config

class AlgoTradingBot:
    """Main algorithmic trading bot"""
    
    def __init__(self):
        # Setup logging
        setup_logger()
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.exchange_client = None
        self.websocket_client = None
        self.strategy = TradingStrategy()
        self.risk_manager = RiskManager()
        self.indicators = TechnicalIndicators()
        
        # State management
        self.is_running = False
        self.is_connected = False
        self.last_heartbeat = datetime.now()
        self.performance_metrics = {}
        
        # Data storage
        self.market_data = pd.DataFrame()
        self.current_balance = 0.0
        
    def initialize(self) -> bool:
        """Initialize the bot with exchange connection"""
        try:
            self.logger.info("Initializing AlgoTradingBot...")
            
            # Validate configuration
            config.validate()
            
            # Initialize exchange client
            self.exchange_client = DeltaExchangeClient(
                api_key=config.exchange.api_key,
                api_secret=config.exchange.api_secret,
                testnet=config.exchange.testnet
            )
            
            # Test connection
            if not self.exchange_client.test_connection():
                self.logger.error("Failed to connect to Delta Exchange")
                return False
            
            # Get initial account balance
            balance_data = self.exchange_client.get_account_balance()
            self.current_balance = self._extract_balance(balance_data)
            self.risk_manager.update_balance(self.current_balance)
            
            self.logger.info(f"Current balance: ${self.current_balance:.2f}")
            
            # Initialize WebSocket client
            self.websocket_client = DeltaWebSocketClient(
                symbol=config.trading.symbol,
                interval=config.trading.timeframe
            )
            
            # Set up WebSocket callbacks
            self.websocket_client.set_data_callback(self._on_market_data)
            self.websocket_client.set_error_callback(self._on_websocket_error)
            
            self.is_connected = True
            self.logger.info("Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {e}")
            return False
    
    def start(self) -> None:
        """Start the trading bot"""
        if not self.is_connected:
            self.logger.error("Bot not initialized. Call initialize() first.")
            return
        
        try:
            self.logger.info("Starting AlgoTradingBot...")
            self.is_running = True
            
            # Start WebSocket connection
            self.websocket_client.start()
            
            # Start main trading loop
            asyncio.run(self._main_loop())
            
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Bot stopped due to error: {e}")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the trading bot"""
        self.logger.info("Stopping AlgoTradingBot...")
        self.is_running = False
        
        if self.websocket_client:
            self.websocket_client.stop()
        
        # Close any open positions if needed
        self._emergency_shutdown()
        
        self.logger.info("Bot stopped")
    
    async def _main_loop(self) -> None:
        """Main trading loop"""
        while self.is_running:
            try:
                # Update heartbeat
                self.last_heartbeat = datetime.now()
                
                # Check WebSocket health
                if not self.websocket_client.is_healthy():
                    self.logger.warning("WebSocket connection unhealthy, attempting restart...")
                    self.websocket_client.start()
                
                # Get latest market data
                latest_data = self.websocket_client.get_latest_data(config.ml.lookback_period)
                
                if len(latest_data) >= 50:  # Minimum data required
                    # Update market data
                    self.market_data = latest_data
                    
                    # Update position prices
                    current_price = latest_data.iloc[-1]['close']
                    self.risk_manager.update_position_prices(config.trading.symbol, current_price)
                    
                    # Check for exit conditions
                    await self._check_exit_conditions()
                    
                    # Generate trading signals
                    await self._process_trading_signals()
                    
                    # Update performance metrics
                    self._update_performance_metrics()
                
                # Sleep for a short interval
                await asyncio.sleep(5)  # 5 second intervals
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def _process_trading_signals(self) -> None:
        """Process trading signals and execute trades"""
        try:
            # Generate signal
            signal = self.strategy.generate_signal(self.market_data)
            
            if signal is None:
                return
            
            # Check risk management
            if not self.risk_manager.should_execute_trade(signal):
                self.logger.info(f"Trade rejected by risk management: {signal.symbol}")
                return
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(signal, self.current_balance)
            
            if position_size <= 0:
                self.logger.info("Position size too small, skipping trade")
                return
            
            # Execute trade
            await self._execute_trade(signal, position_size)
            
        except Exception as e:
            self.logger.error(f"Error processing trading signals: {e}")
    
    async def _execute_trade(self, signal: TradeSignal, position_size: float) -> None:
        """Execute a trade"""
        try:
            self.logger.info(f"Executing trade: {signal.side} {signal.symbol} "
                           f"size: {position_size:.6f} confidence: {signal.confidence:.3f}")
            
            # Place order
            order_result = self.exchange_client.place_order(
                symbol=signal.symbol,
                side=signal.side,
                size=position_size,
                order_type='market'
            )
            
            if order_result.get('success'):
                # Calculate stop loss and take profit
                stop_loss, take_profit = self.risk_manager.calculate_stop_loss_take_profit(signal)
                
                # Create position
                position = Position(
                    symbol=signal.symbol,
                    side=signal.side,
                    size=position_size,
                    entry_price=signal.price,
                    entry_time=signal.timestamp,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    current_price=signal.price
                )
                
                # Add to risk manager
                self.risk_manager.add_position(position)
                
                self.logger.info(f"Trade executed successfully: {order_result}")
                
                # Update balance
                await self._update_balance()
                
            else:
                self.logger.error(f"Trade execution failed: {order_result}")
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
    
    async def _check_exit_conditions(self) -> None:
        """Check exit conditions for open positions"""
        try:
            positions_to_close = []
            
            for position in self.risk_manager.positions:
                should_exit, reason = self.risk_manager.check_exit_conditions(position)
                
                if should_exit:
                    positions_to_close.append((position, reason))
            
            # Close positions
            for position, reason in positions_to_close:
                await self._close_position(position, reason)
                
        except Exception as e:
            self.logger.error(f"Error checking exit conditions: {e}")
    
    async def _close_position(self, position: Position, reason: str) -> None:
        """Close a position"""
        try:
            self.logger.info(f"Closing position: {position.symbol} {position.side} - {reason}")
            
            # Determine opposite side
            close_side = 'sell' if position.side == 'buy' else 'buy'
            
            # Place closing order
            order_result = self.exchange_client.place_order(
                symbol=position.symbol,
                side=close_side,
                size=position.size,
                order_type='market'
            )
            
            if order_result.get('success'):
                # Calculate PnL
                exit_price = position.current_price or position.entry_price
                pnl = position.unrealized_pnl
                
                # Record trade
                self.risk_manager.record_trade(
                    symbol=position.symbol,
                    side=position.side,
                    size=position.size,
                    entry_price=position.entry_price,
                    exit_price=exit_price,
                    pnl=pnl,
                    reason=reason
                )
                
                # Remove position
                self.risk_manager.remove_position(position.symbol, position.side)
                
                self.logger.info(f"Position closed successfully. PnL: ${pnl:.2f}")
                
                # Update balance
                await self._update_balance()
                
            else:
                self.logger.error(f"Failed to close position: {order_result}")
                
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
    
    async def _update_balance(self) -> None:
        """Update current account balance"""
        try:
            balance_data = self.exchange_client.get_account_balance()
            self.current_balance = self._extract_balance(balance_data)
            self.risk_manager.update_balance(self.current_balance)
            
        except Exception as e:
            self.logger.error(f"Error updating balance: {e}")
    
    def _extract_balance(self, balance_data: Dict) -> float:
        """Extract balance from API response"""
        try:
            # This depends on Delta Exchange API response format
            # Adjust based on actual API response
            if 'result' in balance_data and isinstance(balance_data['result'], list):
                for balance in balance_data['result']:
                    if balance.get('asset') == 'USDT':  # or your base currency
                        return float(balance.get('balance', 0))
            return 0.0
        except Exception as e:
            self.logger.error(f"Error extracting balance: {e}")
            return 0.0
    
    def _on_market_data(self, candle: Dict) -> None:
        """Handle new market data"""
        try:
            # Log new candle data
            self.logger.debug(f"New candle: {candle['timestamp']} "
                           f"O:{candle['open']:.2f} H:{candle['high']:.2f} "
                           f"L:{candle['low']:.2f} C:{candle['close']:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error processing market data: {e}")
    
    def _on_websocket_error(self, error) -> None:
        """Handle WebSocket errors"""
        self.logger.error(f"WebSocket error: {error}")
        
        # Implement error handling logic
        if not self.websocket_client.is_healthy():
            self.logger.warning("WebSocket connection lost, attempting to reconnect...")
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics"""
        try:
            risk_metrics = self.risk_manager.get_risk_metrics()
            
            self.performance_metrics = {
                'balance': self.current_balance,
                'total_trades': self.risk_manager.daily_trades,
                'daily_pnl': risk_metrics['daily_pnl'],
                'unrealized_pnl': risk_metrics['unrealized_pnl'],
                'max_drawdown': risk_metrics['max_drawdown'],
                'open_positions': len(self.risk_manager.positions),
                'last_heartbeat': self.last_heartbeat,
                'uptime': datetime.now() - self.last_heartbeat
            }
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
    
    def _emergency_shutdown(self) -> None:
        """Emergency shutdown procedures"""
        try:
            self.logger.warning("Executing emergency shutdown...")
            
            # Close all open positions
            positions_to_close = self.risk_manager.emergency_close_all()
            
            for position in positions_to_close:
                try:
                    close_side = 'sell' if position.side == 'buy' else 'buy'
                    self.exchange_client.place_order(
                        symbol=position.symbol,
                        side=close_side,
                        size=position.size,
                        order_type='market'
                    )
                    self.logger.info(f"Emergency closed position: {position.symbol}")
                except Exception as e:
                    self.logger.error(f"Failed to emergency close position: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error during emergency shutdown: {e}")
    
    def get_status(self) -> Dict:
        """Get bot status"""
        return {
            'is_running': self.is_running,
            'is_connected': self.is_connected,
            'current_balance': self.current_balance,
            'performance_metrics': self.performance_metrics,
            'risk_metrics': self.risk_manager.get_risk_metrics(),
            'position_summary': self.risk_manager.get_position_summary(),
            'strategy_state': self.strategy.get_strategy_state()
        }
    
    def get_logs(self, lines: int = 50) -> List[str]:
        """Get recent log entries"""
        try:
            with open(config.logging.file_path, 'r') as f:
                return f.readlines()[-lines:]
        except Exception as e:
            self.logger.error(f"Error reading logs: {e}")
            return []
