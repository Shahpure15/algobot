"""
Authentication API endpoints
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, insert, update
from app.core.auth import (
    User, UserCreate, UserLogin, Token, UserResponse,
    hash_password, verify_password, create_access_token
)
from app.core.delta_exchange import DeltaExchangeClient, DeltaExchangeConfig
from app.db import database
import jwt

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory token storage for demo purposes (use Redis in production)
_active_tokens = {}


class CredentialSummary(BaseModel):
    """Credential summary for connect dialog"""
    id: int
    credential_name: str
    provider: str
    is_active: bool
    last_used: Optional[str] = None


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """Get current user ID from token"""
    from app.core.config import settings
    try:
        # Check if token exists in active tokens
        if token not in _active_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        token_data = _active_tokens[token]
        
        # Check if token is expired
        if datetime.utcnow() > token_data["expires"]:
            # Remove expired token
            del _active_tokens[token]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        # Decode and validate JWT
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return int(user_id)
    
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


class DeltaCredentials(BaseModel):
    api_key: str
    api_secret: str


class ConnectionStatus(BaseModel):
    is_connected: bool
    last_check: Optional[str] = None
    error: Optional[str] = None
    has_credentials: bool = False


# User-specific Delta Exchange clients
_user_delta_clients: Dict[int, DeltaExchangeClient] = {}


@router.post("/register", response_model=Token)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await database.fetch_one(
            "SELECT id FROM users WHERE username = :username OR email = :email",
            {"username": user_data.username, "email": user_data.email}
        )
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Insert new user
        result = await database.fetch_one(
            """
            INSERT INTO users (username, email, full_name, hashed_password) 
            VALUES (:username, :email, :full_name, :hashed_password)
            RETURNING id
            """,
            {
                "username": user_data.username,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "hashed_password": hashed_password
            }
        )
        user_id = result["id"]
        
        # Create access token
        token = create_access_token({"sub": str(user_id)})
        
        # Store token with expiration info  
        from app.core.config import settings
        from datetime import timedelta
        expire_time = datetime.utcnow() + timedelta(days=getattr(settings, 'jwt_expiration_days', 30))
        _active_tokens[token] = {
            "user_id": user_id,
            "expires": expire_time,
            "created": datetime.utcnow()
        }
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "username": user_data.username,
                "email": user_data.email,
                "full_name": user_data.full_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user and return access token"""
    try:
        # Get user by username
        user = await database.fetch_one(
            "SELECT id, username, email, full_name, hashed_password FROM users WHERE username = :username",
            {"username": form_data.username}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Update last login
        await database.execute(
            "UPDATE users SET last_login = :last_login WHERE id = :id",
            {"last_login": datetime.utcnow(), "id": user["id"]}
        )
        
        # Create access token
        token = create_access_token({"sub": str(user["id"])})
        
        # Store token with expiration info
        from app.core.config import settings
        from datetime import timedelta
        expire_time = datetime.utcnow() + timedelta(days=getattr(settings, 'jwt_expiration_days', 30))
        _active_tokens[token] = {
            "user_id": user["id"],
            "username": user["username"],
            "expires": expire_time,
            "created": datetime.utcnow()
        }
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to login: {str(e)}"
        )


@router.post("/logout")
async def logout_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/login"))):
    """Logout user and invalidate token"""
    try:
        # Remove token from active tokens
        if token in _active_tokens:
            del _active_tokens[token]
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: int = Depends(get_current_user_id)):
    """Get current user information"""
    try:
        user = await database.fetch_one(
            "SELECT id, username, email, created_at FROM users WHERE id = :user_id",
            {"user_id": user_id}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.get("/saved-credentials", response_model=List[CredentialSummary])
async def get_saved_credentials(user_id: int = Depends(get_current_user_id)):
    """Get saved credentials for connect dialog"""
    try:
        credentials = await database.fetch_all(
            """
            SELECT id, provider, credential_name, is_active, last_used 
            FROM user_credentials 
            WHERE user_id = :user_id AND is_active = TRUE
            ORDER BY last_used DESC NULLS LAST, created_at DESC
            """,
            {"user_id": user_id}
        )
        
        return [CredentialSummary(**cred) for cred in credentials]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get saved credentials: {str(e)}"
        )


