from fastapi import APIRouter

from src.auth.routes import router as auth_router
from src.users.routes import router as users_router

api_router = APIRouter()

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"]
)

