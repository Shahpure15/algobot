"""
User profile management API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, SecretStr
from typing import Optional, List
from datetime import datetime
import logging

from app.db import database
from app.api.auth import get_current_user_id
from app.api.auth import get_user_delta_client

router = APIRouter(prefix="/api/profile", tags=["profile"])

# Models
class CredentialsUpdate(BaseModel):
    """API credentials update request model"""
    provider: str = Field(..., description="Provider name (e.g., 'delta_exchange')")
    credential_name: str = Field(..., description="Name for this API key")
    api_key: str = Field(..., description="API key")
    api_secret: SecretStr = Field(..., description="API secret")

class CredentialsResponse(BaseModel):
    """API credentials response model"""
    id: int
    provider: str
    credential_name: str
    api_key: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime] = None

class UserProfile(BaseModel):
    """User profile response model"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    credentials: List[CredentialsResponse] = []

class ProfileUpdate(BaseModel):
    """Profile update request model"""
    email: Optional[str] = None
    full_name: Optional[str] = None

class PasswordUpdate(BaseModel):
    """Password update request model"""
    current_password: str
    new_password: str = Field(..., min_length=8)

@router.get("/", response_model=UserProfile)
async def get_profile(user_id: int = Depends(get_current_user_id)):
    """Get current user's profile with API credentials"""
    try:
        # Get user profile
        user = await database.fetch_one(
            """
            SELECT id, username, email, full_name, created_at, last_login 
            FROM users 
            WHERE id = :user_id
            """,
            {"user_id": user_id}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user credentials (without showing API secret)
        credentials = await database.fetch_all(
            """
            SELECT id, provider, credential_name, api_key, is_active, created_at, last_used 
            FROM user_credentials 
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            """,
            {"user_id": user_id}
        )
        
        return UserProfile(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at,
            last_login=user.last_login,
            credentials=[CredentialsResponse(**cred) for cred in credentials]
        )
    
    except Exception as e:
        logging.error(f"Error getting profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )

@router.put("/", response_model=UserProfile)
async def update_profile(
    profile_update: ProfileUpdate,
    user_id: int = Depends(get_current_user_id)
):
    """Update user profile"""
    try:
        # Build update query dynamically
        updates = {}
        if profile_update.email is not None:
            updates["email"] = profile_update.email
        if profile_update.full_name is not None:
            updates["full_name"] = profile_update.full_name
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided"
            )
        
        # Check if email already exists (if updating email)
        if "email" in updates:
            existing_email = await database.fetch_one(
                "SELECT id FROM users WHERE email = :email AND id != :user_id",
                {"email": updates["email"], "user_id": user_id}
            )
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        # Update user profile
        set_clause = ", ".join([f"{key} = :{key}" for key in updates.keys()])
        query = f"""
            UPDATE users 
            SET {set_clause}
            WHERE id = :user_id
        """
        updates["user_id"] = user_id
        
        await database.execute(query, updates)
        
        # Return updated profile
        return await get_profile(user_id)
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.post("/credentials")
async def update_credentials(
    credentials: CredentialsUpdate,
    user_id: int = Depends(get_current_user_id)
):
    """Update or create API credentials for a provider with connection testing"""
    try:
        # Check if API key already exists for another user
        existing_key = await database.fetch_one(
            """
            SELECT user_id FROM user_credentials 
            WHERE api_key = :api_key AND provider = :provider AND user_id != :user_id
            """,
            {
                "api_key": credentials.api_key,
                "provider": credentials.provider,
                "user_id": user_id
            }
        )
        
        if existing_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"API key already exists for provider {credentials.provider}"
            )
        
        # Test connection before saving for Delta Exchange
        connection_status = {"is_connected": False, "error": None}
        if credentials.provider == "delta_exchange":
            from app.core.delta_exchange import DeltaExchangeClient, DeltaExchangeConfig
            from app.api.auth import _user_delta_clients
            
            try:
                # Create client configuration
                config = DeltaExchangeConfig(
                    api_key=credentials.api_key,
                    api_secret=credentials.api_secret.get_secret_value()
                )
                
                # Create and test client
                client = DeltaExchangeClient(config)
                is_connected = await client.test_connection()
                
                if is_connected:
                    connection_status["is_connected"] = True
                    
                    # Store client for this user
                    if user_id in _user_delta_clients:
                        old_client = _user_delta_clients[user_id]
                        try:
                            await old_client.close()
                        except:
                            pass
                    
                    _user_delta_clients[user_id] = client
                    
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
                else:
                    connection_status["error"] = "Failed to connect with provided credentials"
                    if hasattr(client, 'close'):
                        await client.close()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid API credentials - connection test failed"
                    )
                    
            except Exception as e:
                connection_status["error"] = str(e)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Connection test failed: {str(e)}"
                )
        
        # Check if credential name already exists for this user and provider
        existing_name = await database.fetch_one(
            """
            SELECT id FROM user_credentials 
            WHERE user_id = :user_id AND provider = :provider AND credential_name = :credential_name
            """,
            {
                "user_id": user_id,
                "provider": credentials.provider,
                "credential_name": credentials.credential_name
            }
        )
        
        if existing_name:
            # Update existing credentials
            await database.execute(
                """
                UPDATE user_credentials 
                SET api_key = :api_key, api_secret = :api_secret, last_used = NOW(), is_active = TRUE
                WHERE user_id = :user_id AND provider = :provider AND credential_name = :credential_name
                """,
                {
                    "api_key": credentials.api_key,
                    "api_secret": credentials.api_secret.get_secret_value(),
                    "user_id": user_id,
                    "provider": credentials.provider,
                    "credential_name": credentials.credential_name
                }
            )
        else:
            # Insert new credentials
            await database.execute(
                """
                INSERT INTO user_credentials (user_id, provider, credential_name, api_key, api_secret, is_active, last_used)
                VALUES (:user_id, :provider, :credential_name, :api_key, :api_secret, TRUE, NOW())
                """,
                {
                    "user_id": user_id,
                    "provider": credentials.provider,
                    "credential_name": credentials.credential_name,
                    "api_key": credentials.api_key,
                    "api_secret": credentials.api_secret.get_secret_value()
                }
            )
        
        return {
            "message": "Credentials saved and connection tested successfully",
            "connection_status": connection_status
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update credentials"
        )


