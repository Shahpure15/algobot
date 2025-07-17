"""
Authentication API endpoints
"""
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, insert, update
from app.core.auth import (
    User, UserCreate, UserLogin, Token, UserResponse,
    hash_password, verify_password, create_access_token, get_current_user
)
from app.core.delta_exchange import DeltaExchangeClient, DeltaExchangeConfig
from app.db import database
from app.utils.api_manager import api_manager

# Ensure the api_manager module is created
# If this is the first time running this code, we'll import a dummy module
try:
    from app.utils.api_manager import api_manager
except ImportError:
    pass

router = APIRouter(prefix="/api/auth", tags=["auth"])


class DeltaCredentials(BaseModel):
    api_key: str
    api_secret: str
    user_id: Optional[int] = None


class ConnectionStatus(BaseModel):
    is_connected: bool
    last_check: Optional[str] = None
    error: Optional[str] = None


# In-memory storage for demo purposes (use proper secret management in production)
_delta_client: Optional[DeltaExchangeClient] = None


@router.post("/connect", response_model=ConnectionStatus)
async def connect_delta_exchange(credentials: DeltaCredentials):
    """Connect to Delta Exchange using API credentials"""
    global _delta_client
    
    try:
        config = DeltaExchangeConfig(
            api_key=credentials.api_key,
            api_secret=credentials.api_secret
        )
        
        # Create client and test connection
        client = DeltaExchangeClient(config)
        is_connected = await client.test_connection()
        
        if is_connected:
            # Store client for future use
            if _delta_client:
                await _delta_client.close()
            _delta_client = client
            
            # Store connection status in database
            await database.execute(
                "INSERT INTO connection_status (provider, is_connected, last_check) VALUES ('delta_exchange', true, NOW()) ON CONFLICT (provider, user_id) WHERE user_id IS NULL DO UPDATE SET is_connected = true, last_check = NOW()"
            )
            
            return ConnectionStatus(is_connected=True, last_check="now")
        else:
            await client.close()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API credentials"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection failed: {str(e)}"
        )


@router.get("/status", response_model=ConnectionStatus)
async def get_connection_status():
    """Get current connection status"""
    global _delta_client
    
    try:
        # Check database for stored status
        row = await database.fetch_one(
            "SELECT is_connected, last_check FROM connection_status WHERE provider = 'delta_exchange' AND user_id IS NULL"
        )
        
        if row and _delta_client:
            # Test current connection
            is_connected = await _delta_client.test_connection()
            
            if is_connected != row['is_connected']:
                # Update status if changed
                await database.execute(
                    "UPDATE connection_status SET is_connected = :is_connected, last_check = NOW() WHERE provider = 'delta_exchange' AND user_id IS NULL",
                    {"is_connected": is_connected}
                )
            
            return ConnectionStatus(
                is_connected=is_connected,
                last_check=str(row['last_check']) if row['last_check'] else None
            )
        else:
            return ConnectionStatus(is_connected=False)
            
    except Exception as e:
        return ConnectionStatus(is_connected=False, error=str(e))


@router.post("/disconnect")
async def disconnect_delta_exchange():
    """Disconnect from Delta Exchange"""
    global _delta_client
    
    try:
        if _delta_client:
            await _delta_client.close()
            _delta_client = None
        
        # Update database
        await database.execute(
            "UPDATE connection_status SET is_connected = false, last_check = NOW() WHERE provider = 'delta_exchange' AND user_id IS NULL"
        )
        
        return {"message": "Disconnected successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Disconnect failed: {str(e)}"
        )


def get_delta_client() -> DeltaExchangeClient:
    """Get the current Delta Exchange client"""
    global _delta_client
    if not _delta_client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not connected to Delta Exchange"
        )
    return _delta_client
