from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declared_attr
from app.db.base_class import Base

class TimestampMixin:
    @declared_attr
    def created_at(cls) -> Any:
        return Column(DateTime, nullable=False, default=datetime.utcnow)

    @declared_attr
    def updated_at(cls) -> Any:
        return Column(
            DateTime,
            nullable=False,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
        )

class BaseModel(Base, TimestampMixin):
    __abstract__ = True

    def to_dict(self) -> dict:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    @classmethod
    def from_dict(cls, data: dict) -> Any:
        """Create model instance from dictionary."""
        return cls(**{
            key: value
            for key, value in data.items()
            if key in cls.__table__.columns
        })
