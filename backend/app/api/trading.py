from fastapi import APIRouter, HTTPException, status, Query, Depends
from pydantic import BaseModel, field_validator
from app.db import database
from app.api.auth import get_user_delta_client, get_current_user_id
from typing import Optional, List
from decimal import Decimal
import json
import re
import asyncio
import time
import random

router = APIRouter(prefix="/api/trading", tags=["trading"])


class TradeRequest(BaseModel):
    symbol: str
    side: str
    quantity: Decimal
    price: Optional[Decimal] = None
    order_type: str = "limit_order"
    time_in_force: Optional[str] = "gtc"  # gtc or ioc
    post_only: Optional[bool] = False
    reduce_only: Optional[bool] = False
    client_order_id: Optional[str] = None
    stop_price: Optional[Decimal] = None
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Symbol must be at least 1 character')
        return v.strip()
    
    @field_validator('side')
    @classmethod
    def validate_side(cls, v):
        if v not in ['buy', 'sell']:
            raise ValueError('Side must be buy or sell')
        return v
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Price must be greater than 0')
        return v


class CancelOrderRequest(BaseModel):
    order_id: str
    product_id: int


class TradeResponse(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: str
    price: str
    timestamp: str
    delta_order_id: Optional[str] = None
    status: str


@router.post("/trade", response_model=TradeResponse)
async def place_trade(trade: TradeRequest, user_id: int = Depends(get_current_user_id)):
    """Place a trade through Delta Exchange"""
    try:
        # Get Delta Exchange client
        client = get_user_delta_client(user_id)
        
        # Prepare parameters for the order
        order_params = {
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": str(trade.quantity),
            "order_type": trade.order_type
        }
        
        # Add optional parameters if they're provided
        if trade.price is not None:
            order_params["price"] = str(trade.price)
            
        if trade.time_in_force:
            order_params["time_in_force"] = trade.time_in_force
            
        if trade.post_only is not None:
            order_params["post_only"] = trade.post_only
            
        if trade.reduce_only is not None:
            order_params["reduce_only"] = trade.reduce_only
            
        if trade.client_order_id:
            order_params["client_order_id"] = trade.client_order_id
            
        if trade.stop_price:
            order_params["stop_price"] = str(trade.stop_price)
        
        # Place order on Delta Exchange
        order_result = client.place_order_sync(**order_params)
        
        # Check if order was successful
        if not order_result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order failed: {order_result.get('error', {}).get('message', 'Unknown error')}"
            )
        
        delta_order_id = order_result.get('result', {}).get('id')
        order_status = order_result.get('result', {}).get('state', 'pending')
        
        # Store trade in local database
        query = """
            INSERT INTO trades (symbol, side, quantity, price, delta_order_id, status)
            VALUES (:symbol, :side, :quantity, :price, :delta_order_id, :status)
            RETURNING id, symbol, side, quantity, price, timestamp, delta_order_id, status
        """
        
        values = {
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": trade.quantity,
            "price": trade.price,
            "delta_order_id": str(delta_order_id) if delta_order_id else None,
            "status": order_status
        }
        
        row = await database.fetch_one(query, values)
        
        return TradeResponse(
            id=row['id'],
            symbol=row['symbol'],
            side=row['side'],
            quantity=str(row['quantity']),
            price=str(row['price']),
            timestamp=str(row['timestamp']),
            delta_order_id=row['delta_order_id'],
            status=row['status']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trade execution failed: {str(e)}"
        )


@router.get("/orders")
async def get_trading_orders(user_id: int = Depends(get_current_user_id)):
    """Get all local trading orders"""
    try:
        query = """
            SELECT id, symbol, side, quantity, price, timestamp, delta_order_id, status
            FROM trades
            ORDER BY timestamp DESC
            LIMIT 100
        """
        
        rows = await database.fetch_all(query)
        
        return [
            {
                "id": row['id'],
                "symbol": row['symbol'],
                "side": row['side'],
                "quantity": str(row['quantity']),
                "price": str(row['price']),
                "timestamp": str(row['timestamp']),
                "delta_order_id": row['delta_order_id'],
                "status": row['status']
            }
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get orders: {str(e)}"
        )


