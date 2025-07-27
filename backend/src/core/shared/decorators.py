from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException, status
import logging

from .exceptions import (
    AppBaseException, ValidationError, NotFoundError, 
    ConflictError, BadRequestError, UnauthorizedError,
    ForbiddenError, ExternalServiceError, InternalServerError
)

logger = logging.getLogger(__name__)


def handle_service_exceptions(func: Callable) -> Callable:
    """
    Decorator to handle service layer exceptions and convert them to appropriate HTTP responses.
    
    Usage:
        @router.get("/items/{item_id}")
        @handle_service_exceptions
        async def get_item(item_id: UUID, current_user: User = Depends(get_current_user)):
            return await item_service.get_by_id(item_id, current_user.id)
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
            
        except AppBaseException as e:
            # Map custom exceptions to HTTP exceptions
            status_map = {
                ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
                NotFoundError: status.HTTP_404_NOT_FOUND,
                ConflictError: status.HTTP_409_CONFLICT,
                BadRequestError: status.HTTP_400_BAD_REQUEST,
                UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
                ForbiddenError: status.HTTP_403_FORBIDDEN,
                ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
                InternalServerError: status.HTTP_500_INTERNAL_SERVER_ERROR,
            }
            
            http_status = status_map.get(type(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Log error with context
            log_context = {
                "error_type": type(e).__name__,
                "error_code": e.error_code,
                "detail": e.detail,
                "context": e.context,
                "function": func.__name__
            }
            
            if http_status >= 500:
                logger.error(f"Server error in {func.__name__}: {e}", extra=log_context)
            else:
                logger.warning(f"Client error in {func.__name__}: {e}", extra=log_context)
            
            # Create HTTP exception with structured error response
            raise HTTPException(
                status_code=http_status,
                detail={
                    "error_code": e.error_code,
                    "message": e.detail,
                    "context": e.context if e.context else None,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None
                }
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
            
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "context": None,
                    "timestamp": None
                }
            )
    
    return wrapper


def validate_pagination(func: Callable) -> Callable:
    """
    Decorator to validate pagination parameters.
    
    Usage:
        @router.get("/items/")
        @validate_pagination
        async def get_items(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=100)
        ):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # Extract pagination parameters from kwargs
        skip = kwargs.get('skip', 0)
        limit = kwargs.get('limit', 100)
        
        # Validate parameters
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "INVALID_PAGINATION",
                    "message": "Skip parameter cannot be negative",
                    "context": {"skip": skip}
                }
            )
        
        if limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "INVALID_PAGINATION", 
                    "message": "Limit parameter must be positive",
                    "context": {"limit": limit}
                }
            )
        
        if limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "INVALID_PAGINATION",
                    "message": "Limit parameter cannot exceed 1000", 
                    "context": {"limit": limit, "max_limit": 1000}
                }
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


def require_user_ownership(entity_param: str = "entity_id"):
    """
    Decorator to ensure user owns the requested resource.
    
    Args:
        entity_param: Name of the parameter containing the entity ID
    
    Usage:
        @router.get("/categories/{category_id}")
        @require_user_ownership("category_id")
        async def get_category(
            category_id: UUID,
            current_user: User = Depends(get_current_user)
        ):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # This decorator works in conjunction with service layer validation
            # The actual ownership check is performed in the service layer
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def log_api_call(include_response: bool = False):
    """
    Decorator to log API calls with request details.
    
    Args:
        include_response: Whether to log response data (be careful with sensitive data)
    
    Usage:
        @router.post("/categories/")
        @log_api_call(include_response=True)
        async def create_category(category_data: CategoryCreate):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Log request
            log_data = {
                "function": func.__name__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }
            
            # Extract user info if available
            current_user = kwargs.get('current_user')
            if current_user:
                log_data["user_id"] = current_user.id
            
            logger.info(f"API call: {func.__name__}", extra=log_data)
            
            try:
                result = await func(*args, **kwargs)
                
                if include_response:
                    logger.info(f"API response: {func.__name__}", extra={
                        **log_data,
                        "response_type": type(result).__name__
                    })
                
                return result
                
            except Exception as e:
                logger.error(f"API error: {func.__name__}: {str(e)}", extra=log_data)
                raise
        
        return wrapper
    return decorator


def cache_response(ttl_seconds: int = 300):
    """
    Decorator for response caching (placeholder for future Redis integration).
    
    Args:
        ttl_seconds: Time to live for cached response
    
    Usage:
        @router.get("/categories/stats")
        @cache_response(ttl_seconds=600)
        async def get_category_stats():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # TODO: Implement Redis caching when Redis is integrated
            # For now, just execute the function
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(requests_per_minute: int = 60):
    """
    Decorator for rate limiting (placeholder for future rate limiting implementation).
    
    Args:
        requests_per_minute: Maximum requests per minute per user
    
    Usage:
        @router.post("/expenses/ocr")
        @rate_limit(requests_per_minute=10)  # Limit OCR requests
        async def process_ocr():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # TODO: Implement rate limiting when Redis is integrated
            # For now, just execute the function
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Combined decorator for common patterns
def api_endpoint(
    handle_exceptions: bool = True,
    validate_pagination_params: bool = False,
    log_calls: bool = True,
    require_ownership: str = None
):
    """
    Combined decorator for common API endpoint patterns.
    
    Args:
        handle_exceptions: Apply exception handling
        validate_pagination_params: Apply pagination validation
        log_calls: Apply call logging
        require_ownership: Parameter name for ownership validation
    
    Usage:
        @router.get("/categories/")
        @api_endpoint(validate_pagination_params=True, log_calls=True)
        async def get_categories(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=100)
        ):
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Apply decorators in reverse order (inside out)
        decorated_func = func
        
        if require_ownership:
            decorated_func = require_user_ownership(require_ownership)(decorated_func)
        
        if validate_pagination_params:
            decorated_func = validate_pagination(decorated_func)
        
        if log_calls:
            decorated_func = log_api_call()(decorated_func)
        
        if handle_exceptions:
            decorated_func = handle_service_exceptions(decorated_func)
        
        return decorated_func
    
    return decorator