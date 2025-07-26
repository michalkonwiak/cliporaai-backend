from typing import TYPE_CHECKING
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Float,
    DateTime,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SqlEnum

from enum import Enum

from app.db.base import Base

if TYPE_CHECKING:
    pass


class ProjectType(Enum):
    DYNAMIC = "dynamic"
    CINEMATIC = "cinematic"
    DOCUMENTARY = "documentary"
    SOCIAL = "social"
    CUSTOM = "custom"


class ProjectStatus(Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPORTED = "exported"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="projects")  # type: ignore

    project_type = Column(
        SqlEnum(ProjectType, native_enum=False), default=ProjectType.DYNAMIC
    )
    status = Column(
        SqlEnum(ProjectStatus, native_enum=False), default=ProjectStatus.DRAFT
    )

    timeline_data = Column(JSON, nullable=True)

    total_duration = Column(Float, default=0.0)
    processing_progress = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    videos = relationship(
        "Video", back_populates="project", cascade="all, delete-orphan"
    )  # type: ignore
    cutting_plans = relationship(
        "CuttingPlan", back_populates="project", cascade="all, delete-orphan"
    )  # type: ignore

    def __repr__(self) -> str:
        status_value = (
            self.status.value
            if self.status and hasattr(self.status, "value")
            else "None"
        )
        return f"<Project(id={self.id}, name={self.name}, status={status_value})>"