@router.get("/orders/{order_id}")
async def get_order_details(order_id: int, user_id: int = Depends(get_current_user_id)):
    """Get details of a specific order"""
    try:
        query = """
            SELECT id, symbol, side, quantity, price, timestamp, delta_order_id, status
            FROM trades
            WHERE id = :order_id
        """
        
        row = await database.fetch_one(query, {"order_id": order_id})
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return {
            "id": row['id'],
            "symbol": row['symbol'],
            "side": row['side'],
            "quantity": str(row['quantity']),
            "price": str(row['price']),
            "timestamp": str(row['timestamp']),
            "delta_order_id": row['delta_order_id'],
            "status": row['status']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order details: {str(e)}"
        )


@router.get("/live-orders")
async def get_live_orders(user_id: int = Depends(get_current_user_id)):
    """Get live orders from Delta Exchange"""
    try:
        client = get_user_delta_client(user_id)
        
        # Get active orders from Delta Exchange
        orders_result = client.get_orders_sync(states="open,pending")
        
        if not orders_result.get('success'):
            # Check if it's a permission error
            error_message = orders_result.get('error', {}).get('message', 'Unknown error')
            if 'unauthorized' in error_message.lower() or 'invalid_api_key' in error_message.lower():
                return {
                    "success": False,
                    "error": "API key does not have trading permissions. Please check your Delta Exchange API key settings.",
                    "result": []
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to get live orders: {error_message}"
                )
        
        orders = orders_result.get('result', [])
        
        return {
            "success": True,
            "result": [
                {
                    "id": order.get('id'),
                    "product_id": order.get('product_id'),
                    "product_symbol": order.get('product_symbol'),
                    "side": order.get('side'),
                    "size": order.get('size'),
                    "unfilled_size": order.get('unfilled_size'),
                    "order_type": order.get('order_type'),
                    "limit_price": order.get('limit_price'),
                    "state": order.get('state'),
                    "created_at": order.get('created_at'),
                    "client_order_id": order.get('client_order_id')
                }
                for order in orders
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get live orders: {str(e)}"
        )


@router.post("/orders/cancel")
async def cancel_order(cancel_request: CancelOrderRequest, user_id: int = Depends(get_current_user_id)):
    """Cancel an order on Delta Exchange"""
    try:
        client = get_user_delta_client(user_id)
        
        # Cancel order on Delta Exchange
        cancel_result = client.cancel_order_sync(cancel_request.order_id, cancel_request.product_id)
        
        if not cancel_result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to cancel order: {cancel_result.get('error', {}).get('message', 'Unknown error')}"
            )
        
        # Update local database
        query = """
            UPDATE trades 
            SET status = 'cancelled' 
            WHERE delta_order_id = :order_id
        """
        
        await database.execute(query, {"order_id": cancel_request.order_id})
        
        return {
            "success": True,
            "message": f"Order {cancel_request.order_id} cancelled successfully",
            "result": cancel_result.get('result')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel order: {str(e)}"
        )


