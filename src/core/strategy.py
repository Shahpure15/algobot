# src/core/strategy.py
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from src.utils.logger import get_logger
from src.data.indicators import TechnicalIndicators
from src.ml.predictor import MLPredictor
from src.core.risk_manager import TradeSignal
from config.settings import config

@dataclass
class MarketState:
    """Represents current market state"""
    symbol: str
    timestamp: datetime
    price: float
    volume: float
    trend: str  # 'bullish', 'bearish', 'sideways'
    volatility: float
    indicators: Dict
    
class TradingStrategy:
    """Main trading strategy combining technical analysis and ML"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.indicators = TechnicalIndicators()
        self.ml_predictor = MLPredictor()
        self.last_signal_time = {}
        self.min_signal_interval = timedelta(minutes=5)  # Minimum time between signals
        
    def analyze_market(self, df: pd.DataFrame) -> MarketState:
        """Analyze current market conditions"""
        if len(df) < 50:
            raise ValueError("Insufficient data for analysis")
        
        latest = df.iloc[-1]
        
        # Calculate technical indicators
        indicators = self.indicators.calculate_all(df)
        
        # Determine trend
        trend = self._determine_trend(indicators)
        
        # Calculate volatility
        volatility = self._calculate_volatility(df)
        
        market_state = MarketState(
            symbol=latest.get('symbol', config.trading.symbol),
            timestamp=latest['timestamp'],
            price=latest['close'],
            volume=latest['volume'],
            trend=trend,
            volatility=volatility,
            indicators=indicators
        )
        
        return market_state
    
    def generate_signal(self, df: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate trading signal based on technical analysis and ML"""
        try:
            # Analyze market
            market_state = self.analyze_market(df)
            
            # Check if enough time has passed since last signal
            if not self._can_generate_signal(market_state.symbol, market_state.timestamp):
                return None
            
            # Get technical signal
            tech_signal = self._get_technical_signal(market_state)
            
            # Get ML prediction
            ml_prediction = self.ml_predictor.predict(df)
            
            # Combine signals
            combined_signal = self._combine_signals(tech_signal, ml_prediction, market_state)
            
            if combined_signal:
                self.last_signal_time[market_state.symbol] = market_state.timestamp
                self.logger.info(f"Generated signal: {combined_signal.side} {combined_signal.symbol} "
                               f"confidence: {combined_signal.confidence:.3f}")
            
            return combined_signal
            
        except Exception as e:
            self.logger.error(f"Error generating signal: {e}")
            return None
    
    def _get_technical_signal(self, market_state: MarketState) -> Optional[Dict]:
        """Generate signal based on technical indicators"""
        indicators = market_state.indicators
        
        # RSI conditions
        rsi = indicators.get('rsi', 50)
        rsi_oversold = rsi < 30
        rsi_overbought = rsi > 70
        
        # EMA conditions
        ema_9 = indicators.get('ema_9', 0)
        ema_21 = indicators.get('ema_21', 0)
        ema_200 = indicators.get('ema_200', 0)
        
        price = market_state.price
        
        # Trend conditions
        uptrend = ema_9 > ema_21 > ema_200 and price > ema_9
        downtrend = ema_9 < ema_21 < ema_200 and price < ema_9
        
        # Volume condition
        volume_avg = indicators.get('volume_avg', 0)
        volume_surge = market_state.volume > volume_avg * 1.5
        
        # MACD conditions
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_bullish = macd > macd_signal
        macd_bearish = macd < macd_signal
        
        # Generate buy signal
        buy_conditions = [
            rsi_oversold or (rsi < 50 and rsi > 30),
            uptrend,
            macd_bullish,
            volume_surge,
            market_state.trend == 'bullish'
        ]
        
        # Generate sell signal
        sell_conditions = [
            rsi_overbought or (rsi > 50 and rsi < 70),
            downtrend,
            macd_bearish,
            volume_surge,
            market_state.trend == 'bearish'
        ]
        
        buy_score = sum(buy_conditions) / len(buy_conditions)
        sell_score = sum(sell_conditions) / len(sell_conditions)
        
        if buy_score > 0.6 and buy_score > sell_score:
            return {
                'side': 'buy',
                'confidence': buy_score,
                'reasons': buy_conditions
            }
        elif sell_score > 0.6 and sell_score > buy_score:
            return {
                'side': 'sell',
                'confidence': sell_score,
                'reasons': sell_conditions
            }
        
        return None
    
    def _combine_signals(self, tech_signal: Optional[Dict], ml_prediction: Optional[Dict], 
                        market_state: MarketState) -> Optional[TradeSignal]:
        """Combine technical and ML signals"""
        if not tech_signal or not ml_prediction:
            return None
        
        # Check if signals agree
        if tech_signal['side'] != ml_prediction['direction']:
            return None
        
        # Calculate combined confidence
        tech_weight = 0.4
        ml_weight = 0.6
        
        combined_confidence = (
            tech_signal['confidence'] * tech_weight + 
            ml_prediction['confidence'] * ml_weight
        )
        
        # Apply market condition adjustments
        if market_state.volatility > 0.05:  # High volatility
            combined_confidence *= 0.8
        
        if market_state.trend == 'sideways':
            combined_confidence *= 0.7
        
        # Minimum confidence threshold
        if combined_confidence < config.ml.min_confidence:
            return None
        
        return TradeSignal(
            symbol=market_state.symbol,
            side=tech_signal['side'],
            confidence=combined_confidence,
            timestamp=market_state.timestamp,
            price=market_state.price,
            features={
                'technical': tech_signal,
                'ml': ml_prediction,
                'market_state': market_state.__dict__
            }
        )
    
    def _determine_trend(self, indicators: Dict) -> str:
        """Determine market trend"""
        ema_9 = indicators.get('ema_9', 0)
        ema_21 = indicators.get('ema_21', 0)
        ema_200 = indicators.get('ema_200', 0)
        
        if ema_9 > ema_21 > ema_200:
            return 'bullish'
        elif ema_9 < ema_21 < ema_200:
            return 'bearish'
        else:
            return 'sideways'
    
    def _calculate_volatility(self, df: pd.DataFrame, period: int = 20) -> float:
        """Calculate price volatility"""
        if len(df) < period:
            return 0.0
        
        returns = df['close'].pct_change().dropna()
        return returns.tail(period).std()
    
    def _can_generate_signal(self, symbol: str, current_time: datetime) -> bool:
        """Check if enough time has passed since last signal"""
        if symbol not in self.last_signal_time:
            return True
        
        time_diff = current_time - self.last_signal_time[symbol]
        return time_diff >= self.min_signal_interval
    
    def get_strategy_state(self) -> Dict:
        """Get current strategy state"""
        return {
            'last_signal_times': self.last_signal_time,
            'min_signal_interval': self.min_signal_interval.total_seconds(),
            'ml_model_loaded': self.ml_predictor.is_model_loaded()
        }