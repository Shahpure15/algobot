"""
User API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import logging

from app.db import database
from app.core.auth import UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])

# In-memory token storage for demo purposes (use Redis in production)
_active_tokens = {}

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
    
    # Create a proper JWT token
    token = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    
    # Store token in memory for validation
    _active_tokens[token] = {
        "user_id": data.get("sub"),
        "expires": expire,
        "created": datetime.utcnow()
    }
    
    return token


async def get_current_user_id(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/login"))) -> int:
    """Get current user ID from token"""
    try:
        # Check if token exists in active tokens
        if token not in _active_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        token_data = _active_tokens[token]
        
        # Check if token has expired
        if datetime.utcnow() > token_data["expires"]:
            del _active_tokens[token]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        # Decode JWT token
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return int(user_id)
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    except Exception as e:
        logging.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: int = Depends(get_current_user_id)):
    """Get current authenticated user"""
    try:
        user = await database.fetch_one(
            "SELECT id, username, email, full_name FROM users WHERE id = :id",
            {"id": user_id}
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