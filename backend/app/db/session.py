from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Create synchronous database engine
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    echo=settings.ENVIRONMENT == "development",
)

# Create asynchronous database engine
async_engine = create_async_engine(
    settings.ASYNC_SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    echo=settings.ENVIRONMENT == "development",
)

# Add engine event listeners
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    logger.info("New database connection established")

@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug("Database connection checked out from pool")

@event.listens_for(engine, "checkin")
def checkin(dbapi_connection, connection_record):
    logger.debug("Database connection returned to pool")

# Create session factories
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
    class_=Session
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session without dependency injection."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def check_db_connection() -> bool:
    """Check if database connection is working."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

def init_db() -> None:
    """Initialize database tables."""
    from app.db.base import Base  # Import here to avoid circular imports
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise
