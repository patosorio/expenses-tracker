from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.firebase.auth import verify_firebase_token
from src.users.service import UserService
from src.users.models import User
from src.database import get_db
from src.users.schemas import UserCreate

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        decoded_token = await verify_firebase_token(token)
        firebase_uid = decoded_token.get('uid')
        
        if not firebase_uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user_service = UserService(db)
        user = await user_service.get_user_by_firebase_uid(firebase_uid)
        
        if not user:
            # Create user if doesn't exist
            user_data = UserCreate(
                firebase_uid=firebase_uid,
                email=decoded_token.get('email'),
                full_name=decoded_token.get('name'),
                is_verified=decoded_token.get('email_verified', False)
            )
            user = await user_service.create_user(user_data)
        
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