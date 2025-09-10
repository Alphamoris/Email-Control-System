





import logging
import sys
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.config import settings
from app.models.user import User
from app.core.auth import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_superuser(db: Session) -> None:
    """Create a superuser if it doesn't exist."""
    try:
        # Check if superuser already exists
        user = db.query(User).filter(User.email == settings.FIRST_SUPERUSER).first()
        if user:
            logger.info(f"Superuser {settings.FIRST_SUPERUSER} already exists")
            return

        # Create superuser
        user = User(
            email=settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            full_name="System Administrator",
            is_superuser=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        logger.info(f"Superuser {settings.FIRST_SUPERUSER} created successfully")

    except Exception as e:
        logger.error(f"Error creating superuser: {str(e)}")
        db.rollback()
        sys.exit(1)

def main() -> None:
    logger.info("Creating superuser...")
    db = SessionLocal()
    try:
        create_superuser(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()