@router.post("/connect-with-saved")
async def connect_with_saved_credential(
    credential_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """Connect using a saved credential"""
    try:
        # Get the credential
        credential = await database.fetch_one(
            """
            SELECT api_key, api_secret, provider, credential_name
            FROM user_credentials 
            WHERE id = :credential_id AND user_id = :user_id AND is_active = TRUE
            """,
            {"credential_id": credential_id, "user_id": user_id}
        )
        
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
        
        if credential["provider"] == "delta_exchange":
            config = DeltaExchangeConfig(
                api_key=credential["api_key"],
                api_secret=credential["api_secret"]
            )
            
            # Create client and test connection
            client = DeltaExchangeClient(config)
            is_connected = await client.test_connection()
            
            if is_connected:
                # Store client for this user
                if user_id in _user_delta_clients:
                    old_client = _user_delta_clients[user_id]
                    try:
                        await old_client.close()
                    except:
                        pass
                
                _user_delta_clients[user_id] = client
                
                # Update last_used timestamp
                await database.execute(
                    "UPDATE user_credentials SET last_used = NOW() WHERE id = :credential_id",
                    {"credential_id": credential_id}
                )
                
                # Update connection status in database
                await database.execute(
                    """
                    INSERT INTO connection_status (user_id, provider, is_connected, last_check) 
                    VALUES (:user_id, 'delta_exchange', true, NOW()) 
                    ON CONFLICT (provider, COALESCE(user_id, -1)) 
                    DO UPDATE SET is_connected = true, last_check = NOW()
                    """,
                    {"user_id": user_id}
                )
                
                return ConnectionStatus(
                    is_connected=True,
                    last_check="now",
                    has_credentials=True
                )
            else:
                if hasattr(client, 'close'):
                    await client.close()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Connection failed with saved credentials"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {credential['provider']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection failed: {str(e)}"
        )


@router.post("/connect", response_model=ConnectionStatus)
async def connect_delta_exchange(
    credentials: DeltaCredentials,
    user_id: int = Depends(get_current_user_id)
):
    """Connect to Delta Exchange using API credentials for specific user"""
    try:
        # Check if user already has credentials stored
        existing_creds = await database.fetch_one(
            "SELECT id FROM user_credentials WHERE user_id = :user_id AND provider = 'delta_exchange'",
            {"user_id": user_id}
        )
        
        config = DeltaExchangeConfig(
            api_key=credentials.api_key,
            api_secret=credentials.api_secret
        )
        
        # Create client and test connection
        client = DeltaExchangeClient(config)
        is_connected = await client.test_connection()
        
        if is_connected:
            # Store or update user credentials
            if existing_creds:
                await database.execute(
                    """
                    UPDATE user_credentials 
                    SET api_key = :api_key, api_secret = :api_secret, last_used = NOW()
                    WHERE user_id = :user_id AND provider = 'delta_exchange'
                    """,
                    {
                        "api_key": credentials.api_key,
                        "api_secret": credentials.api_secret,
                        "user_id": user_id
                    }
                )
            else:
                await database.execute(
                    """
                    INSERT INTO user_credentials (user_id, provider, api_key, api_secret, last_used)
                    VALUES (:user_id, 'delta_exchange', :api_key, :api_secret, NOW())
                    """,
                    {
                        "user_id": user_id,
                        "api_key": credentials.api_key,
                        "api_secret": credentials.api_secret
                    }
                )
            
            # Store client for this user
            if user_id in _user_delta_clients:
                old_client = _user_delta_clients[user_id]
                # Close old client if it exists
                try:
                    await old_client.close()
                except:
                    pass
            
            _user_delta_clients[user_id] = client
            
            # Store connection status in database
            await database.execute(
                """
                INSERT INTO connection_status (user_id, provider, is_connected, last_check) 
                VALUES (:user_id, 'delta_exchange', true, NOW()) 
                ON CONFLICT (provider, COALESCE(user_id, -1)) 
                DO UPDATE SET is_connected = true, last_check = NOW()
                """,
                {"user_id": user_id}
            )
            
            return ConnectionStatus(
                is_connected=True, 
                last_check="now",
                has_credentials=True
            )
        else:
            if hasattr(client, 'close'):
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
async def get_connection_status(user_id: int = Depends(get_current_user_id)):
    """Get current connection status for specific user"""
    try:
        # Check if user has stored credentials
        user_creds = await database.fetch_one(
            "SELECT api_key, api_secret FROM user_credentials WHERE user_id = :user_id AND provider = 'delta_exchange' AND is_active = true",
            {"user_id": user_id}
        )
        
        if not user_creds:
            return ConnectionStatus(
                is_connected=False,
                has_credentials=False
            )
        
        # Check database for stored status
        row = await database.fetch_one(
            "SELECT is_connected, last_check FROM connection_status WHERE provider = 'delta_exchange' AND user_id = :user_id",
            {"user_id": user_id}
        )
        
        # Check if we have an active client for this user
        client = _user_delta_clients.get(user_id)
        
        if client and row:
            # Test current connection
            is_connected = await client.test_connection()
            
            if is_connected != row['is_connected']:
                # Update status if changed
                await database.execute(
                    "UPDATE connection_status SET is_connected = :is_connected, last_check = NOW() WHERE provider = 'delta_exchange' AND user_id = :user_id",
                    {"is_connected": is_connected, "user_id": user_id}
                )
            
            return ConnectionStatus(
                is_connected=is_connected,
                last_check=str(row['last_check']) if row['last_check'] else None,
                has_credentials=True
            )
        elif user_creds:
            # User has credentials but no active client - try to reconnect
            try:
                config = DeltaExchangeConfig(
                    api_key=user_creds['api_key'],
                    api_secret=user_creds['api_secret']
                )
                client = DeltaExchangeClient(config)
                is_connected = await client.test_connection()
                
                if is_connected:
                    _user_delta_clients[user_id] = client
                    
                    # Update connection status
                    await database.execute(
                        """
                        INSERT INTO connection_status (user_id, provider, is_connected, last_check) 
                        VALUES (:user_id, 'delta_exchange', true, NOW()) 
                        ON CONFLICT (provider, COALESCE(user_id, -1)) 
                        DO UPDATE SET is_connected = true, last_check = NOW()
                        """,
                        {"user_id": user_id}
                    )
                    
                    return ConnectionStatus(
                        is_connected=True,
                        last_check="now",
                        has_credentials=True
                    )
                else:
                    if hasattr(client, 'close'):
                        await client.close()
                    return ConnectionStatus(
                        is_connected=False,
                        has_credentials=True,
                        error="Connection failed with stored credentials"
                    )
            except Exception as e:
                return ConnectionStatus(
                    is_connected=False,
                    has_credentials=True,
                    error=str(e)
                )
        else:
            return ConnectionStatus(
                is_connected=False,
                has_credentials=True
            )
            
    except Exception as e:
        return ConnectionStatus(
            is_connected=False,
            has_credentials=False,
            error=str(e)
        )


