import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base

if TYPE_CHECKING:
    pass


class ProjectType(str, enum.Enum):
    DYNAMIC = "DYNAMIC"
    CINEMATIC = "CINEMATIC"
    DOCUMENTARY = "DOCUMENTARY"
    SOCIAL = "SOCIAL"
    CUSTOM = "CUSTOM"


class ProjectStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPORTED = "EXPORTED"


class Project(Base):
    __tablename__ = "projects"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Project configuration
    project_type = Column(Enum(ProjectType, native_enum=False), nullable=True)
    status = Column(Enum(ProjectStatus, native_enum=False), nullable=True)
    timeline_data = Column(JSON, nullable=True)
    total_duration = Column(Float, nullable=True)
    processing_progress = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Any = relationship("User", back_populates="projects")
    videos: Any = relationship(
        "Video", back_populates="project", cascade="all, delete-orphan"
    )
    audios: Any = relationship(
        "Audio", back_populates="project", cascade="all, delete-orphan"
    )
    cutting_plans: Any = relationship(
        "CuttingPlan", back_populates="project", cascade="all, delete-orphan"
    )
    export_jobs: Any = relationship(
        "ExportJob", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', status={self.status})>"
