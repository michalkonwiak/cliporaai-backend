from typing import TYPE_CHECKING, Any
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Float,
    JSON,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy import text
from datetime import datetime

from app.db.base import Base

if TYPE_CHECKING:
    pass


class CuttingPlanStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CuttingPlan(Base):
    __tablename__ = "cutting_plans"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Foreign keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Plan configuration
    status = Column(Enum(CuttingPlanStatus, native_enum=False), nullable=True)
    plan_data = Column(JSON, nullable=True)  # Contains cutting instructions, segments, etc.
    total_duration = Column(Float, nullable=True)
    estimated_output_duration = Column(Float, nullable=True)

    # AI/ML configuration
    cutting_strategy = Column(String, nullable=True)  # "DYNAMIC", "HIGHLIGHT_BASED", etc.
    ai_parameters = Column(JSON, nullable=True)  # AI model parameters

    # Processing metadata
    processing_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Any = relationship("Project", back_populates="cutting_plans")

    def __repr__(self) -> str:
        return f"<CuttingPlan(id={self.id}, name='{self.name}', status={self.status})>"