@router.post("/disconnect")
async def disconnect_delta_exchange(user_id: int = Depends(get_current_user_id)):
    """Disconnect from Delta Exchange for specific user"""
    try:
        # Close and remove client for this user
        if user_id in _user_delta_clients:
            client = _user_delta_clients[user_id]
            if hasattr(client, 'close'):
                await client.close()
            del _user_delta_clients[user_id]
        
        # Update database
        await database.execute(
            "UPDATE connection_status SET is_connected = false, last_check = NOW() WHERE provider = 'delta_exchange' AND user_id = :user_id",
            {"user_id": user_id}
        )
        
        return {"message": "Disconnected successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Disconnect failed: {str(e)}"
        )


def get_user_delta_client(user_id: int = Depends(get_current_user_id)) -> DeltaExchangeClient:
    """Get the Delta Exchange client for a specific user"""
    # Check if client already exists in memory
    if user_id in _user_delta_clients:
        return _user_delta_clients[user_id]
    
    # Try to create client from stored credentials
    import asyncio
    
    async def create_client_from_db():
        # Get user credentials from database
        credentials = await database.fetch_one(
            """
            SELECT api_key, api_secret FROM user_credentials 
            WHERE user_id = :user_id AND provider = 'delta_exchange' AND is_active = TRUE
            ORDER BY last_used DESC NULLS LAST
            LIMIT 1
            """,
            {"user_id": user_id}
        )
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No Delta Exchange credentials found. Please connect first."
            )
        
        # Create client with stored credentials
        config = DeltaExchangeConfig(
            api_key=credentials.api_key,
            api_secret=credentials.api_secret
        )
        
        client = DeltaExchangeClient(config)
        
        # Test connection
        is_connected = await client.test_connection()
        if not is_connected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to connect to Delta Exchange. Please check your credentials."
            )
        
        # Store client for future use
        _user_delta_clients[user_id] = client
        
        # Update last_used timestamp
        await database.execute(
            """
            UPDATE user_credentials 
            SET last_used = NOW() 
            WHERE user_id = :user_id AND provider = 'delta_exchange'
            """,
            {"user_id": user_id}
        )
        
        return client
    
    # Run async function in event loop
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(create_client_from_db())
    except RuntimeError:
        # If no event loop exists, create one
        return asyncio.run(create_client_from_db())
