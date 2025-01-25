from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session, joinedload
from app.models.email import Email
from app.models.email_account import EmailAccount
from app.schemas.email import EmailCreate, EmailUpdate, EmailFilter
from app.services.storage_service import StorageService
from app.services.gmail_service import GmailService
from app.services.outlook_service import OutlookService
from app.core.config import settings
from app.core.security import verify_rate_limit
from datetime import datetime, timedelta
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = StorageService()
        self.gmail_service = GmailService()
        self.outlook_service = OutlookService()

    async def list_emails(
        self,
        user_id: int,
        filter_params: EmailFilter,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Email], int]:
        """List emails with filtering and pagination"""
        query = self.db.query(Email).join(EmailAccount).filter(
            EmailAccount.user_id == user_id
        )

        # Apply filters
        if filter_params.folder:
            query = query.filter(Email.folder == filter_params.folder)
        if filter_params.is_read is not None:
            query = query.filter(Email.is_read == filter_params.is_read)
        if filter_params.is_starred is not None:
            query = query.filter(Email.is_starred == filter_params.is_starred)
        if filter_params.account_id:
            query = query.filter(Email.account_id == filter_params.account_id)
        if filter_params.labels:
            query = query.filter(Email.labels.overlap(filter_params.labels))
        if filter_params.from_date:
            query = query.filter(Email.received_at >= filter_params.from_date)
        if filter_params.to_date:
            query = query.filter(Email.received_at <= filter_params.to_date)
        if filter_params.has_attachments is not None:
            if filter_params.has_attachments:
                query = query.filter(Email.attachments != None)
            else:
                query = query.filter(Email.attachments == None)
        
        # Apply search if provided
        if filter_params.search:
            search_filter = or_(
                Email.subject.ilike(f"%{filter_params.search}%"),
                Email.content.ilike(f"%{filter_params.search}%"),
                Email.sender.ilike(f"%{filter_params.search}%"),
                func.array_to_string(Email.recipients, ',').ilike(f"%{filter_params.search}%")
            )
            query = query.filter(search_filter)

        # Get total count
        total = query.count()

        # Apply sorting
        if filter_params.sort_desc:
            query = query.order_by(desc(getattr(Email, filter_params.sort_by)))
        else:
            query = query.order_by(getattr(Email, filter_params.sort_by))

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        return query.all(), total

    async def send_email(self, account: EmailAccount, email_data: EmailCreate) -> Email:
        """Send email using the appropriate service"""
        try:
            # Check rate limit
            if not await self.check_rate_limit(account.user_id):
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Maximum {settings.RATE_LIMIT_PER_USER} emails per hour."
                )

            # Process attachments
            attachments = []
            if email_data.attachments:
                attachments = await self.storage.get_attachments(email_data.attachments)

            # Send email using appropriate service
            if account.account_type == "gmail":
                message_id = await self.gmail_service.send_email(account, email_data, attachments)
            elif account.account_type == "outlook":
                message_id = await self.outlook_service.send_email(account, email_data, attachments)
            else:
                message_id = await self._send_smtp_email(account, email_data, attachments)

            # Save sent email
            email = self._save_sent_email(account, email_data, message_id)
            
            # Update account stats
            account.last_sent_at = datetime.utcnow()
            account.total_sent += 1
            self.db.commit()

            return email

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def fetch_emails(self, account: EmailAccount, sync_all: bool = False) -> Dict[str, Any]:
        """Fetch emails from the email provider"""
        try:
            # Update sync status
            account.sync_status = "syncing"
            account.error_message = None
            self.db.commit()

            # Fetch emails using appropriate service
            if account.account_type == "gmail":
                result = await self.gmail_service.fetch_emails(account, sync_all)
            elif account.account_type == "outlook":
                result = await self.outlook_service.fetch_emails(account, sync_all)
            else:
                result = await self._fetch_imap_emails(account, sync_all)

            # Update account sync info
            account.last_sync_at = datetime.utcnow()
            account.sync_status = "success"
            self.db.commit()

            return result

        except Exception as e:
            logger.error(f"Failed to fetch emails: {str(e)}")
            account.sync_status = "error"
            account.error_message = str(e)
            self.db.commit()
            raise HTTPException(status_code=500, detail=str(e))

    async def update_email(self, email: Email, update_data: EmailUpdate) -> Email:
        """Update email properties"""
        try:
            # Update remote email if needed
            if update_data.folder and update_data.folder != email.folder:
                if email.account.account_type == "gmail":
                    await self.gmail_service.move_email(email, update_data.folder)
                elif email.account.account_type == "outlook":
                    await self.outlook_service.move_email(email, update_data.folder)
                else:
                    await self._move_imap_email(email, update_data.folder)

            # Update local email
            for field, value in update_data.dict(exclude_unset=True).items():
                setattr(email, field, value)

            email.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(email)

            return email

        except Exception as e:
            logger.error(f"Failed to update email: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_email(self, email: Email, permanent: bool = False) -> None:
        """Delete an email"""
        try:
            if permanent:
                # Delete from remote
                if email.account.account_type == "gmail":
                    await self.gmail_service.delete_email(email)
                elif email.account.account_type == "outlook":
                    await self.outlook_service.delete_email(email)
                else:
                    await self._delete_imap_email(email)

                # Delete attachments
                if email.attachments:
                    await self.storage.delete_attachments(email.attachments)

                # Delete from database
                self.db.delete(email)
            else:
                # Move to trash
                email.folder = "trash"
                email.updated_at = datetime.utcnow()

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to delete email: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def perform_bulk_action(self, user_id: int, action_data: EmailBulkAction) -> Dict[str, Any]:
        """Perform bulk actions on emails"""
        success_count = 0
        failed_count = 0
        failed_ids = []

        emails = self.db.query(Email).join(EmailAccount).filter(
            and_(
                Email.id.in_(action_data.email_ids),
                EmailAccount.user_id == user_id
            )
        ).all()

        for email in emails:
            try:
                if action_data.action in ["mark_read", "mark_unread"]:
                    email.is_read = action_data.action == "mark_read"
                elif action_data.action in ["star", "unstar"]:
                    email.is_starred = action_data.action == "star"
                elif action_data.action == "move":
                    await self.update_email(email, EmailUpdate(folder=action_data.target_folder))
                elif action_data.action == "delete":
                    await self.delete_email(email)
                elif action_data.action == "label":
                    email.labels = list(set(email.labels or []) | set(action_data.labels))
                elif action_data.action == "unlabel":
                    email.labels = list(set(email.labels or []) - set(action_data.labels))

                success_count += 1
            except Exception as e:
                logger.error(f"Failed to perform {action_data.action} on email {email.id}: {str(e)}")
                failed_count += 1
                failed_ids.append(email.id)

        self.db.commit()

        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_ids": failed_ids
        }

    async def check_rate_limit(self, user_id: int) -> bool:
        """Check if user has exceeded email sending rate limit"""
        key = f"email_rate_limit:{user_id}"
        return await verify_rate_limit(key, settings.RATE_LIMIT_PER_USER, 3600)  # 1 hour window

    def _save_sent_email(self, account: EmailAccount, email_data: EmailCreate, message_id: str) -> Email:
        """Save sent email to database"""
        email = Email(
            account_id=account.id,
            message_id=message_id,
            subject=email_data.subject,
            content=email_data.content,
            html_content=email_data.html_content,
            sender=account.email,
            recipients=email_data.recipients,
            cc=email_data.cc,
            bcc=email_data.bcc,
            folder="sent",
            is_read=True,
            received_at=datetime.utcnow(),
            attachments=[{"id": id} for id in (email_data.attachments or [])]
        )
        self.db.add(email)
        self.db.commit()
        self.db.refresh(email)
        return email

    async def _send_smtp_email(
        self,
        account: EmailAccount,
        email_data: EmailCreate,
        attachments: List[Dict[str, Any]]
    ) -> str:
        """Send email using SMTP"""
        message = MIMEMultipart("alternative")
        message["Subject"] = email_data.subject
        message["From"] = account.email
        message["To"] = ", ".join(email_data.recipients)
        
        if email_data.cc:
            message["Cc"] = ", ".join(email_data.cc)
        if email_data.bcc:
            message["Bcc"] = ", ".join(email_data.bcc)

        # Add text content
        if email_data.content:
            message.attach(MIMEText(email_data.content, "plain"))
        
        # Add HTML content if provided
        if email_data.html_content:
            message.attach(MIMEText(email_data.html_content, "html"))

        # Add attachments
        for attachment in attachments:
            with open(attachment["path"], "rb") as f:
                part = MIMEApplication(f.read(), _subtype=attachment["content_type"].split("/")[1])
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=attachment["filename"]
                )
                message.attach(part)

        try:
            smtp = aiosmtplib.SMTP(hostname=account.smtp_host, port=account.smtp_port, use_tls=True)
            await smtp.connect()
            await smtp.login(account.email, account.refresh_token)
            await smtp.send_message(message)
            await smtp.quit()
            return f"smtp_{datetime.utcnow().timestamp()}"
        except Exception as e:
            raise Exception(f"SMTP error: {str(e)}")

    async def _fetch_imap_emails(self, account: EmailAccount, sync_all: bool = False) -> Dict[str, Any]:
        """Fetch emails using IMAP"""
        # Implementation for IMAP email fetching
        raise NotImplementedError("IMAP email fetching not implemented yet")

    async def _move_imap_email(self, email: Email, folder: str) -> None:
        """Move email using IMAP"""
        # Implementation for IMAP email moving
        raise NotImplementedError("IMAP email moving not implemented yet")

    async def _delete_imap_email(self, email: Email) -> None:
        """Delete email using IMAP"""
        # Implementation for IMAP email deletion
        raise NotImplementedError("IMAP email deletion not implemented yet")
