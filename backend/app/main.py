from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import database
from app.core.config import settings
from app.api import history, trading, auth, account, users
from app.core.delta_exchange import DeltaExchangeClient, DeltaExchangeConfig


app = FastAPI(title="Algo Trading Bot", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://28f66dfad14b.ngrok-free.app",
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
app.include_router(account.router)
app.include_router(trading.router)
app.include_router(history.router)


@app.on_event("startup")
async def startup():
    await database.connect()
    
    # Auto-connect to Delta Exchange if credentials are provided
    if settings.delta_api_key and settings.delta_api_secret:
        try:
            from app.api.auth import _delta_client
            
            config = DeltaExchangeConfig(
                api_key=settings.delta_api_key,
                api_secret=settings.delta_api_secret,
                base_url=settings.delta_base_url
            )
            
            client = DeltaExchangeClient(config)
            is_connected = await client.test_connection()
            
            if is_connected:
                # Store client globally
                import app.api.auth as auth_module
                auth_module._delta_client = client
                
                # Update database
                await database.execute(
                    "INSERT INTO connection_status (provider, is_connected, last_check) VALUES ('delta_exchange', true, NOW()) ON CONFLICT (provider) DO UPDATE SET is_connected = true, last_check = NOW()"
                )
                print("✅ Auto-connected to Delta Exchange successfully")
            else:
                print("❌ Failed to auto-connect to Delta Exchange - Invalid credentials")
        except Exception as e:
            print(f"❌ Auto-connection to Delta Exchange failed: {str(e)}")


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/")
async def root():
    return {"message": "Algo Trading Bot API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}