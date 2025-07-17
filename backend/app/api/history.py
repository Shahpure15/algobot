from fastapi import APIRouter, HTTPException, status
from app.db import database
from typing import List, Dict, Any
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/trades")
async def get_trade_history():
    """Get trade history from local database"""
    try:
        query = """
            SELECT id, symbol, side, quantity, price, timestamp, delta_order_id, status
            FROM trades
            ORDER BY timestamp DESC
            LIMIT 50
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
            detail=f"Failed to get trade history: {str(e)}"
        )


@router.get("/stats")
async def get_trading_stats():
    """Get trading statistics"""
    try:
        # Get total trades
        total_trades_query = "SELECT COUNT(*) as total FROM trades"
        total_trades_row = await database.fetch_one(total_trades_query)
        total_trades = total_trades_row['total'] if total_trades_row else 0
        
        # Get successful trades
        successful_trades_query = "SELECT COUNT(*) as successful FROM trades WHERE status = 'filled'"
        successful_trades_row = await database.fetch_one(successful_trades_query)
        successful_trades = successful_trades_row['successful'] if successful_trades_row else 0
        
        # Get trades by side
        buy_trades_query = "SELECT COUNT(*) as buy_count FROM trades WHERE side = 'buy'"
        buy_trades_row = await database.fetch_one(buy_trades_query)
        buy_trades = buy_trades_row['buy_count'] if buy_trades_row else 0
        
        sell_trades_query = "SELECT COUNT(*) as sell_count FROM trades WHERE side = 'sell'"
        sell_trades_row = await database.fetch_one(sell_trades_query)
        sell_trades = sell_trades_row['sell_count'] if sell_trades_row else 0
        
        # Get recent activity (last 24 hours)
        recent_activity_query = """
            SELECT COUNT(*) as recent
            FROM trades
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
        """
        recent_activity_row = await database.fetch_one(recent_activity_query)
        recent_activity = recent_activity_row['recent'] if recent_activity_row else 0
        
        return {
            "total_trades": total_trades,
            "successful_trades": successful_trades,
            "buy_trades": buy_trades,
            "sell_trades": sell_trades,
            "recent_activity_24h": recent_activity,
            "success_rate": (successful_trades / total_trades * 100) if total_trades > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trading stats: {str(e)}"
        )


@router.get("/chart-data")
async def get_chart_data():
    """Get data for charts and visualizations"""
    try:
        # Get daily trade counts for the last 30 days
        daily_trades_query = """
            SELECT 
                DATE(timestamp) as trade_date,
                COUNT(*) as trade_count,
                SUM(CASE WHEN side = 'buy' THEN 1 ELSE 0 END) as buy_count,
                SUM(CASE WHEN side = 'sell' THEN 1 ELSE 0 END) as sell_count
            FROM trades
            WHERE timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(timestamp)
            ORDER BY trade_date DESC
        """
        
        daily_trades_rows = await database.fetch_all(daily_trades_query)
        
        daily_trades = [
            {
                "date": str(row['trade_date']),
                "total": row['trade_count'],
                "buy": row['buy_count'],
                "sell": row['sell_count']
            }
            for row in daily_trades_rows
        ]
        
        # Get symbol distribution
        symbol_dist_query = """
            SELECT symbol, COUNT(*) as count
            FROM trades
            GROUP BY symbol
            ORDER BY count DESC
            LIMIT 10
        """
        
        symbol_dist_rows = await database.fetch_all(symbol_dist_query)
        
        symbol_distribution = [
            {
                "symbol": row['symbol'],
                "count": row['count']
            }
            for row in symbol_dist_rows
        ]
        
        return {
            "daily_trades": daily_trades,
            "symbol_distribution": symbol_distribution
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chart data: {str(e)}"
        )