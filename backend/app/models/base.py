from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, Integer, DateTime, func, event
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

@as_declarative()
class Base:
    """Base class for all database models."""
    
    id: Any
    __name__: str
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate tablename from class name."""
        return cls.__name__.lower()
    
    # Common columns for all models
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Base":
        """Create model instance from dictionary."""
        return cls(**{
            k: v for k, v in data.items()
            if k in cls.__table__.columns.keys()
        })

    def update(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

@event.listens_for(Base, 'before_update', propagate=True)
def timestamp_before_update(mapper, connection, target):
    """Update timestamp before update."""
    target.updated_at = datetime.utcnow()

class CRUDMixin:
    """Mixin that adds convenience methods for CRUD operations."""

    @classmethod
    def create(cls, db: Session, **kwargs: Any) -> Any:
        """Create a new record and save it the database."""
        try:
            instance = cls(**kwargs)
            db.add(instance)
            db.flush()
            return instance
        except Exception as e:
            logger.error(f"Error creating {cls.__name__}: {str(e)}")
            raise

    @classmethod
    def get(cls, db: Session, id: int) -> Any:
        """Get record by ID."""
        return db.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_multi(
        cls,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        **filters: Any
    ) -> list[Any]:
        """Get multiple records."""
        query = db.query(cls)
        for field, value in filters.items():
            if hasattr(cls, field):
                query = query.filter(getattr(cls, field) == value)
        return query.offset(skip).limit(limit).all()

    def update_from_dict(
        self,
        db: Session,
        data: Dict[str, Any],
        commit: bool = True
    ) -> Any:
        """Update record from dictionary."""
        for field, value in data.items():
            if hasattr(self, field):
                setattr(self, field, value)
        if commit:
            db.commit()
            db.refresh(self)
        return self

    def delete(self, db: Session) -> None:
        """Delete record."""
        db.delete(self)
        db.commit()

class TimestampMixin:
    pass

class BaseModel(Base, TimestampMixin):
    __abstract__ = True
