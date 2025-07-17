from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router
from src.config import settings
from src.database import Base, engine
from src.firebase.auth import initialize_firebase

# Import models to register them with SQLAlchemy
from src.users.models import User, UserSettings
from src.categories.models import Category
from src.contacts.models import Contact
from src.expenses.models import Expense
from src.business.models import BusinessSettings, TaxConfiguration
from src.team.models import TeamMember, TeamInvitation

# Initialize Firebase Admin SDK
initialize_firebase()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Expense Tracker API",
    description="API for tracking expenses with Firebase authentication",
    version="1.0.0",
)

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

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/test-cors")
async def test_cors():
    return {"message": "CORS test successful"}