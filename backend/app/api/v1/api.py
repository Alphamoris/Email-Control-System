from fastapi import APIRouter
from app.api.v1.endpoints import auth, emails

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])
