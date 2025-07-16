from fastapi import APIRouter, status
from pydantic import BaseModel, constr, condecimal
from app.core.database import database
from sqlalchemy import insert

router = APIRouter()

class TradeIn(BaseModel):
    symbol: constr(strip_whitespace=True, min_length=1, max_length=10)
    side: constr(strip_whitespace=True, to_lower=True, pattern="^(buy|sell)$")
    quantity: condecimal(gt=0)
    price: condecimal(gt=0)

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