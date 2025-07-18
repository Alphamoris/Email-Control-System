



from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core import auth, security
from app.core.config import settings
from app.db.session import get_db
from app.schemas.user import User, UserCreate, UserLogin, Token, TokenPayload
from app.models.user import User as UserModel
from app.core.exceptions import AuthenticationError, UserNotFoundError
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    *,
    db: Session = Depends(get_db),
    response: Response,
    user_in: UserLogin,
) -> Any:
    """Login user and return tokens"""
    try:
        user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
        if not user or not security.verify_password(user_in.password, user.hashed_password):
            user.increment_failed_login() if user else None
            db.commit()
            raise AuthenticationError("Incorrect email or password")
        
        if not user.is_active:
            raise AuthenticationError("Inactive user")
        
        if user.is_locked:
            raise AuthenticationError(
                f"Account is locked. Please try again after {user.lock_expiry}"
            )

        # Update user login info
        user.last_login = datetime.utcnow()
        user.failed_login_attempts = 0
        user.lock_expiry = None
        db.commit()

        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = security.create_token(
            user.id,
            expires_delta=access_token_expires,
            token_type="access",
            user_claims={"email": user.email, "role": user.role}
        )
        refresh_token = security.create_token(
            user.id,
            expires_delta=refresh_token_expires,
            token_type="refresh"
        )

        # Set refresh token in HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/api/v1/auth/refresh"
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active
            }
        }

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Any:
    """Refresh access token"""
    try:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise AuthenticationError("Refresh token missing")

        # Verify refresh token
        payload = security.decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        # Get user
        user = db.query(UserModel).filter(UserModel.id == payload.get("sub")).first()
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_token(
            user.id,
            expires_delta=access_token_expires,
            token_type="access",
            user_claims={"email": user.email, "role": user.role}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active
            }
        }

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/register", response_model=Token)
async def register(
    *,
    db: Session = Depends(get_db),
    response: Response,
    user_in: UserCreate,
) -> Any:
    """Register new user"""
    try:
        # Check if user exists
        if db.query(UserModel).filter(UserModel.email == user_in.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user
        user = UserModel(
            email=user_in.email,
            hashed_password=security.get_password_hash(user_in.password),
            full_name=user_in.full_name,
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = security.create_token(
            user.id,
            expires_delta=access_token_expires,
            token_type="access",
            user_claims={"email": user.email, "role": user.role}
        )
        refresh_token = security.create_token(
            user.id,
            expires_delta=refresh_token_expires,
            token_type="refresh"
        )

        # Set refresh token in HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/api/v1/auth/refresh"
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/logout")
async def logout(response: Response) -> Any:
    """Logout user"""
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth/refresh",
        secure=True,
        httponly=True
    )
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: UserModel = Depends(auth.get_current_user),
) -> Any:
    """Get current user"""
    return current_user
