# src/exchanges/delta/clients.py
import requests
import json
from typing import Dict, List, Optional, Any
from .auth import DeltaAuthenticator
from src.utils.exceptions import ExchangeError, AuthenticationError
from src.utils.logger import get_logger

class DeltaExchangeClient:
    """Delta Exchange API client with proper authentication"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.base_url = "https://testnet-api.delta.exchange" if testnet else "https://api.delta.exchange"
        self.auth = DeltaAuthenticator(api_key, api_secret)
        self.session = requests.Session()
        self.logger = get_logger(__name__)
        
    def _make_request(self, method: str, endpoint: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Delta Exchange API"""
        url = f"{self.base_url}{endpoint}"
        headers = self.auth.generate_signature(method, endpoint, payload)
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, params=payload)
            else:
                response = self.session.request(
                    method.upper(), 
                    url, 
                    headers=headers, 
                    json=payload
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise AuthenticationError(f"Authentication failed: {e}")
            raise ExchangeError(f"HTTP error {response.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            raise ExchangeError(f"Request failed: {e}")
    
    def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        return self._make_request('GET', '/v2/wallet/balances')
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get open positions"""
        return self._make_request('GET', '/v2/positions')
    
    def place_order(self, symbol: str, side: str, size: float, order_type: str = 'market', 
                   price: Optional[float] = None) -> Dict[str, Any]:
        """Place an order"""
        
        # Get product ID from symbol
        product_id = self._get_product_id(symbol)
        
        payload = {
            'product_id': product_id,
            'side': side.lower(),
            'size': str(size),
            'order_type': order_type.lower()
        }
        
        if price and order_type.lower() == 'limit':
            payload['limit_price'] = str(price)
        
        return self._make_request('POST', '/v2/orders', payload)
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        return self._make_request('DELETE', f'/v2/orders/{order_id}')
    
    def get_products(self) -> List[Dict[str, Any]]:
        """Get available products"""
        return self._make_request('GET', '/v2/products')
    
    def get_historical_data(self, symbol: str, resolution: str = '5m', 
                          start_time: int = None, end_time: int = None) -> List[Dict[str, Any]]:
        """Get historical candle data"""
        params = {
            'symbol': symbol,
            'resolution': resolution
        }
        
        if start_time:
            params['start'] = start_time
        if end_time:
            params['end'] = end_time
            
        return self._make_request('GET', '/v2/history/candles', params)
    
    def _get_product_id(self, symbol: str) -> int:
        """Get product ID for a symbol"""
        products = self.get_products()
        for product in products['result']:
            if product['symbol'] == symbol:
                return product['id']
        raise ValueError(f"Product not found for symbol: {symbol}")
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            result = self.get_account_balance()
            self.logger.info("Delta Exchange connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"Delta Exchange connection test failed: {e}")
            return False
