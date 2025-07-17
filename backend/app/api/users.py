"""
User authentication API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timedelta
import secrets
import logging
from sqlalchemy import select, insert

from app.db import database
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Models
class UserCreate(BaseModel):
    """User registration request model"""
    username: str
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login request model"""
    username: str
    password: str


class UserResponse(BaseModel):
    """User data response model"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Simple password hashing for now (replace with proper bcrypt in production)
def hash_password(password: str) -> str:
    return f"hashed_{password}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashed_password == f"hashed_{plain_password}"


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.jwt_expiration_days))
    to_encode.update({"exp": expire.timestamp()})
    # Simple token generation for demo purposes
    token = secrets.token_urlsafe(64)
    return token


@router.post("/register", response_model=Token)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if username already exists
        existing_user = await database.fetch_one(
            "SELECT id FROM users WHERE username = :username",
            {"username": user_data.username}
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        existing_email = await database.fetch_one(
            "SELECT id FROM users WHERE email = :email",
            {"email": user_data.email}
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash the password
        hashed_password = hash_password(user_data.password)
        
        # Insert user into database
        user_id = await database.execute(
            """
            INSERT INTO users (username, email, full_name, hashed_password, created_at)
            VALUES (:username, :email, :full_name, :hashed_password, :created_at)
            RETURNING id
            """,
            {
                "username": user_data.username,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "hashed_password": hashed_password,
                "created_at": datetime.utcnow()
            }
        )
        
        # Get created user
        user = await database.fetch_one(
            "SELECT id, username, email, full_name FROM users WHERE id = :id",
            {"id": user_id}
        )
        
        # Create access token
        token = create_access_token({"sub": str(user_id)})
        
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
    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
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
        logging.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/login"))):
    """Get current authenticated user"""
    try:
        # In a real app, you'd decode the JWT token and extract the user ID
        # Here we're just mocking it for simplicity
        user = await database.fetch_one(
            "SELECT id, username, email, full_name FROM users WHERE id = 1"  # Placeholder
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"]
        }
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
