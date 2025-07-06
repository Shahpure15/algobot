# src/exchanges/delta/websocket.py
import json
import threading
import time
import websocket
import pandas as pd
from datetime import datetime
from typing import Dict, Callable, Optional, List
from src.utils.logger import get_logger
from src.utils.exceptions import WebSocketError

class DeltaWebSocketClient:
    """Robust WebSocket client for Delta Exchange"""
    
    def __init__(self, symbol: str, interval: str = "1m", max_reconnects: int = 5):
        self.symbol = symbol
        self.interval = interval
        self.max_reconnects = max_reconnects
        self.ws_url = "wss://socket.delta.exchange"
        
        # Data storage
        self.df = pd.DataFrame()
        self.lock = threading.Lock()
        
        # Connection management
        self.ws = None
        self.reconnect_count = 0
        self.is_connected = False
        self.should_reconnect = True
        
        # Callbacks
        self.on_data_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        
        self.logger = get_logger(__name__)
    
    def set_data_callback(self, callback: Callable):
        """Set callback for when new data arrives"""
        self.on_data_callback = callback
    
    def set_error_callback(self, callback: Callable):
        """Set callback for errors"""
        self.on_error_callback = callback
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            
            # Handle different message types
            if data.get('type') == 'subscriptions':
                self.logger.info(f"Subscription confirmed: {data}")
                return
            
            if data.get('type') != 'v2/candles':
                return
            
            # Process candle data
            for candle_data in data.get('payload', []):
                self._process_candle(candle_data)
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse WebSocket message: {e}")
        except Exception as e:
            self.logger.error(f"Error processing WebSocket message: {e}")
            if self.on_error_callback:
                self.on_error_callback(e)
    
    def _process_candle(self, candle_data: Dict):
        """Process individual candle data"""
        try:
            candle = {
                'timestamp': pd.to_datetime(candle_data['timestamp'], unit='s'),
                'open': float(candle_data['open']),
                'high': float(candle_data['high']),
                'low': float(candle_data['low']),
                'close': float(candle_data['close']),
                'volume': float(candle_data['volume']),
                'symbol': self.symbol
            }
            
            with self.lock:
                # Add new candle to DataFrame
                new_row = pd.DataFrame([candle])
                self.df = pd.concat([self.df, new_row], ignore_index=True)
                
                # Remove duplicates and sort
                self.df.drop_duplicates(subset=['timestamp'], keep='last', inplace=True)
                self.df.sort_values('timestamp', inplace=True)
                
                # Keep only last 1000 candles to manage memory
                if len(self.df) > 1000:
                    self.df = self.df.tail(1000).reset_index(drop=True)
            
            # Trigger callback if set
            if self.on_data_callback:
                self.on_data_callback(candle)
                
        except Exception as e:
            self.logger.error(f"Error processing candle data: {e}")
    
    def _on_open(self, ws):
        """Handle WebSocket connection opened"""
        self.logger.info("WebSocket connection opened")
        self.is_connected = True
        self.reconnect_count = 0
        
        # Subscribe to candles
        self._subscribe_to_candles()
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        self.logger.error(f"WebSocket error: {error}")
        self.is_connected = False
        
        if self.on_error_callback:
            self.on_error_callback(error)
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection closed"""
        self.logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.is_connected = False
        
        # Attempt reconnection if needed
        if self.should_reconnect and self.reconnect_count < self.max_reconnects:
            self._reconnect()
    
    def _subscribe_to_candles(self):
        """Subscribe to candle data"""
        subscription = {
            "type": "subscribe",
            "payload": {
                "channels": [
                    {
                        "name": "v2/candles",
                        "symbols": [self.symbol],
                        "interval": self.interval
                    }
                ]
            }
        }
        
        try:
            self.ws.send(json.dumps(subscription))
            self.logger.info(f"Subscribed to {self.symbol} candles")
        except Exception as e:
            self.logger.error(f"Failed to subscribe: {e}")
    
    def _reconnect(self):
        """Attempt to reconnect WebSocket"""
        self.reconnect_count += 1
        wait_time = min(2 ** self.reconnect_count, 60)  # Exponential backoff
        
        self.logger.info(f"Reconnecting in {wait_time} seconds... (attempt {self.reconnect_count})")
        time.sleep(wait_time)
        
        try:
            self.start()
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")
    
    def start(self):
        """Start WebSocket connection"""
        if self.ws and self.is_connected:
            self.logger.warning("WebSocket already connected")
            return
        
        try:
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=self._on_message,
                on_open=self._on_open,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Start in a separate thread
            ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            ws_thread.start()
            
            # Wait for connection
            for _ in range(50):  # Wait up to 5 seconds
                if self.is_connected:
                    break
                time.sleep(0.1)
            
            if not self.is_connected:
                raise WebSocketError("Failed to establish WebSocket connection")
                
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket: {e}")
            raise
    
    def stop(self):
        """Stop WebSocket connection"""
        self.should_reconnect = False
        self.is_connected = False
        
        if self.ws:
            self.ws.close()
            self.ws = None
        
        self.logger.info("WebSocket connection stopped")
    
    def get_latest_data(self, n: int = 100) -> pd.DataFrame:
        """Get latest n candles"""
        with self.lock:
            if len(self.df) == 0:
                return pd.DataFrame()
            return self.df.tail(n).copy()
    
    def get_latest_candle(self) -> Optional[Dict]:
        """Get the most recent candle"""
        with self.lock:
            if len(self.df) == 0:
                return None
            return self.df.iloc[-1].to_dict()
    
    def is_healthy(self) -> bool:
        """Check if WebSocket connection is healthy"""
        return self.is_connected and self.ws is not None