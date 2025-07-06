# src/data/indicators.py
import pandas as pd
import numpy as np
from typing import Dict, Optional
import talib
from src.utils.logger import get_logger

class TechnicalIndicators:
    """Technical indicator calculations"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def calculate_all(self, df: pd.DataFrame) -> Dict:
        """Calculate all technical indicators"""
        if len(df) < 50:
            raise ValueError("Insufficient data for indicator calculation")
        
        indicators = {}
        
        # Price data
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values
        
        try:
            # Moving averages
            indicators['ema_9'] = talib.EMA(close, timeperiod=9)[-1]
            indicators['ema_21'] = talib.EMA(close, timeperiod=21)[-1]
            indicators['ema_200'] = talib.EMA(close, timeperiod=200)[-1] if len(df) >= 200 else close[-1]
            indicators['sma_20'] = talib.SMA(close, timeperiod=20)[-1]
            indicators['sma_50'] = talib.SMA(close, timeperiod=50)[-1]
            
            # RSI
            indicators['rsi'] = talib.RSI(close, timeperiod=14)[-1]
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            indicators['macd'] = macd[-1]
            indicators['macd_signal'] = macd_signal[-1]
            indicators['macd_histogram'] = macd_hist[-1]
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
            indicators['bb_upper'] = bb_upper[-1]
            indicators['bb_middle'] = bb_middle[-1]
            indicators['bb_lower'] = bb_lower[-1]
            indicators['bb_width'] = (bb_upper[-1] - bb_lower[-1]) / bb_middle[-1]
            
            # ATR (Average True Range)
            indicators['atr'] = talib.ATR(high, low, close, timeperiod=14)[-1]
            
            # Stochastic
            stoch_k, stoch_d = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
            indicators['stoch_k'] = stoch_k[-1]
            indicators['stoch_d'] = stoch_d[-1]
            
            # CCI (Commodity Channel Index)
            indicators['cci'] = talib.CCI(high, low, close, timeperiod=14)[-1]
            
            # Williams %R
            indicators['williams_r'] = talib.WILLR(high, low, close, timeperiod=14)[-1]
            
            # Volume indicators
            indicators['volume_avg'] = talib.SMA(volume, timeperiod=20)[-1]
            indicators['volume_ratio'] = volume[-1] / indicators['volume_avg']
            
            # OBV (On-Balance Volume)
            indicators['obv'] = talib.OBV(close, volume)[-1]
            
            # ADX (Average Directional Index)
            indicators['adx'] = talib.ADX(high, low, close, timeperiod=14)[-1]
            
            # Momentum indicators
            indicators['momentum'] = talib.MOM(close, timeperiod=10)[-1]
            indicators['roc'] = talib.ROC(close, timeperiod=10)[-1]
            
            # Custom indicators
            indicators.update(self._custom_indicators(df))
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return {}
        
        return indicators
    
    def _custom_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate custom indicators"""
        indicators = {}
        
        try:
            # Price position within recent range
            recent_high = df['high'].tail(20).max()
            recent_low = df['low'].tail(20).min()
            current_price = df['close'].iloc[-1]
            
            if recent_high != recent_low:
                indicators['price_position'] = (current_price - recent_low) / (recent_high - recent_low)
            else:
                indicators['price_position'] = 0.5
            
            # Volatility indicators
            returns = df['close'].pct_change().dropna()
            indicators['volatility_10'] = returns.tail(10).std()
            indicators['volatility_20'] = returns.tail(20).std()
            
            # Support/Resistance levels
            indicators['support'] = df['low'].tail(20).min()
            indicators['resistance'] = df['high'].tail(20).max()
            
            # Trend strength
            ema_9 = df['close'].ewm(span=9).mean()
            ema_21 = df['close'].ewm(span=21).mean()
            indicators['trend_strength'] = (ema_9.iloc[-1] - ema_21.iloc[-1]) / ema_21.iloc[-1]
            
            # Volume trend
            volume_ema = df['volume'].ewm(span=10).mean()
            indicators['volume_trend'] = (df['volume'].iloc[-1] - volume_ema.iloc[-1]) / volume_ema.iloc[-1]
            
            # Price acceleration
            if len(df) >= 3:
                price_change_1 = df['close'].iloc[-1] - df['close'].iloc[-2]
                price_change_2 = df['close'].iloc[-2] - df['close'].iloc[-3]
                indicators['price_acceleration'] = price_change_1 - price_change_2
            
        except Exception as e:
            self.logger.error(f"Error calculating custom indicators: {e}")
        
        return indicators
    
    def get_signal_strength(self, indicators: Dict) -> Dict:
        """Calculate signal strength for various indicators"""
        signals = {}
        
        # RSI signals
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            signals['rsi'] = {'signal': 'buy', 'strength': min((30 - rsi) / 10, 1.0)}
        elif rsi > 70:
            signals['rsi'] = {'signal': 'sell', 'strength': min((rsi - 70) / 10, 1.0)}
        else:
            signals['rsi'] = {'signal': 'neutral', 'strength': 0.0}
        
        # MACD signals
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_diff = macd - macd_signal
        
        if macd_diff > 0:
            signals['macd'] = {'signal': 'buy', 'strength': min(abs(macd_diff) / 0.1, 1.0)}
        elif macd_diff < 0:
            signals['macd'] = {'signal': 'sell', 'strength': min(abs(macd_diff) / 0.1, 1.0)}
        else:
            signals['macd'] = {'signal': 'neutral', 'strength': 0.0}
        
        # Bollinger Bands signals
        bb_upper = indicators.get('bb_upper', 0)
        bb_lower = indicators.get('bb_lower', 0)
        bb_middle = indicators.get('bb_middle', 0)
        current_price = indicators.get('close', bb_middle)
        
        if current_price < bb_lower:
            signals['bb'] = {'signal': 'buy', 'strength': min((bb_lower - current_price) / (bb_middle - bb_lower), 1.0)}
        elif current_price > bb_upper:
            signals['bb'] = {'signal': 'sell', 'strength': min((current_price - bb_upper) / (bb_upper - bb_middle), 1.0)}
        else:
            signals['bb'] = {'signal': 'neutral', 'strength': 0.0}
        
        # Stochastic signals
        stoch