@router.get("/positions")
async def get_positions(product_id: Optional[int] = None, user_id: int = Depends(get_current_user_id)):
    """Get positions from Delta Exchange"""
    try:
        client = get_user_delta_client(user_id)
        
        # Get positions from Delta Exchange
        positions_result = client.get_positions_sync(product_id)
        
        if not positions_result.get('success'):
            # Check if it's a permission error
            error_message = positions_result.get('error', {}).get('message', 'Unknown error')
            if 'unauthorized' in error_message.lower() or 'invalid_api_key' in error_message.lower():
                return {
                    "success": False,
                    "error": "API key does not have trading permissions. Please check your Delta Exchange API key settings.",
                    "result": []
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to get positions: {error_message}"
                )
        
        positions = positions_result.get('result', [])
        
        # If single product_id requested, return single position
        if product_id and not isinstance(positions, list):
            return {
                "success": True,
                "result": {
                    "product_id": product_id,
                    "size": positions.get('size', 0),
                    "entry_price": positions.get('entry_price'),
                    "margin": positions.get('margin'),
                    "liquidation_price": positions.get('liquidation_price'),
                    "bankruptcy_price": positions.get('bankruptcy_price')
                }
            }
        
        # Return all positions
        return {
            "success": True,
            "result": [
                {
                    "user_id": pos.get('user_id'),
                    "product_id": pos.get('product_id'),
                    "product_symbol": pos.get('product_symbol'),
                    "size": pos.get('size'),
                    "entry_price": pos.get('entry_price'),
                    "margin": pos.get('margin'),
                    "liquidation_price": pos.get('liquidation_price'),
                    "bankruptcy_price": pos.get('bankruptcy_price'),
                    "realized_pnl": pos.get('realized_pnl'),
                    "realized_funding": pos.get('realized_funding')
                }
                for pos in positions
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get positions: {str(e)}"
        )


@router.get("/fills")
async def get_fills(product_ids: Optional[str] = None, 
                   start_time: Optional[int] = None,
                   end_time: Optional[int] = None,
                   page_size: int = 50,
                   user_id: int = Depends(get_current_user_id)):
    """Get fills/trade history from Delta Exchange"""
    try:
        client = get_user_delta_client(user_id)
        
        # Get fills from Delta Exchange
        fills_result = client.get_fills_sync(product_ids, start_time, end_time, page_size)
        
        if not fills_result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get fills: {fills_result.get('error', {}).get('message', 'Unknown error')}"
            )
        
        fills = fills_result.get('result', [])
        
        return {
            "success": True,
            "result": [
                {
                    "id": fill.get('id'),
                    "product_id": fill.get('product_id'),
                    "product_symbol": fill.get('product_symbol'),
                    "order_id": fill.get('order_id'),
                    "side": fill.get('side'),
                    "size": fill.get('size'),
                    "price": fill.get('price'),
                    "role": fill.get('role'),
                    "commission": fill.get('commission'),
                    "created_at": fill.get('created_at'),
                    "fill_type": fill.get('fill_type'),
                    "settling_asset_symbol": fill.get('settling_asset_symbol')
                }
                for fill in fills
            ],
            "meta": fills_result.get('meta', {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fills: {str(e)}"
        )


@router.post("/sync-orders")
async def sync_orders(user_id: int = Depends(get_current_user_id)):
    """Sync local orders with Delta Exchange status"""
    try:
        client = get_user_delta_client(user_id)
        
        # Get all orders with delta_order_id that are not closed/cancelled
        query = """
            SELECT id, delta_order_id, symbol, status
            FROM trades
            WHERE delta_order_id IS NOT NULL 
            AND status NOT IN ('closed', 'cancelled')
            ORDER BY timestamp DESC
            LIMIT 50
        """
        
        local_orders = await database.fetch_all(query)
        
        updated_orders = []
        
        for order in local_orders:
            if order['delta_order_id']:
                # Get order status from Delta Exchange
                order_result = client.get_order_by_id_sync(order['delta_order_id'])
                
                if order_result.get('success'):
                    delta_order = order_result.get('result', {})
                    new_status = delta_order.get('state', order['status'])
                    
                    # Update local database if status changed
                    if new_status != order['status']:
                        update_query = """
                            UPDATE trades 
                            SET status = :new_status
                            WHERE id = :order_id
                        """
                        
                        await database.execute(update_query, {
                            "new_status": new_status,
                            "order_id": order['id']
                        })
                        
                        updated_orders.append({
                            "local_id": order['id'],
                            "delta_order_id": order['delta_order_id'],
                            "symbol": order['symbol'],
                            "old_status": order['status'],
                            "new_status": new_status
                        })
        
        return {
            "success": True,
            "message": f"Synced {len(updated_orders)} orders",
            "updated_orders": updated_orders
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync orders: {str(e)}"
        )


@router.post("/demo-trade")
async def demo_trade(trade: TradeRequest, user_id: int = Depends(get_current_user_id)):
    """Demo trade endpoint - simulates order placement without hitting real API"""
    try:
        # Simulate order processing delay
        await asyncio.sleep(0.5)
        
        # Generate fake order ID
        fake_order_id = random.randint(10000, 99999)
        
        # Store demo trade in local database
        query = """
            INSERT INTO trades (symbol, side, quantity, price, delta_order_id, status)
            VALUES (:symbol, :side, :quantity, :price, :delta_order_id, :status)
            RETURNING id, symbol, side, quantity, price, timestamp, delta_order_id, status
        """
        
        values = {
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": trade.quantity,
            "price": trade.price,
            "delta_order_id": f"DEMO_{fake_order_id}",
            "status": "demo_filled"
        }
        
        row = await database.fetch_one(query, values)
        
        return TradeResponse(
            id=row['id'],
            symbol=row['symbol'],
            side=row['side'],
            quantity=str(row['quantity']),
            price=str(row['price']),
            timestamp=str(row['timestamp']),
            delta_order_id=row['delta_order_id'],
            status=row['status']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo trade failed: {str(e)}"
        )


@router.get("/demo-orders")
async def get_demo_orders(user_id: int = Depends(get_current_user_id)):
    """Get demo orders for testing"""
    try:
        # Generate some fake live orders for demo
        demo_orders = []
        products = ["BTCUSD", "ETHUSD", "ADAUSD"]
        
        for i in range(3):
            demo_orders.append({
                "id": f"DEMO_{10000 + i}",
                "product_id": 27 + i,
                "product_symbol": products[i],
                "side": random.choice(["buy", "sell"]),
                "size": random.randint(1, 10),
                "unfilled_size": random.randint(0, 5),
                "order_type": "limit_order",
                "limit_price": str(random.randint(20000, 70000)),
                "state": random.choice(["open", "pending"]),
                "created_at": int(time.time() * 1000000),
                "client_order_id": f"demo_{i}"
            })
        
        return {
            "success": True,
            "result": demo_orders
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get demo orders: {str(e)}"
        )


@router.get("/demo-positions") 
async def get_demo_positions(user_id: int = Depends(get_current_user_id)):
    """Get demo positions for testing"""
    try:
        # Generate some fake positions for demo
        demo_positions = []
        products = ["BTCUSD", "ETHUSD", "ADAUSD"]
        
        for i in range(2):
            pnl = random.uniform(-1000, 1000)
            demo_positions.append({
                "user_id": 12345,
                "product_id": 27 + i,
                "product_symbol": products[i],
                "size": random.randint(-10, 10),
                "entry_price": str(random.randint(20000, 70000)),
                "margin": str(random.randint(100, 1000)),
                "liquidation_price": str(random.randint(15000, 75000)),
                "bankruptcy_price": str(random.randint(10000, 80000)),
                "realized_pnl": str(round(pnl, 2)),
                "realized_funding": str(round(random.uniform(-50, 50), 2))
            })
        
        return {
            "success": True,
            "result": demo_positions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get demo positions: {str(e)}"
        )


# Products API endpoints
@router.get("/products")
async def get_products(
    contract_types: Optional[str] = Query(None, description="Comma separated list of contract types"),
    states: Optional[str] = Query(None, description="Comma separated list of states"),
    after: Optional[str] = Query(None, description="After cursor for pagination"),
    before: Optional[str] = Query(None, description="Before cursor for pagination"),
    page_size: int = Query(100, description="Size of a single page"),
    user_id: int = Depends(get_current_user_id)
):
    """Get list of available products/instruments"""
    try:
        client = get_user_delta_client(user_id)
        
        # Get products from Delta Exchange
        products_result = client.get_products_sync(
            contract_types=contract_types,
            states=states,
            after=after,
            before=before,
            page_size=page_size
        )
        
        if not products_result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get products: {products_result.get('error', {}).get('message', 'Unknown error')}"
            )
        
        return products_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get products: {str(e)}"
        )


