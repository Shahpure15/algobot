from fastapi import FastAPI
from databases import Database
from app.db import database
from app.api import history, trading
DATABASE_URL = "postgresql+asyncpg://trader:secret@db:5432/trading"
database = Database(DATABASE_URL)

app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()