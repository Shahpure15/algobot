from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from app.api.auth import get_delta_client
from app.db import database
from typing import Dict, Any, List, Optional
from decimal import Decimal

router = APIRouter(prefix="/api/account", tags=["account"])


class Balance(BaseModel):
    asset: str
    available: str
    locked: str
    total: str


class AccountInfo(BaseModel):
    balances: List[Balance]
    total_balance_usd: Optional[str] = None


@router.get("/balance", response_model=AccountInfo)
async def get_account_balance():
    """Get account balance from Delta Exchange"""
    try:
        client = get_delta_client()
        balance_data = await client.get_balance()
        
        # Process balance data
        balances = []
        if balance_data.get('success') and balance_data.get('result'):
            for balance in balance_data['result']:
                if float(balance.get('balance', 0)) > 0:
                    balances.append(Balance(
                        asset=balance.get('asset', ''),
                        available=str(balance.get('available_balance', 0)),
                        locked=str(balance.get('order_margin', 0)),
                        total=str(balance.get('balance', 0))
                    ))
        
        return AccountInfo(balances=balances)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get balance: {str(e)}"
        )


@router.get("/products")
async def get_products():
    """Get available trading products/symbols"""
    try:
        client = get_delta_client()
        products_data = await client.get_products()
        
        # Process products data
        products = []
        if products_data.get('success') and products_data.get('result'):
            for product in products_data['result']:
                products.append({
                    'id': product.get('id'),
                    'symbol': product.get('symbol'),
                    'name': product.get('name'),
                    'precision': product.get('precision'),
                    'minimum_precision': product.get('minimum_precision')
                })
        
        return {"products": products}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get products: {str(e)}"
        )


@router.get("/orders")
async def get_order_history():
    """Get order history from Delta Exchange"""
    try:
        client = get_delta_client()
        orders_data = await client.get_orders()
        
        orders = []
        if orders_data.get('success') and orders_data.get('result'):
            for order in orders_data['result']:
                orders.append({
                    'id': order.get('id'),
                    'product_id': order.get('product_id'),
                    'side': order.get('side'),
                    'size': order.get('size'),
                    'price': order.get('price'),
                    'state': order.get('state'),
                    'order_type': order.get('order_type'),
                    'created_at': order.get('created_at'),
                    'updated_at': order.get('updated_at')
                })
        
        return {"orders": orders}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order history: {str(e)}"
        )


@router.get("/wallet/transactions")
async def get_wallet_transactions(
    asset_ids: Optional[str] = Query(None, description="Comma-separated asset IDs"),
    start_time: Optional[int] = Query(None, description="Start time in microseconds"),
    end_time: Optional[int] = Query(None, description="End time in microseconds"),
    page_size: int = Query(50, description="Number of transactions per page")
):
    """Get wallet transaction history from Delta Exchange"""
    try:
        client = get_delta_client()
        
        # Parse asset_ids if provided
        asset_ids_list = None
        if asset_ids:
            asset_ids_list = [int(id.strip()) for id in asset_ids.split(",") if id.strip()]
        
        # Get wallet transactions
        transactions_data = await client.get_wallet_transactions(
            asset_ids=asset_ids_list,
            start_time=start_time,
            end_time=end_time,
            page_size=page_size
        )
        
        if not transactions_data.get('success', False):
            return {
                "transactions": [],
                "error": transactions_data.get('error', {}).get('message', 'Unknown error'),
                "meta": {}
            }
        
        transactions = []
        for txn in transactions_data.get('result', []):
            transactions.append({
                'id': txn.get('id'),
                'amount': txn.get('amount'),
                'balance': txn.get('balance'),
                'transaction_type': txn.get('transaction_type'),
                'asset_id': txn.get('asset_id'),
                'asset_symbol': txn.get('asset_symbol'),
                'product_id': txn.get('product_id'),
                'created_at': txn.get('created_at'),
                'meta_data': txn.get('meta_data', {})
            })
        
        return {
            "transactions": transactions,
            "meta": transactions_data.get('meta', {}),
            "error": None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wallet transactions: {str(e)}"
        )
