
# Global exception handler for FastAPI application
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from core.exceptions import AppBaseException

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup global exception handlers for the FastAPI application."""

    @app.exception_handler(AppBaseException)
    async def app_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
        """Handle custom application exceptions."""
        logger.error(
            f"Application exception: {exc.__class__.__name__} - {exc.detail}",
            extra={
                "path": str(request.url),
                "method": request.method,
                "error_code": getattr(exc, 'error_code', None),
                "context": getattr(exc, 'context', None)
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail}",
            extra={"path": str(request.url), "method": request.method}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "status_code": exc.status_code,
                "detail": exc.detail
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        logger.warning(
            f"Validation error: {exc.errors()}",
            extra={"path": str(request.url), "method": request.method}
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": True,
                "status_code": 422,
                "detail": "Validation failed",
                "error_code": "VALIDATION_ERROR",
                "errors": exc.errors()
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle Starlette HTTP exceptions."""
        logger.error(
            f"Starlette HTTP exception: {exc.status_code} - {exc.detail}",
            extra={"path": str(request.url), "method": request.method}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "status_code": exc.status_code,
                "detail": exc.detail or "Internal server error"
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.error(
            f"Unexpected error: {exc.__class__.__name__} - {str(exc)}",
            extra={"path": str(request.url), "method": request.method},
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "status_code": 500,
                "detail": "Internal server error",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )