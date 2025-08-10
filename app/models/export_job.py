import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    BigInteger,
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


class ExportStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ExportFormat(str, enum.Enum):
    MP4 = "MP4"
    MOV = "MOV"
    AVI = "AVI"
    WEBM = "WEBM"
    MKV = "MKV"


class ExportQuality(str, enum.Enum):
    LOW = "LOW"           # 720p
    MEDIUM = "MEDIUM"     # 1080p
    HIGH = "HIGH"         # 1440p
    ULTRA = "ULTRA"       # 4K


class ExportJob(Base):
    __tablename__ = "export_jobs"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Foreign keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Export configuration
    status = Column(Enum(ExportStatus, native_enum=False), nullable=True)
    format = Column(Enum(ExportFormat, native_enum=False), nullable=False)
    quality = Column(Enum(ExportQuality, native_enum=False), nullable=False)

    # Output specifications
    output_width = Column(Integer, nullable=True)
    output_height = Column(Integer, nullable=True)
    output_fps = Column(Float, nullable=True)
    output_bitrate = Column(Integer, nullable=True)

    # File information
    output_filename = Column(String, nullable=True)
    output_file_path = Column(String(500), nullable=True)
    output_file_size = Column(BigInteger, nullable=True)

    # Export parameters
    export_settings = Column(JSON, nullable=True)  # Additional export parameters
    progress_percentage = Column(Float, default=0.0, nullable=True)

    # Processing metadata
    processing_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Any = relationship("Project", back_populates="export_jobs")

    def __repr__(self) -> str:
        return f"<ExportJob(id={self.id}, name='{self.name}', status={self.status}, format={self.format})>"