@router.get("/products/{symbol}")
async def get_product_by_symbol(symbol: str, user_id: int = Depends(get_current_user_id)):
    """Get details of a specific product by symbol"""
    try:
        client = get_user_delta_client(user_id)
        
        # Get product from Delta Exchange
        product_result = client.get_product_by_symbol_sync(symbol)
        
        if not product_result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product not found: {product_result.get('error', {}).get('message', 'Unknown error')}"
            )
        
        return product_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get product: {str(e)}"
        )


@router.get("/tickers")
async def get_tickers(
    contract_types: Optional[str] = Query(None, description="Comma separated list of contract types"),
    underlying_asset_symbols: Optional[str] = Query(None, description="Comma separated list of underlying asset symbols"),
    expiry_date: Optional[str] = Query(None, description="Expiry date in DD-MM-YYYY format"),
    user_id: int = Depends(get_current_user_id)
):
    """Get tickers for products"""
    try:
        client = get_user_delta_client(user_id)
        
        # Get tickers from Delta Exchange
        tickers_result = client.get_tickers_sync(
            contract_types=contract_types,
            underlying_asset_symbols=underlying_asset_symbols,
            expiry_date=expiry_date
        )
        
        if not tickers_result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get tickers: {tickers_result.get('error', {}).get('message', 'Unknown error')}"
            )
        
        return tickers_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tickers: {str(e)}"
        )


@router.get("/tickers/{symbol}")
async def get_ticker_by_symbol(symbol: str, user_id: int = Depends(get_current_user_id)):
    """Get ticker for a specific product by symbol"""
    try:
        client = get_user_delta_client(user_id)
        
        # Get ticker from Delta Exchange
        ticker_result = client.get_ticker_by_symbol_sync(symbol)
        
        if not ticker_result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticker not found: {ticker_result.get('error', {}).get('message', 'Unknown error')}"
            )
        
        return ticker_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ticker: {str(e)}"
        )