@router.get("/credentials")
async def get_credentials(user_id: int = Depends(get_current_user_id)):
    """Get all user credentials"""
    try:
        credentials = await database.fetch_all(
            """
            SELECT id, provider, credential_name, api_key, is_active, created_at, last_used 
            FROM user_credentials 
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            """,
            {"user_id": user_id}
        )
        
        return [CredentialsResponse(**cred) for cred in credentials]
    
    except Exception as e:
        logging.error(f"Error getting credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get credentials"
        )

@router.post("/connect/{credential_id}")
async def connect_with_credential(
    credential_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """Connect using existing credential"""
    try:
        # Get the credential
        credential = await database.fetch_one(
            """
            SELECT provider, credential_name, api_key, api_secret 
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
        
        if credential.provider == "delta_exchange":
            from app.core.delta_exchange import DeltaExchangeClient, DeltaExchangeConfig
            from app.api.auth import _user_delta_clients
            
            # Create client configuration
            config = DeltaExchangeConfig(
                api_key=credential.api_key,
                api_secret=credential.api_secret
            )
            
            # Create and test client
            client = DeltaExchangeClient(config)
            is_connected = await client.test_connection()
            
            if is_connected:
                # Store client for this user
                if user_id in _user_delta_clients:
                    # Close old client if it exists
                    old_client = _user_delta_clients[user_id]
                    try:
                        await old_client.close()
                    except:
                        pass
                
                _user_delta_clients[user_id] = client
                
                # Update last_used timestamp
                await database.execute(
                    """
                    UPDATE user_credentials 
                    SET last_used = NOW() 
                    WHERE id = :credential_id
                    """,
                    {"credential_id": credential_id}
                )
                
                return {
                    "success": True,
                    "message": f"Successfully connected using '{credential.credential_name}'",
                    "credential_name": credential.credential_name,
                    "has_wallet_permissions": client.has_wallet_permissions
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to connect using '{credential.credential_name}'"
                }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider {credential.provider} not supported"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error connecting with credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect with credential"
        )

@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """Delete a specific credential"""
    try:
        # Check if credential exists
        credential = await database.fetch_one(
            """
            SELECT id, provider FROM user_credentials 
            WHERE id = :credential_id AND user_id = :user_id
            """,
            {"credential_id": credential_id, "user_id": user_id}
        )
        
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
        
        # Delete credential
        await database.execute(
            "DELETE FROM user_credentials WHERE id = :credential_id",
            {"credential_id": credential_id}
        )
        
        # If it's Delta Exchange, clean up the client
        if credential.provider == "delta_exchange":
            from app.api.auth import _user_delta_clients
            
            if user_id in _user_delta_clients:
                try:
                    client = _user_delta_clients[user_id]
                    await client.close()
                except:
                    pass
                finally:
                    del _user_delta_clients[user_id]
                    logging.info(f"Delta Exchange client cleaned up for user {user_id}")
        
        return {"message": "Credential deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete credential"
        )

@router.delete("/credentials/{provider}")
async def delete_credentials(provider: str):
    """Delete API credentials for a provider"""
    try:
        # For simplicity, just delete the first credential for this provider
        existing = await database.fetch_one(
            "SELECT id FROM user_credentials WHERE provider = :provider LIMIT 1",
            {"provider": provider}
        )
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No credentials found for provider {provider}"
            )
        
        # Delete credentials (simplified - delete all for this provider)
        await database.execute(
            "DELETE FROM user_credentials WHERE provider = :provider",
            {"provider": provider}
        )
        
        # If it's Delta Exchange, clean up all clients
        if provider == "delta_exchange":
            from app.api.auth import _user_delta_clients
            
            # Clear all delta clients
            for user_id in list(_user_delta_clients.keys()):
                try:
                    client = _user_delta_clients[user_id]
                    await client.close()
                except:
                    pass
                finally:
                    del _user_delta_clients[user_id]
            
            logging.info(f"All Delta Exchange clients cleaned up")
        
        return {"message": f"Credentials deleted successfully for {provider}"}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete credentials"
        )

@router.post("/test-connection/{provider}")
async def test_connection(
    provider: str,
    user_id: int = Depends(get_current_user_id)
):
    """Test API connection for a provider"""
    try:
        if provider == "delta_exchange":
            # Get user credentials from database
            credentials = await database.fetch_one(
                """
                SELECT api_key, api_secret FROM user_credentials 
                WHERE user_id = :user_id AND provider = 'delta_exchange' AND is_active = TRUE
                """,
                {"user_id": user_id}
            )
            
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No credentials configured for Delta Exchange"
                )
            
            # Create client with stored credentials
            from app.core.delta_exchange import DeltaExchangeClient, DeltaExchangeConfig
            
            config = DeltaExchangeConfig(
                api_key=credentials.api_key,
                api_secret=credentials.api_secret
            )
            
            client = DeltaExchangeClient(config)
            
            # Test connection
            is_connected = await client.test_connection()
            
            if is_connected:
                # Update last_used timestamp
                await database.execute(
                    """
                    UPDATE user_credentials 
                    SET last_used = NOW() 
                    WHERE user_id = :user_id AND provider = :provider
                    """,
                    {"user_id": user_id, "provider": provider}
                )
                
                return {
                    "success": True,
                    "message": "Connection successful",
                    "has_wallet_permissions": client.has_wallet_permissions
                }
            else:
                return {
                    "success": False,
                    "message": "Connection failed - unable to connect to Delta Exchange"
                }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider {provider} not supported"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error testing connection: {str(e)}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}"
        }

@router.put("/password")
async def update_password(
    password_update: PasswordUpdate,
    user_id: int = Depends(get_current_user_id)
):
    """Update user password"""
    try:
        # Get current user
        user = await database.fetch_one(
            "SELECT hashed_password FROM users WHERE id = :user_id",
            {"user_id": user_id}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password (using simple hash for now)
        if user.hashed_password != f"hashed_{password_update.current_password}":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        new_hashed_password = f"hashed_{password_update.new_password}"
        await database.execute(
            "UPDATE users SET hashed_password = :password WHERE id = :user_id",
            {"password": new_hashed_password, "user_id": user_id}
        )
        
        return {"message": "Password updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
