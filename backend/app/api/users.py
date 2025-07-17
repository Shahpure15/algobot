"""
User API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
import logging

from app.db import database
from app.core.auth import UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])


# Import at module level to avoid circular import
def get_current_user_id_dependency():
    from app.api.auth import get_current_user_id
    return get_current_user_id


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user_id: int = Depends(get_current_user_id_dependency())):
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
