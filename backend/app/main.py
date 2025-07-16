from fastapi import FastAPI
from app.api.trading import router as trading_router
from app.api.history import router as history_router
from fastapi import FastAPI
from databases import Database

DATABASE_URL = "postgresql+asyncpg://trader:secret@db:5432/trading"
database = Database(DATABASE_URL)

app = FastAPI()
app.include_router(trading_router, prefix= "/api")
app.include_router(history_router, prefix = "/api")
app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
