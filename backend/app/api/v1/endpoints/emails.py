from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.email_service import EmailService
from app.services.storage_service import StorageService
from app.schemas.email import (
    EmailCreate,
    EmailResponse,
    EmailUpdate,
    EmailBulkAction,
    EmailFilter,
    EmailAttachment,
    PaginatedEmailResponse
)
from app.models.email import Email
from app.models.email_account import EmailAccount
from app.core.auth import get_current_user, RateLimiter
from app.core.config import settings
from app.core.exceptions import (
    EmailNotFoundError,
    StorageError,
    RateLimitExceededError,
    InvalidEmailError
)

router = APIRouter()
rate_limiter = RateLimiter()

@router.get("/", response_model=PaginatedEmailResponse)
async def list_emails(
    background_tasks: BackgroundTasks,
    folder: str = "inbox",
    is_read: Optional[bool] = None,
    is_starred: Optional[bool] = None,
    account_id: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: str = "received_at",
    sort_desc: bool = True,
    page: int = Query(1, gt=0),
    page_size: int = Query(20, gt=0, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List emails with filtering and pagination"""
    try:
        await rate_limiter.check_rate_limit(current_user.id, "list_emails")
        email_service = EmailService(db)
        filter_params = EmailFilter(
            folder=folder,
            is_read=is_read,
            is_starred=is_starred,
            account_id=account_id,
            search=search,
            sort_by=sort_by,
            sort_desc=sort_desc
        )
        
        emails, total = await email_service.list_emails(
            user_id=current_user.id,
            filter_params=filter_params,
            page=page,
            page_size=page_size
        )

        # Start background sync if needed
        if not account_id:
            for account in current_user.email_accounts:
                if account.is_active:
                    background_tasks.add_task(
                        email_service.fetch_new_emails,
                        user_id=current_user.id,
                        account_id=account.id
                    )

        return {
            "items": emails,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in list_emails: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch emails"
        )

@router.post("/send", response_model=EmailResponse)
async def send_email(
    email_data: EmailCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Send a new email"""
    try:
        await rate_limiter.check_rate_limit(current_user.id, "send_email")
        email_service = EmailService(db)
        email = await email_service.send_email(
            user_id=current_user.id,
            email_data=email_data
        )
        return email

    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in send_email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )

@router.post("/attachments", response_model=EmailAttachment)
async def upload_attachment(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Upload email attachment"""
    try:
        await rate_limiter.check_rate_limit(current_user.id, "upload_attachment")
        
        # Validate file size
        if file.size > settings.MAX_ATTACHMENT_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large"
            )

        # Validate file type
        if file.content_type not in settings.ALLOWED_ATTACHMENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported file type"
            )

        storage_service = StorageService()
        attachment = await storage_service.store_attachment(file)
        return attachment

    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except StorageError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in upload_attachment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload attachment"
        )

@router.post("/sync")
async def sync_emails(
    background_tasks: BackgroundTasks,
    account_id: int,
    sync_all: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Start email synchronization"""
    try:
        email_service = EmailService(db)
        background_tasks.add_task(
            email_service.fetch_new_emails,
            user_id=current_user.id,
            account_id=account_id,
            sync_all=sync_all
        )
        return {"message": "Sync started"}

    except Exception as e:
        logger.error(f"Error in sync_emails: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start sync"
        )

@router.post("/fetch")
async def fetch_emails(
    background_tasks: BackgroundTasks,
    account_id: int,
    sync_all: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Fetch new emails from the email provider"""
    try:
        await rate_limiter.check_rate_limit(current_user.id, "fetch_emails")
        email_service = EmailService(db)
        
        # Start sync in background
        background_tasks.add_task(
            email_service.sync_emails,
            user_id=current_user.id,
            account_id=account_id,
            sync_all=sync_all
        )
        
        return {
            "message": "Email synchronization started",
            "status": "processing"
        }
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers={"Retry-After": str(e.retry_after)}
        )

@router.post("/bulk-action")
async def bulk_action(
    action_data: EmailBulkAction,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Perform bulk actions on emails"""
    try:
        await rate_limiter.check_rate_limit(current_user.id, "bulk_action")
        email_service = EmailService(db)
        result = await email_service.perform_bulk_action(
            user_id=current_user.id,
            action_data=action_data
        )
        return result
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers={"Retry-After": str(e.retry_after)}
        )
    except EmailNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.patch("/{email_id}")
async def update_email(
    email_id: int,
    email_update: EmailUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update email properties"""
    try:
        await rate_limiter.check_rate_limit(current_user.id, "update_email")
        email_service = EmailService(db)
        email = await email_service.update_email(
            user_id=current_user.id,
            email_id=email_id,
            update_data=email_update
        )
        return email
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers={"Retry-After": str(e.retry_after)}
        )
    except EmailNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.delete("/{email_id}")
async def delete_email(
    email_id: int,
    permanent: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an email"""
    try:
        await rate_limiter.check_rate_limit(current_user.id, "delete_email")
        email_service = EmailService(db)
        await email_service.delete_email(
            user_id=current_user.id,
            email_id=email_id,
            permanent=permanent
        )
        return {"message": "Email deleted successfully"}
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers={"Retry-After": str(e.retry_after)}
        )
    except EmailNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/sync-status/{account_id}")
async def get_sync_status(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get email account sync status"""
    try:
        email_service = EmailService(db)
        status = await email_service.get_sync_status(
            user_id=current_user.id,
            account_id=account_id
        )
        return status
    except EmailNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
