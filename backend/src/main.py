from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.api import api_router
from .core.config import settings
from .core.database import Base, engine, init_db
from .core.firebase.auth import initialize_firebase

# Import models to register them with SQLAlchemy
from .users.models import User, UserSettings
from .categories.models import Category
from .contacts.models import Contact
from .expenses.models import Expense
from .business.models import BusinessSettings, TaxConfiguration
from .team.models import TeamMember, TeamInvitation

# Initialize Firebase Admin SDK
initialize_firebase()

app = FastAPI(
    title="Expense Tracker API",
    description="API for tracking expenses with Firebase authentication",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    await init_db()

# Configure CORS
print(f"CORS Origins: {settings.CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Length"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include API routes - including expenses now
from .auth.routes import router as auth_router
from .users.routes import router as users_router
from .categories.routes import router as categories_router
from .contacts.routes import router as contacts_router
from .business.routes import router as business_router
from .team.routes import router as team_router
from .expenses.routes import router as expenses_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(categories_router, prefix="/api/v1/categories", tags=["Categories"])
app.include_router(contacts_router, prefix="/api/v1/contacts", tags=["Contacts"])
app.include_router(business_router, prefix="/api/v1/business", tags=["Business"])
app.include_router(team_router, prefix="/api/v1/team", tags=["Team"])
app.include_router(expenses_router, prefix="/api/v1/expenses", tags=["Expenses"])

# app.include_router(api_router, prefix="/api/v1")  # Temporarily commented out

@app.get("/test-cors")
async def test_cors():
    return {"message": "CORS test successful"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}