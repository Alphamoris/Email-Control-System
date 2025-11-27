


from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("email_accounts.id"), nullable=False)
    message_id = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=True)
    sender = Column(String, nullable=False)
    recipients = Column(JSON, nullable=False)
    cc = Column(JSON, nullable=True)
    bcc = Column(JSON, nullable=True)
    content = Column(Text, nullable=True)
    html_content = Column(Text, nullable=True)
    received_at = Column(DateTime, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    is_starred = Column(Boolean, nullable=False, default=False)
    folder = Column(String, nullable=False, default="inbox")
    priority = Column(Integer, nullable=False, default=0)
    spam_score = Column(Float, nullable=True)
    thread_id = Column(String, nullable=True, index=True)
    in_reply_to = Column(String, nullable=True)
    references = Column(JSON, nullable=True)
    labels = Column(JSON, nullable=True)

    # Relationships
    account = relationship("EmailAccount", back_populates="emails")
    attachments = relationship("Attachment", back_populates="email", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Email {self.subject}>"

class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)  # Size in bytes
    storage_path = Column(String, nullable=False)
    is_inline = Column(Boolean, nullable=False, default=False)
    content_id = Column(String, nullable=True)  # For inline attachments
    checksum = Column(String, nullable=True)  # For deduplication

    # Relationships
    email = relationship("Email", back_populates="attachments")

    def __repr__(self):
        return f"<Attachment {self.filename}>"
