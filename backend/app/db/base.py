# Import all models here for Alembic autogeneration support
from app.db.base_class import Base
from app.models.user import User
from app.models.email_account import EmailAccount
from app.models.email import Email, Attachment
