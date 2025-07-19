from pydantic import BaseModel
from ..users.schemas import UserResponse

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str
    user: UserResponse
