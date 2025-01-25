from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator

class EmailBase(BaseModel):
    """Base email schema with common attributes"""
    subject: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None
    html_content: Optional[str] = None
    folder: str = "inbox"
    is_read: bool = False
    is_starred: bool = False
    priority: int = Field(0, ge=0, le=5)

class EmailCreate(EmailBase):
    """Schema for creating a new email"""
    account_id: int
    recipients: List[EmailStr]
    cc: Optional[List[EmailStr]] = []
    bcc: Optional[List[EmailStr]] = []
    attachments: Optional[List[str]] = []  # List of attachment IDs

    @validator("recipients")
    def validate_recipients(cls, v):
        if not v:
            raise ValueError("At least one recipient is required")
        return v

class EmailUpdate(BaseModel):
    """Schema for updating email properties"""
    is_read: Optional[bool] = None
    is_starred: Optional[bool] = None
    folder: Optional[str] = None
    labels: Optional[List[str]] = None

class EmailResponse(EmailBase):
    """Schema for email response"""
    id: int
    account_id: int
    message_id: str
    sender: EmailStr
    recipients: List[EmailStr]
    cc: Optional[List[EmailStr]]
    bcc: Optional[List[EmailStr]]
    received_at: datetime
    thread_id: Optional[str]
    in_reply_to: Optional[str]
    references: Optional[List[str]]
    labels: Optional[List[str]]
    spam_score: Optional[float]
    attachments: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EmailFilter(BaseModel):
    """Schema for email filtering"""
    folder: Optional[str] = None
    is_read: Optional[bool] = None
    is_starred: Optional[bool] = None
    account_id: Optional[int] = None
    search: Optional[str] = None
    sort_by: str = "received_at"
    sort_desc: bool = True
    labels: Optional[List[str]] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    has_attachments: Optional[bool] = None

class EmailBulkAction(BaseModel):
    """Schema for bulk email actions"""
    email_ids: List[int]
    action: str = Field(..., regex="^(mark_read|mark_unread|star|unstar|move|delete|label|unlabel)$")
    target_folder: Optional[str] = None
    labels: Optional[List[str]] = None

    @validator("email_ids")
    def validate_email_ids(cls, v):
        if not v:
            raise ValueError("At least one email ID is required")
        return v

    @validator("target_folder")
    def validate_target_folder(cls, v, values):
        if values.get("action") == "move" and not v:
            raise ValueError("Target folder is required for move action")
        return v

    @validator("labels")
    def validate_labels(cls, v, values):
        if values.get("action") in ["label", "unlabel"] and not v:
            raise ValueError("Labels are required for label/unlabel actions")
        return v

class EmailAttachment(BaseModel):
    """Schema for email attachments"""
    id: str
    filename: str
    content_type: str
    size: int
    storage_path: str
    is_inline: bool = False
    content_id: Optional[str] = None
    checksum: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
