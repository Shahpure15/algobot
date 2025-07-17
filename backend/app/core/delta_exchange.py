from delta_rest_client import DeltaRestClient
import asyncio
import logging
import json
import concurrent.futures
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class DeltaExchangeConfig(BaseModel):
    api_key: str = ""
    api_secret: str = ""
    base_url: str = "https://api.delta.exchange"

class DeltaExchangeClient:
    def __init__(self, config: DeltaExchangeConfig):
        self.config = config
        self.client = DeltaRestClient(
            base_url=config.base_url,
            api_key=config.api_key,
            api_secret=config.api_secret
        )
        self.is_connected = False
        self.has_wallet_permissions = False

    def _run_sync(self, coro):
        """Helper to run async methods synchronously"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # concurrent.futures already imported at the top
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            # Try to get products to test connection
            response = await self.get_products()
            if isinstance(response, dict) and response.get('success', False):
                self.is_connected = True
                logger.info("Successfully connected to Delta Exchange")
                
                try:
                    await self._test_wallet_permissions()
                except Exception as e:
                    logger.warning(f"Wallet permissions test failed: {e}")
                    self.has_wallet_permissions = False
                
                return True
            else:
                logger.error(f"Failed to connect to Delta Exchange: {response}")
                return False
        except Exception as e:
            logger.error(f"Error testing Delta Exchange connection: {e}")
            return False

    async def _test_wallet_permissions(self):
        """Test if the API key has wallet permissions"""
        try:
            response = await self._get_wallet_balances()
            if response.get('success', False):
                self.has_wallet_permissions = True
                logger.info("API key has wallet permissions")
            else:
                self.has_wallet_permissions = False
                logger.warning("API key does not have wallet permissions")
        except Exception as e:
            self.has_wallet_permissions = False
            logger.warning(f"API key does not have wallet permissions: {e}")

    async def _get_assets_auth(self) -> Dict[str, Any]:
        """Get wallet balance with authentication to test connection"""
        def _sync_get_wallet():
            # Use the request method directly to call the wallet endpoint
            response = self.client.request("GET", "v2/wallet/balances", auth=True)
            
            # Handle response object
            if hasattr(response, 'json'):
                return response.json()
            elif hasattr(response, 'text'):
                import json
                return json.loads(response.text)
            else:
                return response
        return await asyncio.get_event_loop().run_in_executor(None, _sync_get_wallet)

    async def _get_wallet_balances(self) -> Dict[str, Any]:
        """Get user wallet balances - uses direct API call since delta-rest-client might not have this endpoint"""
        def _sync_get_wallet_balances():
            # Use the client's request method directly to call the wallet balances endpoint
            response = self.client.request("GET", "v2/wallet/balances", auth=True)
            
            # Handle response object
            if hasattr(response, 'json'):
                return response.json()
            elif hasattr(response, 'text'):
                return json.loads(response.text)
            else:
                return response
        return await asyncio.get_event_loop().run_in_executor(None, _sync_get_wallet_balances)

    async def get_balance(self, asset_id: str = "5") -> Dict[str, Any]:
        """Get account balance - gets all wallet balances"""
        try:
            if not self.has_wallet_permissions:
                return {
                    'success': False, 
                    'error': {'message': 'API key does not have wallet permissions. Please check your Delta Exchange API key settings.'}
                }
            
            response = await self._get_wallet_balances()
            if response.get('success', False):
                balances = response.get('result', [])
                balance_dict = {}
                
                # Convert the wallet balances to the expected format
                for balance in balances:
                    asset_symbol = balance.get('asset_symbol', 'unknown')
                    balance_dict[asset_symbol] = {
                        'balance': float(balance.get('balance', 0)),
                        'available_balance': float(balance.get('available_balance', 0)),
                        'order_margin': float(balance.get('order_margin', 0)),
                        'position_margin': float(balance.get('position_margin', 0))
                    }
                
                return {'success': True, 'result': balance_dict}
            else:
                return response
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return {'success': False, 'error': {'message': f'Balance unavailable: {str(e)}. API credentials may lack wallet permissions.'}}

    async def get_products(self, contract_types: Optional[str] = None,
                         states: Optional[str] = None,
                         after: Optional[str] = None,
                         before: Optional[str] = None,
                         page_size: int = 100) -> Dict[str, Any]:
        """Get available products/instruments from Delta Exchange"""
        try:
            def _sync_get_products():
                # Build query parameters
                query_params = []
                if contract_types:
                    query_params.append(f"contract_types={contract_types}")
                if states:
                    query_params.append(f"states={states}")
                if after:
                    query_params.append(f"after={after}")
                if before:
                    query_params.append(f"before={before}")
                query_params.append(f"page_size={page_size}")
                
                # Build URL with query parameters
                url = "v2/products"
                if query_params:
                    url += "?" + "&".join(query_params)
                
                response = self.client.request("GET", url, auth=False)
                
                # Handle response object
                if hasattr(response, 'json'):
                    return response.json()
                elif hasattr(response, 'text'):
                    import json
                    return json.loads(response.text)
                else:
                    return response
            
            response = await asyncio.get_event_loop().run_in_executor(None, _sync_get_products)
            
            # Debug: Log the raw response
            logger.info(f"Raw products response: {response}")
            
            if response.get('success', False):
                return response
            else:
                # If response doesn't have success key but has result, it's likely successful
                if 'result' in response:
                    logger.info("Products response has result key - assuming success")
                    return {'success': True, 'result': response['result']}
                # Fallback to assets if products endpoint fails
                return await self._get_assets_fallback()
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return {'success': False, 'error': {'message': str(e)}}

    async def get_product_by_symbol(self, symbol: str) -> Dict[str, Any]:
        """Get specific product by symbol from Delta Exchange"""
        try:
            def _sync_get_product():
                response = self.client.request("GET", f"v2/products/{symbol}", auth=False)
                
                # Handle response object
                if hasattr(response, 'json'):
                    return response.json()
                elif hasattr(response, 'text'):
                    import json
                    return json.loads(response.text)
                else:
                    return response
            
            response = await asyncio.get_event_loop().run_in_executor(None, _sync_get_product)
            return response
        except Exception as e:
            logger.error(f"Error getting product {symbol}: {e}")
            return {'success': False, 'error': {'message': str(e)}}

    async def get_tickers(self, contract_types: Optional[str] = None,
                         underlying_asset_symbols: Optional[str] = None,
                         expiry_date: Optional[str] = None) -> Dict[str, Any]:
        """Get tickers for products from Delta Exchange"""
        try:
            def _sync_get_tickers():
                # Build query parameters
                query_params = []
                if contract_types:
                    query_params.append(f"contract_types={contract_types}")
                if underlying_asset_symbols:
                    query_params.append(f"underlying_asset_symbols={underlying_asset_symbols}")
                if expiry_date:
                    query_params.append(f"expiry_date={expiry_date}")
                
                # Build URL with query parameters
                url = "v2/tickers"
                if query_params:
                    url += "?" + "&".join(query_params)
                
                response = self.client.request("GET", url, auth=False)
                
                # Handle response object
                if hasattr(response, 'json'):
                    return response.json()
                elif hasattr(response, 'text'):
                    import json
                    return json.loads(response.text)
                else:
                    return response
            
            response = await asyncio.get_event_loop().run_in_executor(None, _sync_get_tickers)
            return response
        except Exception as e:
            logger.error(f"Error getting tickers: {e}")
            return {'success': False, 'error': {'message': str(e)}}

    async def get_ticker_by_symbol(self, symbol: str) -> Dict[str, Any]:
        """Get ticker for specific product by symbol from Delta Exchange"""
        try:
            def _sync_get_ticker():
                response = self.client.request("GET", f"v2/tickers/{symbol}", auth=False)
                
                # Handle response object
                if hasattr(response, 'json'):
                    return response.json()
                elif hasattr(response, 'text'):
                    import json
                    return json.loads(response.text)
                else:
                    return response
            
            response = await asyncio.get_event_loop().run_in_executor(None, _sync_get_ticker)
            return response
        except Exception as e:
            logger.error(f"Error getting ticker for {symbol}: {e}")
            return {'success': False, 'error': {'message': str(e)}}

    async def get_option_chain(self, underlying_asset_symbols: str, 
                              expiry_date: str) -> Dict[str, Any]:
        """Get option chain data for given underlying asset and expiry date"""
        try:
            def _sync_get_option_chain():
                query_params = [
                    "contract_types=call_options,put_options",
                    f"underlying_asset_symbols={underlying_asset_symbols}",
                    f"expiry_date={expiry_date}"
                ]
                
                url = "v2/tickers?" + "&".join(query_params)
                response = self.client.request("GET", url, auth=False)
                
                # Handle response object
                if hasattr(response, 'json'):
                    return response.json()
                elif hasattr(response, 'text'):
                    import json
                    return json.loads(response.text)
                else:
                    return response
            
            response = await asyncio.get_event_loop().run_in_executor(None, _sync_get_option_chain)
            return response
        except Exception as e:
            logger.error(f"Error getting option chain: {e}")
            return {'success': False, 'error': {'message': str(e)}}

    async def _get_assets_fallback(self) -> Dict[str, Any]:
        """Fallback method to get products when main endpoint fails"""
        try:
            def _sync_get_products():
                response = self.client.request("GET", "v2/products", auth=False)
                
                # Handle response object
                if hasattr(response, 'json'):
                    return response.json()
                elif hasattr(response, 'text'):
                    import json
                    return json.loads(response.text)
                else:
                    return response
            
            response = await asyncio.get_event_loop().run_in_executor(None, _sync_get_products)
            if isinstance(response, list):
                major_assets = []
                for asset in response:
                    # Show more assets - use sort_priority <= 20 instead of <= 10
                    if asset.get('sort_priority', 100) <= 20:
                        major_assets.append({
                            'id': asset.get('id'),
                            'symbol': asset.get('symbol'),
                            'name': asset.get('name'),
                            'precision': asset.get('precision'),
                            'minimum_precision': asset.get('minimum_precision')
                        })
                
                # If no assets found with the filter, return top 10 assets
                if not major_assets:
                    sorted_assets = sorted(response, key=lambda x: x.get('sort_priority', 100))
                    for asset in sorted_assets[:10]:
                        major_assets.append({
                            'id': asset.get('id'),
                            'symbol': asset.get('symbol'),
                            'name': asset.get('name'),
                            'precision': asset.get('precision'),
                            'minimum_precision': asset.get('minimum_precision')
                        })
                
                return {'success': True, 'result': major_assets}
            elif isinstance(response, dict) and response.get('success', False):
                products = response.get('result', [])
                return {'success': True, 'result': products}
            else:
                return {'success': False, 'error': {'message': 'Unable to get products'}}
        except Exception as e:
            logger.error(f"Error getting assets fallback: {e}")
            return {'success': False, 'error': {'message': str(e)}}

    async def get_wallet_transactions(self, asset_ids: Optional[List[int]] = None, 
                                    start_time: Optional[int] = None, 
                                    end_time: Optional[int] = None,
                                    page_size: int = 50) -> Dict[str, Any]:
        """Get wallet transaction history"""
        try:
            if not self.has_wallet_permissions:
                return {
                    'success': False, 
                    'error': {'message': 'API key does not have wallet permissions. Please check your Delta Exchange API key settings.'}
                }
            
            def _sync_get_wallet_transactions():
                # Build query parameters
                query_params = []
                if asset_ids:
                    query_params.append(f"asset_ids={','.join(map(str, asset_ids))}")
                if start_time:
                    query_params.append(f"start_time={start_time}")
                if end_time:
                    query_params.append(f"end_time={end_time}")
                query_params.append(f"page_size={page_size}")
                
                # Build URL with query parameters
                url = "v2/wallet/transactions"
                if query_params:
                    url += "?" + "&".join(query_params)
                
                return self.client.request("GET", url, auth=True)
            
            response = await asyncio.get_event_loop().run_in_executor(None, _sync_get_wallet_transactions)
            if response.get('success', False):
                transactions = response.get('result', [])
                return {'success': True, 'result': transactions, 'meta': response.get('meta', {})}
            else:
                return response
        except Exception as e:
            logger.error(f"Error getting wallet transactions: {e}")
            return {'success': False, 'error': {'message': str(e)}}

    def test_connection_sync(self) -> bool:
        """Synchronous wrapper for test_connection"""
        return self._run_sync(self.test_connection())

    def get_balance_sync(self, asset_id: str = "5") -> Dict[str, Any]:
        """Synchronous wrapper for get_balance"""
        return self._run_sync(self.get_balance(asset_id))

    def get_products_sync(self, contract_types: Optional[str] = None,
                         states: Optional[str] = None,
                         after: Optional[str] = None,
                         before: Optional[str] = None,
                         page_size: int = 100) -> Dict[str, Any]:
        """Synchronous wrapper for get_products"""
        return self._run_sync(self.get_products(contract_types, states, after, before, page_size))

    def get_product_by_symbol_sync(self, symbol: str) -> Dict[str, Any]:
        """Synchronous wrapper for get_product_by_symbol"""
        return self._run_sync(self.get_product_by_symbol(symbol))

    def get_tickers_sync(self, contract_types: Optional[str] = None,
                        underlying_asset_symbols: Optional[str] = None,
                        expiry_date: Optional[str] = None) -> Dict[str, Any]:
        """Synchronous wrapper for get_tickers"""
        return self._run_sync(self.get_tickers(contract_types, underlying_asset_symbols, expiry_date))

    def get_ticker_by_symbol_sync(self, symbol: str) -> Dict[str, Any]:
        """Synchronous wrapper for get_ticker_by_symbol"""
        return self._run_sync(self.get_ticker_by_symbol(symbol))

    def get_option_chain_sync(self, underlying_asset_symbols: str, expiry_date: str) -> Dict[str, Any]:
        """Synchronous wrapper for get_option_chain"""
        return self._run_sync(self.get_option_chain(underlying_asset_symbols, expiry_date))

    def get_wallet_transactions_sync(self, asset_ids: Optional[List[int]] = None, 
                                   start_time: Optional[int] = None, 
                                   end_time: Optional[int] = None,
                                   page_size: int = 50) -> Dict[str, Any]:
        """Synchronous wrapper for get_wallet_transactions"""
        return self._run_sync(self.get_wallet_transactions(asset_ids, start_time, end_time, page_size))

    async def place_order(self, symbol: str, side: str, quantity: str, 
                         price: Optional[str] = None, order_type: str = "limit_order",
                         time_in_force: str = "gtc", post_only: bool = False,
                         reduce_only: bool = False, client_order_id: Optional[str] = None,
                         stop_price: Optional[str] = None) -> Dict[str, Any]:
        """Place a new order on Delta Exchange"""
        try:
            # Get product ID from symbol
            products = await self.get_products()
            if not products.get('success'):
                return {'success': False, 'error': {'message': 'Failed to get products'}}
            
            product_id = None
            for product in products.get('result', []):
                if product.get('symbol') == symbol:
                    product_id = product.get('id')
                    break
            
            if not product_id:
                return {'success': False, 'error': {'message': f'Product {symbol} not found'}}
            
            def _sync_place_order():
                order_data = {
                    'product_id': product_id,
                    'size': int(float(quantity)),
                    'side': side,
                    'order_type': order_type,
                    'time_in_force': time_in_force,
                    'post_only': post_only,
                    'reduce_only': reduce_only
                }
                
                # Add optional parameters if they're provided
                if price is not None and order_type == "limit_order":
                    order_data['limit_price'] = price
                
                if client_order_id:
                    order_data['client_order_id'] = client_order_id
                    
                if stop_price and (order_type == "stop_loss_order" or order_type == "take_profit_order"):
                    order_data['stop_price'] = stop_price
                
                return self.client.request("POST", "v2/orders", json=order_data, auth=True)
            
            response = await asyncio.get_event_loop().run_in_executor(None, _sync_place_order)
            
            if response.get('success', False):
                return response
            else:
                return {'success': False, 'error': response.get('error', {'message': 'Order placement failed'})}
        
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {'success': False, 'error': {'message': str(e)}}

    async def get_orders(self, product_ids: Optional[str] = None, 
                        states: Optional[str] = None,
                        page_size: int = 50) -> Dict[str, Any]:
        """Get active orders from Delta Exchange"""
        try:
            def _sync_get_orders():
                # Build query parameters
                query_params = []
                if product_ids:
                    query_params.append(f"product_ids={product_ids}")
                if states:
                    query_params.append(f"states={states}")
                query_params.append(f"page_size={page_size}")
                
                # Build URL with query parameters
                url = "v2/orders"
                if query_params:
                    url += "?" + "&".join(query_params)
                
                return self.client.request("GET", url, auth=True)
            
            response = await asyncio.get_event_loop().run_in_executor(None, _sync_get_orders)
            return response
        
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return {'success': False, 'error': {'message': str(e)}}

    async def get_order_by_id(self, order_id: str) -> Dict[str, Any]:
        """Get specific order by ID from Delta Exchange"""
        try:
            def _sync_get_order():
                return self.client.request("GET", f"v2/orders/{order_id}", auth=True)
            
            response = await asyncio.get_event_loop().run_in_executor(None, _sync_get_order)
            return response
        
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return {'success': False, 'error': {'message': str(e)}}

    async def cancel_order(self, order_id: str, product_id: int) -> Dict[str, Any]:
        """Cancel an order on Delta Exchange"""
        try:
            def _sync_cancel_order():
                cancel_data = {
                    'id': int(order_id),
                    'product_id': product_id
                }
                return self.client.request("DELETE", "v2/orders", json=cancel_data, auth=True)
            
            response = await asyncio.get_event_loop().run_in_executor(None, _sync_cancel_order)
            return response
        
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            return {'success': False, 'error': {'message': str(e)}}

    async def get_positions(self, product_id: Optional[int] = None) -> Dict[str, Any]:
        """Get positions from Delta Exchange"""
        try:
            def _sync_get_positions():
                if product_id:
                    url = f"v2/positions?product_id={product_id}"
                    return self.client.request("GET", url, auth=True)
                else:
                    return self.client.request("GET", "v2/positions/margined", auth=True)
            
            response = await asyncio.get_event_loop().run_in_executor(None, _sync_get_positions)
            return response
        
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {'success': False, 'error': {'message': str(e)}}

    async def get_fills(self, product_ids: Optional[str] = None,
                       start_time: Optional[int] = None,
                       end_time: Optional[int] = None,
                       page_size: int = 50) -> Dict[str, Any]:
        """Get fills/trade history from Delta Exchange"""
        try:
            def _sync_get_fills():
                # Build query parameters
                query_params = []
                if product_ids:
                    query_params.append(f"product_ids={product_ids}")
                if start_time:
                    query_params.append(f"start_time={start_time}")
                if end_time:
                    query_params.append(f"end_time={end_time}")
                query_params.append(f"page_size={page_size}")
                
                # Build URL with query parameters
                url = "v2/fills"
                if query_params:
                    url += "?" + "&".join(query_params)
                
                return self.client.request("GET", url, auth=True)
            
            response = await asyncio.get_event_loop().run_in_executor(None, _sync_get_fills)
            return response
        
        except Exception as e:
            logger.error(f"Error getting fills: {e}")
            return {'success': False, 'error': {'message': str(e)}}

    # Synchronous wrappers for trading methods
    def place_order_sync(self, symbol: str, side: str, quantity: str, 
                        price: Optional[str] = None, order_type: str = "limit_order",
                        time_in_force: str = "gtc", post_only: bool = False,
                        reduce_only: bool = False, client_order_id: Optional[str] = None,
                        stop_price: Optional[str] = None) -> Dict[str, Any]:
        """Synchronous wrapper for place_order"""
        return self._run_sync(self.place_order(
            symbol, side, quantity, price, order_type,
            time_in_force, post_only, reduce_only, client_order_id, stop_price
        ))

    def get_orders_sync(self, product_ids: Optional[str] = None, 
                       states: Optional[str] = None,
                       page_size: int = 50) -> Dict[str, Any]:
        """Synchronous wrapper for get_orders"""
        return self._run_sync(self.get_orders(product_ids, states, page_size))

    def get_order_by_id_sync(self, order_id: str) -> Dict[str, Any]:
        """Synchronous wrapper for get_order_by_id"""
        return self._run_sync(self.get_order_by_id(order_id))

    def cancel_order_sync(self, order_id: str, product_id: int) -> Dict[str, Any]:
        """Synchronous wrapper for cancel_order"""
        return self._run_sync(self.cancel_order(order_id, product_id))

    def get_positions_sync(self, product_id: Optional[int] = None) -> Dict[str, Any]:
        """Synchronous wrapper for get_positions"""
        return self._run_sync(self.get_positions(product_id))

    def get_fills_sync(self, product_ids: Optional[str] = None,
                      start_time: Optional[int] = None,
                      end_time: Optional[int] = None,
                      page_size: int = 50) -> Dict[str, Any]:
        """Synchronous wrapper for get_fills"""
        return self._run_sync(self.get_fills(product_ids, start_time, end_time, page_size))