@router.get("/option-chain")
async def get_option_chain(
    underlying_asset_symbols: str = Query(..., description="Underlying asset symbol (e.g., BTC, ETH)"),
    expiry_date: str = Query(..., description="Expiry date in DD-MM-YYYY format"),
    user_id: int = Depends(get_current_user_id)
):
    """Get option chain data for given underlying asset and expiry date"""
    try:
        client = get_user_delta_client(user_id)
        
        # Get option chain from Delta Exchange
        option_chain_result = client.get_option_chain_sync(
            underlying_asset_symbols=underlying_asset_symbols,
            expiry_date=expiry_date
        )
        
        if not option_chain_result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get option chain: {option_chain_result.get('error', {}).get('message', 'Unknown error')}"
            )
        
        return option_chain_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get option chain: {str(e)}"
        )


@router.get("/demo-products")
async def get_demo_products(user_id: int = Depends(get_current_user_id)):
    """Get demo products for testing"""
    try:
        # Generate some fake products for demo
        demo_products = [
            {
                "id": 27,
                "symbol": "BTCUSD",
                "description": "Bitcoin Perpetual futures, quoted, settled & margined in USD",
                "contract_type": "perpetual_futures",
                "state": "live",
                "trading_status": "operational",
                "tick_size": "0.5",
                "contract_value": "0.001",
                "initial_margin": "0.5",
                "maintenance_margin": "0.25",
                "taker_commission_rate": "0.0005",
                "maker_commission_rate": "0.0002",
                "underlying_asset": {"symbol": "BTC"},
                "quoting_asset": {"symbol": "USD"},
                "settling_asset": {"symbol": "USD"}
            },
            {
                "id": 28,
                "symbol": "ETHUSD",
                "description": "Ethereum Perpetual futures, quoted, settled & margined in USD",
                "contract_type": "perpetual_futures",
                "state": "live",
                "trading_status": "operational",
                "tick_size": "0.1",
                "contract_value": "0.01",
                "initial_margin": "0.5",
                "maintenance_margin": "0.25",
                "taker_commission_rate": "0.0005",
                "maker_commission_rate": "0.0002",
                "underlying_asset": {"symbol": "ETH"},
                "quoting_asset": {"symbol": "USD"},
                "settling_asset": {"symbol": "USD"}
            },
            {
                "id": 29,
                "symbol": "ADAUSD",
                "description": "Cardano Perpetual futures, quoted, settled & margined in USD",
                "contract_type": "perpetual_futures",
                "state": "live",
                "trading_status": "operational",
                "tick_size": "0.0001",
                "contract_value": "1.0",
                "initial_margin": "0.5",
                "maintenance_margin": "0.25",
                "taker_commission_rate": "0.0005",
                "maker_commission_rate": "0.0002",
                "underlying_asset": {"symbol": "ADA"},
                "quoting_asset": {"symbol": "USD"},
                "settling_asset": {"symbol": "USD"}
            }
        ]
        
        return {
            "success": True,
            "result": demo_products
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get demo products: {str(e)}"
        )


@router.get("/demo-tickers")
async def get_demo_tickers(user_id: int = Depends(get_current_user_id)):
    """Get demo tickers for testing"""
    try:
        # Generate some fake tickers for demo
        demo_tickers = [
            {
                "symbol": "BTCUSD",
                "product_id": 27,
                "close": 67321.5,
                "high": 68500.5,
                "low": 66300.25,
                "open": 67000.0,
                "mark_price": "67000.00",
                "volume": 25000,
                "turnover": 5000000,
                "turnover_symbol": "USD",
                "oi": "15000",
                "timestamp": int(time.time())
            },
            {
                "symbol": "ETHUSD",
                "product_id": 28,
                "close": 2845.75,
                "high": 2890.0,
                "low": 2800.0,
                "open": 2850.0,
                "mark_price": "2845.00",
                "volume": 45000,
                "turnover": 2500000,
                "turnover_symbol": "USD",
                "oi": "8500",
                "timestamp": int(time.time())
            },
            {
                "symbol": "ADAUSD",
                "product_id": 29,
                "close": 0.8945,
                "high": 0.9100,
                "low": 0.8800,
                "open": 0.8950,
                "mark_price": "0.8945",
                "volume": 150000,
                "turnover": 134000,
                "turnover_symbol": "USD",
                "oi": "25000",
                "timestamp": int(time.time())
            }
        ]
        
        return {
            "success": True,
            "result": demo_tickers
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get demo tickers: {str(e)}"
        )
