from fastapi import APIRouter, status
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from app.db import database


router = APIRouter(prefix="/api")

class TradeIn(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    side: str = Field(..., description="Trade side (buy or sell)")
    quantity: Decimal = Field(..., gt=0, description="Trade quantity")
    price: Decimal = Field(..., gt=0, description="Trade price")

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        return v.strip().upper()

    @field_validator('side')
    @classmethod
    def validate_side(cls, v):
        side = v.strip().lower()
        if side not in ['buy', 'sell']:
            raise ValueError("Side must be 'buy' or 'sell'")
        return side

@router.post("/trade", status_code=status.HTTP_201_CREATED)
async def place_trade(trade: TradeIn):
    query = """
        INSERT INTO trades (symbol, side, quantity, price)
        VALUES (:symbol, :side, :quantity, :price)
        RETURNING id, symbol, side, quantity, price, timestamp
    """
    values = trade.dict()
    row = await database.fetch_one(query, values)
    return row