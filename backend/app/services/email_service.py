from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from app.models.email import Email
from app.models.email_account import EmailAccount, AccountType
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
from app.core.exceptions import EmailNotFoundError, StorageError
import logging
from typing import AsyncGenerator

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
        try:
            query = self.db.query(Email).join(EmailAccount).filter(
                EmailAccount.user_id == user_id
            ).options(joinedload(Email.attachments))

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
            if filter_params.search:
                search_term = f"%{filter_params.search}%"
                query = query.filter(
                    or_(
                        Email.subject.ilike(search_term),
                        Email.content.ilike(search_term),
                        Email.sender.ilike(search_term),
                    )
                )

            # Get total count
            total = query.count()

            # Apply sorting and pagination
            query = query.order_by(
                desc(Email.received_at) if filter_params.sort_desc else Email.received_at
            )
            query = query.offset((page - 1) * page_size).limit(page_size)

            return query.all(), total

        except SQLAlchemyError as e:
            logger.error(f"Database error in list_emails: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch emails"
            )

    async def send_email(self, user_id: int, email_data: EmailCreate) -> Email:
        """Send a new email"""
        try:
            # Get the email account
            account = self.db.query(EmailAccount).filter(
                and_(
                    EmailAccount.id == email_data.account_id,
                    EmailAccount.user_id == user_id
                )
            ).first()

            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Email account not found"
                )

            # Create email object
            email = Email(
                account_id=account.id,
                subject=email_data.subject,
                recipients=email_data.recipients,
                cc=email_data.cc,
                bcc=email_data.bcc,
                content=email_data.content,
                html_content=email_data.html_content,
                priority=email_data.priority or 0,
                folder="sent",
                received_at=datetime.utcnow(),
                is_read=True,
            )

            # Handle attachments
            if email_data.attachments:
                for attachment_id in email_data.attachments:
                    attachment = self.storage.get_attachment(attachment_id)
                    if attachment:
                        email.attachments.append(attachment)

            # Send email based on account type
            if account.account_type == AccountType.GMAIL:
                await self.gmail_service.send_email(account, email)
            elif account.account_type == AccountType.OUTLOOK:
                await self.outlook_service.send_email(account, email)
            else:
                await self._send_smtp_email(account, email)

            # Save to database
            self.db.add(email)
            self.db.commit()
            self.db.refresh(email)

            return email

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error in send_email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email"
            )
        except StorageError as e:
            logger.error(f"Storage error in send_email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process attachments"
            )
        except Exception as e:
            logger.error(f"Error in send_email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email"
            )

    async def fetch_new_emails(
        self,
        user_id: int,
        account_id: int,
        sync_all: bool = False
    ) -> AsyncGenerator[Email, None]:
        """Fetch new emails from the provider"""
        try:
            account = self.db.query(EmailAccount).filter(
                and_(
                    EmailAccount.id == account_id,
                    EmailAccount.user_id == user_id
                )
            ).first()

            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Email account not found"
                )

            # Update sync status
            account.sync_status = "syncing"
            self.db.commit()

            try:
                if account.account_type == AccountType.GMAIL:
                    async for email in self.gmail_service.fetch_emails(account, sync_all):
                        yield email
                elif account.account_type == AccountType.OUTLOOK:
                    async for email in self.outlook_service.fetch_emails(account, sync_all):
                        yield email

                # Update sync status
                account.sync_status = "success"
                account.last_sync_at = datetime.utcnow()
                self.db.commit()

            except Exception as e:
                account.sync_status = "failed"
                account.error_message = str(e)
                self.db.commit()
                raise

        except SQLAlchemyError as e:
            logger.error(f"Database error in fetch_new_emails: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch new emails"
            )

    async def _send_smtp_email(self, account: EmailAccount, email: Email) -> None:
        """Send email using SMTP"""
        if not account.smtp_host or not account.smtp_port:
            raise ValueError("SMTP configuration missing")

        message = MIMEMultipart()
        message["From"] = account.email
        message["To"] = ", ".join(email.recipients)
        if email.cc:
            message["Cc"] = ", ".join(email.cc)
        message["Subject"] = email.subject or ""

        # Add body
        if email.html_content:
            message.attach(MIMEText(email.html_content, "html"))
        else:
            message.attach(MIMEText(email.content or "", "plain"))

        # Add attachments
        for attachment in email.attachments:
            with open(attachment.storage_path, "rb") as f:
                part = MIMEApplication(f.read(), _subtype=attachment.content_type.split("/")[1])
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=attachment.filename
                )
                message.attach(part)

        # Send email
        async with aiosmtplib.SMTP(
            hostname=account.smtp_host,
            port=account.smtp_port,
            use_tls=True
        ) as smtp:
            await smtp.send_message(message)

    async def update_email(self, email: Email, update_data: EmailUpdate) -> Email:
        """Update email properties"""
        try:
            # Update remote email if needed
            if update_data.folder and update_data.folder != email.folder:
                if email.account.account_type == AccountType.GMAIL:
                    await self.gmail_service.move_email(email, update_data.folder)
                elif email.account.account_type == AccountType.OUTLOOK:
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
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    async def delete_email(self, email: Email, permanent: bool = False) -> None:
        """Delete an email"""
        try:
            if permanent:
                # Delete from remote
                if email.account.account_type == AccountType.GMAIL:
                    await self.gmail_service.delete_email(email)
                elif email.account.account_type == AccountType.OUTLOOK:
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
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

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
