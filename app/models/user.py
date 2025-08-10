from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, Integer, String, text
from sqlalchemy.orm import relationship

from app.db.base import Base

if TYPE_CHECKING:
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)

    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")  # type: ignore
    audios = relationship("Audio", back_populates="user", cascade="all, delete-orphan")  # type: ignore
    projects = relationship(
        "Project", back_populates="user", cascade="all, delete-orphan"
    )  # type: ignore

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, email='{self.email}', "
            f"is_active={self.is_active}, is_superuser={self.is_superuser})>"
        )
