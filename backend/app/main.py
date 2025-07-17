from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import database
from app.core.config import settings
from app.api import history, trading, auth, account, users, profile
from app.core.delta_exchange import DeltaExchangeClient, DeltaExchangeConfig


app = FastAPI(title="Algo Trading Bot", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://154cb416789f.ngrok-free.app",
        # For production, remove the wildcard and specify exact origins
        "*" if settings.environment == "development" else None
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
)

# Include API routers
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(account.router)
app.include_router(trading.router)
app.include_router(history.router)


@app.on_event("startup")
async def startup():
    await database.connect()
    
    # Note: Auto-connection removed - now using user-specific API credentials
    # Each user will connect with their own API keys when they authenticate
    print("✅ Database connected successfully")
    print("🔐 User-specific API authentication system initialized")


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/")
async def root():
    return {"message": "Algo Trading Bot API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}