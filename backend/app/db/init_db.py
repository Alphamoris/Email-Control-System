import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.core import auth
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import create_access_token

logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    """Initialize database with required initial data."""
    try:
        # Create super user if it doesn't exist already 
        user = db.query(User).filter(User.email == settings.FIRST_SUPERUSER).first()
        if not user:
            logger.info(f"Creating superuser: {settings.FIRST_SUPERUSER}")
            user_in = UserCreate(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                full_name="Initial Super User",
                is_superuser=True,
            )
            user = User(
                email=user_in.email,
                hashed_password=auth.get_password_hash(user_in.password),
                full_name=user_in.full_name,
                is_superuser=True,
                is_active=True,
                timezone="UTC",
                language="en",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Create access token for superuser
            access_token = create_access_token(
                data={"sub": user.email, "is_superuser": True}
            )
            logger.info(f"Superuser created successfully. Access token: {access_token}")
        else:
            logger.info("Superuser already exists")

        # Initialize other required data
        init_required_data(db)
        
        logger.info("Database initialization completed successfully")
    except SQLAlchemyError as e:
        logger.error(f"Database initialization failed: {str(e)}")
        db.rollback()
        raise

def init_required_data(db: Session) -> None:
    """Initialize other required data in the database."""
    try:
        # Add any other required initial data here
        # For example:
        # - Default email templates
        # - System settings
        # - Default folders
        pass
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize required data: {str(e)}")
        db.rollback()
        raise
