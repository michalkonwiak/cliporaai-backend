from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SqlEnum
from enum import Enum

from app.db.base import Base

if TYPE_CHECKING:
    pass


class CuttingPlanStatus(Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CuttingPlan(Base):
    __tablename__ = "cutting_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Core cutting data
    cuts_data = Column(JSON, nullable=False)  # List of cut segments with metadata
    export_settings = Column(JSON, nullable=True)  # Export configuration

    # AI metadata
    is_ai_generated = Column(Boolean, default=True)
    confidence_score = Column(Float, nullable=True)  # 0-1 AI confidence
    ai_model_version = Column(String(50), nullable=True)  # Track which AI model version was used

    # Status and progress
    status = Column(SqlEnum(CuttingPlanStatus, native_enum=False), default=CuttingPlanStatus.DRAFT)
    processing_progress = Column(Float, default=0.0)  # 0-100
    estimated_output_duration = Column(Float, nullable=True)  # seconds

    # Error handling
    error_message = Column(Text, nullable=True)

    # Relations
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="cutting_plans")  # type: ignore
    video = relationship("Video", back_populates="cutting_plans")  # type: ignore
    created_by = relationship("User")  # type: ignore
    export_jobs = relationship("ExportJob", back_populates="cutting_plan", cascade="all, delete-orphan")  # type: ignore

    def __repr__(self) -> str:
        status_value = self.status.value if self.status and hasattr(self.status, 'value') else "None"
        return f"<CuttingPlan(id={self.id}, name={self.name}, status={status_value})>"

    @property
    def total_cuts(self) -> int:
        """Return total number of cuts in this plan"""
        if not self.cuts_data:
            return 0
        return len(self.cuts_data)

    @property
    def total_segments_duration(self) -> float:
        """Calculate total duration of all segments in seconds"""
        if not self.cuts_data or not isinstance(self.cuts_data, list):
            return 0.0

        total = 0.0
        for cut in self.cuts_data:
            if isinstance(cut, dict) and 'start_time' in cut and 'end_time' in cut:
                start_time = float(cut['start_time'])
                end_time = float(cut['end_time'])
                total += end_time - start_time
        return total

    def get_high_confidence_cuts(self, threshold: float = 0.8) -> list:
        """Return cuts with confidence above threshold"""
        if not self.cuts_data or not isinstance(self.cuts_data, list):
            return []

        return [
            cut for cut in self.cuts_data
            if isinstance(cut, dict) and cut.get('confidence', 0) >= threshold
        ]
