from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .dependencies import get_current_user
from .schemas import TokenResponse
from ..users.models import User
from ..core.database import get_db
from ..users.service import UserService

router = APIRouter()

@router.post("/verify", response_model=TokenResponse)
async def verify_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify Firebase token and return user info"""
    # Update last login
    user_service = UserService(db)
    await user_service.update_last_login(current_user.id)
    
    return TokenResponse(
        access_token="firebase_token_verified",
        token_type="bearer",
        user=current_user
    )

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user info"""
    return current_user

@router.post("/logout")
async def logout():
    """Logout - client side only"""
    return {"message": "Logged out successfully"}