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
from app.domain.enums import VideoCodec, VideoStatus

if TYPE_CHECKING:
    pass


class Video(Base):
    __tablename__ = "videos"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # Foreign keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # File properties
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)

    # Video properties
    duration = Column(Float, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    fps = Column(Float, nullable=False)
    codec = Column(Enum(VideoCodec, native_enum=False), nullable=False)
    bitrate = Column(Integer, nullable=True)

    # Processing status
    status = Column(Enum(VideoStatus, native_enum=False), nullable=True)

    # Analysis data
    analysis_data = Column(JSON, nullable=True)
    scene_cuts = Column(JSON, nullable=True)
    audio_analysis = Column(JSON, nullable=True)
    face_detections = Column(JSON, nullable=True)
    emotion_analysis = Column(JSON, nullable=True)
    text_detections = Column(JSON, nullable=True)
    object_detections = Column(JSON, nullable=True)

    # Processing metadata
    processing_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Any = relationship("User", back_populates="videos")
    project: Any = relationship("Project", back_populates="videos")

    def __repr__(self) -> str:
        return f"<Video(id={self.id}, filename='{self.filename}', status={self.status})>"
