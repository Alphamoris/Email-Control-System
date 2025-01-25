from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core import auth, security
from app.core.config import settings
from app.db.session import get_db
from app.schemas.user import User, UserCreate, UserLogin, Token, TokenPayload
from app.models.user import User as UserModel

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    *,
    db: Session = Depends(get_db),
    response: Response,
    user_in: UserLogin,
) -> Any:
    """Login user and return tokens"""
    user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if not user or not security.verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    elif user.is_locked:
        raise HTTPException(status_code=401, detail="Account is locked. Please try again later")

    # Update user login info
    user.update_last_login()
    user.reset_failed_login()
    db.commit()

    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = security.create_token(
        user.id, expires_delta=access_token_expires, token_type="access"
    )
    refresh_token = security.create_token(
        user.id, expires_delta=refresh_token_expires, token_type="refresh"
    )

    # Set refresh token in HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Any:
    """Refresh access token"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        token_data = security.decode_token(refresh_token)
        if token_data.token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user = db.query(UserModel).filter(UserModel.id == token_data.sub).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        # Create new tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = security.create_token(
            user.id, expires_delta=access_token_expires, token_type="access"
        )
        new_refresh_token = security.create_token(
            user.id, expires_delta=refresh_token_expires, token_type="refresh"
        )

        # Update refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "user": user
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/register", response_model=Token)
async def register(
    *,
    db: Session = Depends(get_db),
    response: Response,
    user_in: UserCreate,
) -> Any:
    """Register new user"""
    # Check if user exists
    user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists",
        )
    
    # Create new user
    user = UserModel(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = security.create_token(
        user.id, expires_delta=access_token_expires, token_type="access"
    )
    refresh_token = security.create_token(
        user.id, expires_delta=refresh_token_expires, token_type="refresh"
    )

    # Set refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/logout")
async def logout(response: Response) -> Any:
    """Logout user"""
    response.delete_cookie(key="refresh_token")
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: UserModel = Depends(auth.get_current_user),
) -> Any:
    """Get current user"""
    return current_user
