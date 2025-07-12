from fastapi import APIRouter

from src.auth.routes import router as auth_router
from src.users.routes import router as users_router
from src.categories.routes import router as categories_router
from src.expenses.routes import router as expenses_router
from src.business.routes import router as business_router
from src.team.routes import router as team_router

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

api_router.include_router(
    categories_router,
    prefix="/categories",
    tags=["Categories"]
)

api_router.include_router(
    expenses_router,
    prefix="/expenses",
    tags=["Expenses"]
)

api_router.include_router(
    business_router,
    prefix="/business",
    tags=["Business"]
)

api_router.include_router(
    team_router,
    prefix="/team",
    tags=["Team"]
)

