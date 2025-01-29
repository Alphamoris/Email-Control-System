# Import all the models here so that Alembic can discover them
from app.db.base_class import Base
from app.models.user import User
from app.models.email_account import EmailAccount
from app.models.email import Email
from app.models.attachment import Attachment
from app.models.folder import Folder
from app.models.label import Label
from app.models.contact import Contact



# Make sure all models are imported before initializing Alembic
__all__ = [
    "Base",
    "User",
    "EmailAccount",
    "Email",
    "Attachment",
    "Folder",
    "Label",
    "Contact"
]
