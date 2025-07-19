from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..core.firebase.auth import verify_firebase_token
from ..users.models import User
from ..users.schemas import UserCreate
from ..users.repository import UserRepository

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def authenticate_user(self, token: str) -> User:
        """Authenticate user with Firebase token"""
        try:
            decoded_token = await verify_firebase_token(token)
            firebase_uid = decoded_token.get('uid')
            
            if not firebase_uid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
            
            user = await self.user_repo.get_user_by_firebase_uid(firebase_uid)
            
            if not user:
                # Create user if doesn't exist
                user_data = UserCreate(
                    firebase_uid=firebase_uid,
                    email=decoded_token.get('email'),
                    full_name=decoded_token.get('name'),
                    is_verified=decoded_token.get('email_verified', False)
                )
                user = await self.user_repo.create_user(user_data)
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )
            
            return user
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            ) 