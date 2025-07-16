from fastapi import FastAPI
from app.db import database
from app.api import history, trading

app = FastAPI()

# Include API routers
app.include_router(trading.router)
app.include_router(history.router)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()