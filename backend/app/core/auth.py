"""
User authentication and management module.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, EmailStr
import logging
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from app.core.config import settings
from app.core.database import Base

logger = logging.getLogger(__name__)

# Database models
class User(Base):
    """User database model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(128))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

# API models
class UserCreate(BaseModel):
    """User creation request model"""
    username: str
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    """User login request model"""
    username: str
    password: str

class UserResponse(BaseModel):
    """User response model"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    user: UserResponse

class UserSettings(BaseModel):
    """User settings model"""
    delta_exchange_api_key: Optional[str] = None
    delta_exchange_api_secret: Optional[str] = None

# Auth functions
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT token with the provided data"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.jwt_expiration_days)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current user from the JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Here you would query the database for the user
    # For demonstration, we'll add that function later
    user = await get_user_by_username(username)
    if user is None:
        raise credentials_exception
    
    return user

async def get_user_by_username(username: str) -> Optional[User]:
    """Get a user by username from the database"""
    # This will be implemented with database access
    # For now it's a placeholder
    pass
