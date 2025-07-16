from fastapi import APIRouter
from app.core.database import database

router = APIRouter()

@router.get("/history")
async def get_history():
    rows = await database.fetch_all(
        "SELECT id, symbol, side, quantity, price, timestamp FROM trades ORDER BY timestamp DESC LIMIT 50"
    )
    return [dict(row) for row in rows]