from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    preferences = Column(JSON, nullable=True)  # Store user preferences
    avatar_url = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    language = Column(String, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_active_at = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    email_accounts = relationship("EmailAccount", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def is_locked(self) -> bool:
        """Check if the user account is locked."""
        if not self.locked_until:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) <= self.locked_until

    def increment_failed_login(self) -> None:
        """Increment failed login attempts and lock account if necessary."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            from datetime import datetime, timezone, timedelta
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)

    def reset_failed_login(self) -> None:
        """Reset failed login attempts and unlock account."""
        self.failed_login_attempts = 0
        self.locked_until = None

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        from datetime import datetime, timezone
        self.last_login_at = datetime.now(timezone.utc)
        self.reset_failed_login()

    def update_last_active(self) -> None:
        """Update last active timestamp."""
        from datetime import datetime, timezone
        self.last_active_at = datetime.now(timezone.utc)
