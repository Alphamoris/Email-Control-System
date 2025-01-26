from typing import Any
from datetime import datetime
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func

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

    def __repr__(self) -> str:
        """String representation of the model."""
        attrs = []
        for col in self.__table__.columns:
            value = getattr(self, col.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            attrs.append(f"{col.name}={value!r}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"

                setattr(self, key, value)
    
    @classmethod
    def from_dict(cls, data: dict) -> Any:
        """Create model instance from dictionary."""
        return cls(**{
            key: value for key, value in data.items()
            if hasattr(cls, key)
        })
