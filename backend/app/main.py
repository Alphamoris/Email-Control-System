from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import (
    EmailNotFoundError,
    StorageError,
    RateLimitExceededError,
    InvalidEmailError,
    AuthenticationError,
    PermissionDeniedError
)
import logging

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Email Control System API",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "X-Total-Count"],
    max_age=3600,
)

# Add API router
app.include_router(api_router, prefix="/api/v1")

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )

@app.exception_handler(EmailNotFoundError)
async def email_not_found_exception_handler(request: Request, exc: EmailNotFoundError):
    """Handle email not found errors"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )

@app.exception_handler(StorageError)
async def storage_exception_handler(request: Request, exc: StorageError):
    """Handle storage errors"""
    logger.error(f"Storage error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)}
    )

@app.exception_handler(RateLimitExceededError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceededError):
    """Handle rate limit exceeded errors"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": str(exc)},
        headers={"Retry-After": str(exc.retry_after)}
    )

@app.exception_handler(InvalidEmailError)
async def invalid_email_exception_handler(request: Request, exc: InvalidEmailError):
    """Handle invalid email errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )

@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors"""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)}
    )

@app.exception_handler(PermissionDeniedError)
async def permission_denied_exception_handler(request: Request, exc: PermissionDeniedError):
    """Handle permission denied errors"""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
