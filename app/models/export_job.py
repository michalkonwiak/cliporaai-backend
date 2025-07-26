from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SqlEnum
from enum import Enum

from app.db.base import Base

if TYPE_CHECKING:
    pass


class ExportStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFormat(Enum):
    MP4 = "mp4"
    MOV = "mov"
    WEBM = "webm"
    AVI = "avi"


class ExportQuality(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class ExportJob(Base):
    __tablename__ = "export_jobs"

    id = Column(Integer, primary_key=True, index=True)

    # Export settings
    output_format = Column(SqlEnum(ExportFormat, native_enum=False), nullable=False, default=ExportFormat.MP4)
    resolution = Column(String(20), nullable=False)  # "1920x1080", "1280x720", "3840x2160"
    quality = Column(SqlEnum(ExportQuality, native_enum=False), nullable=False, default=ExportQuality.HIGH)
    fps = Column(Float, nullable=True)  # Target FPS for export
    bitrate = Column(Integer, nullable=True)  # Target bitrate in kbps

    # Output information
    output_filename = Column(String(255), nullable=True)
    output_path = Column(String(500), nullable=True)
    output_size = Column(BigInteger, nullable=True)  # File size in bytes
    download_url = Column(String(500), nullable=True)  # URL for downloading the exported file

    # Progress and status tracking
    status = Column(SqlEnum(ExportStatus, native_enum=False), default=ExportStatus.QUEUED)
    progress = Column(Float, default=0.0)  # 0-100 percentage
    current_step = Column(String(100), nullable=True)  # "analyzing", "cutting", "encoding", "finalizing"

    # Performance metrics
    processing_time = Column(Float, nullable=True)  # Total processing time in seconds
    estimated_completion = Column(DateTime(timezone=True), nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Relations
    cutting_plan_id = Column(Integer, ForeignKey("cutting_plans.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # When the exported file expires

    # Relationships
    cutting_plan = relationship("CuttingPlan", back_populates="export_jobs")  # type: ignore

    def __repr__(self) -> str:
        status_value = self.status.value if self.status and hasattr(self.status, 'value') else "None"
        return f"<ExportJob(id={self.id}, status={status_value}, progress={self.progress}%)>"

    @property
    def is_completed(self) -> bool:
        """Check if export job is completed successfully"""
        return self.status == ExportStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if export job failed"""
        return self.status == ExportStatus.FAILED

    @property
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.is_failed and self.retry_count < self.max_retries

    @property
    def output_size_formatted(self) -> str:
        """Return human-readable file size"""
        if not self.output_size:
            return "Unknown"

        size = float(self.output_size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @property
    def resolution_width(self) -> int:
        """Extract width from resolution string"""
        if not self.resolution:
            return 0
        return int(self.resolution.split('x')[0])

    @property
    def resolution_height(self) -> int:
        """Extract height from resolution string"""
        if not self.resolution:
            return 0
        return int(self.resolution.split('x')[1])
