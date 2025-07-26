import enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    BigInteger,
    ForeignKey,
    JSON,
)
from sqlalchemy.types import Enum as SqlEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base

if TYPE_CHECKING:
    pass


class VideoStatus(enum.Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class VideoCodec(enum.Enum):
    H264 = "h264"
    H265 = "h265"
    VP9 = "vp9"
    AV1 = "av1"


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # Ownership
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # File details
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)

    # Video technical specs
    duration = Column(Float, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    fps = Column(Float, nullable=False)
    codec = Column(SqlEnum(VideoCodec, native_enum=False), nullable=False)
    bitrate = Column(Integer, nullable=True)

    # AI Analysis results
    status = Column(
        SqlEnum(VideoStatus, native_enum=False), default=VideoStatus.UPLOADING
    )
    analysis_data = Column(JSON, default=dict)

    # AI Analysis components
    scene_cuts = Column(JSON, default=list)
    audio_analysis = Column(JSON, default=dict)
    face_detections = Column(JSON, default=list)
    emotion_analysis = Column(JSON, default=list)
    text_detections = Column(JSON, default=list)
    object_detections = Column(JSON, default=list)

    # Processing metadata
    processing_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    analyzed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="videos")  # type: ignore
    user = relationship("User", back_populates="videos")  # type: ignore
    cutting_plans = relationship(
        "CuttingPlan", back_populates="video", cascade="all, delete-orphan"
    )  # type: ignore

    def __repr__(self) -> str:
        status_value = (
            self.status.value
            if self.status and hasattr(self.status, "value")
            else "None"
        )
        return f"<Video(id={self.id}, filename={self.filename}, status={status_value})>"
