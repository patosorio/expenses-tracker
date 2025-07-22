import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.api import api_router
from .core.config import settings
from .core.database import Base, engine, init_db
from .core.firebase.auth import initialize_firebase
from .core.shared.exceptions_handler import setup_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import models to register them with SQLAlchemy
from .users.models import User, UserSettings
from .categories.models import Category
from .contacts.models import Contact
from .expenses.models import Expense
from .business.models import BusinessSettings, TaxConfiguration
from .team.models import TeamMember, TeamInvitation

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up SmartBudget360 API...")
    
    # Initialize Firebase Admin SDK
    try:
        initialize_firebase()
        logger.info("Firebase initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        raise
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    
    logger.info("SmartBudget360 API startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SmartBudget360 API...")
    # Add any cleanup logic here if needed
    logger.info("SmartBudget360 API shutdown completed")


app = FastAPI(
    title="SmartBudget360 API",
    description="AI-Powered Business Financial Intelligence Platform",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENV", "development") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENV", "development") == "development" else None,
    lifespan=lifespan
)

# Setup global exception handlers
setup_exception_handlers(app)
logger.info("Exception handlers configured")

# Configure CORS
cors_origins = settings.CORS_ORIGINS.copy() if settings.CORS_ORIGINS else []

dev_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    "https://localhost:3000"
]

for origin in dev_origins:
    if origin not in cors_origins:
        cors_origins.append(origin)

logger.info(f"CORS Origins configured: {cors_origins}")
logger.info(f"Environment: {settings.ENV}, Debug: {settings.DEBUG}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
    ],
    expose_headers=["Content-Length", "X-Total-Count"],
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

logger.info("All API routes registered successfully")

# Health check and utility endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "SmartBudget360 API",
        "version": "1.0.0",
        "environment": os.getenv("ENV", "development")
    }


@app.get("/test-cors", tags=["Health"])
async def test_cors():
    """CORS test endpoint for development."""
    return {
        "message": "CORS test successful",
        "cors_origins": cors_origins,
        "environment": os.getenv("ENV", "development")
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to SmartBudget360 API",
        "version": "1.0.0",
        "docs": "/docs" if os.getenv("ENV", "development") == "development" else "Documentation disabled in production",
        "health": "/health"
    }


# Add middleware for request logging in development
if os.getenv("ENV", "development") == "development":
    
    @app.middleware("http")
    async def log_requests(request, call_next):
        """Log all requests in development mode."""
        import time
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} - "
            f"Process time: {process_time:.4f}s"
        )
        
        return response


# Error handling verification endpoint (development only)
if os.getenv("ENV", "development") == "development":
    
    @app.get("/test-exceptions", tags=["Development"])
    async def test_exceptions(exception_type: str = "validation"):
        """Test different exception types (development only)."""
        from .core.shared.exceptions import (
            ValidationError, NotFoundError, BadRequestError, 
            UnauthorizedError, InternalServerError
        )
        
        if exception_type == "validation":
            raise ValidationError(
                detail="Test validation error",
                context={"test": True}
            )
        elif exception_type == "notfound":
            raise NotFoundError(
                detail="Test not found error",
                context={"test": True}
            )
        elif exception_type == "badrequest":
            raise BadRequestError(
                detail="Test bad request error",
                context={"test": True}
            )
        elif exception_type == "unauthorized":
            raise UnauthorizedError(
                detail="Test unauthorized error",
                context={"test": True}
            )
        elif exception_type == "internal":
            raise InternalServerError(
                detail="Test internal server error",
                context={"test": True}
            )
        else:
            raise Exception("Test generic exception")
        
        return {"message": "This should not be reached"}