from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum
from datetime import datetime

class AccountType(str, enum.Enum):
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    IMAP = "imap"

class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    account_type = Column(Enum(AccountType))
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_sync_at = Column(DateTime, nullable=True)
    sync_status = Column(String, nullable=True)  # e.g., "syncing", "failed", "success"
    error_message = Column(String, nullable=True)
    settings = Column(JSON, nullable=True)  # Store account-specific settings
    capabilities = Column(JSON, nullable=True)  # Store provider capabilities
    quota = Column(JSON, nullable=True)  # Store quota information
    
    # For IMAP accounts
    imap_host = Column(String, nullable=True)
    imap_port = Column(Integer, nullable=True)
    smtp_host = Column(String, nullable=True)
    smtp_port = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="email_accounts")
    emails = relationship("Email", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EmailAccount {self.email}>"

    @property
    def is_token_expired(self) -> bool:
        """Check if the access token is expired."""
        if not self.token_expires_at:
            return True
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) >= self.token_expires_at

    @property
    def needs_refresh(self) -> bool:
        """Check if the account needs token refresh."""
        if not self.refresh_token or not self.token_expires_at:
            return False
        from datetime import datetime, timezone, timedelta
        # Refresh if token expires in less than 5 minutes
        return datetime.now(timezone.utc) + timedelta(minutes=5) >= self.token_expires_at
