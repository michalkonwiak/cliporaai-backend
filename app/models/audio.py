from typing import TYPE_CHECKING, Any
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
    BigInteger,
)
from sqlalchemy.orm import relationship
from sqlalchemy import text
from datetime import datetime

from app.db.base import Base
from app.domain.enums import AudioCodec, AudioStatus

if TYPE_CHECKING:
    pass


class Audio(Base):
    __tablename__ = "audios"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # Foreign keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # File properties
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)

    # Audio properties
    duration = Column(Float, nullable=False)
    codec = Column(Enum(AudioCodec, native_enum=False), nullable=False)
    bitrate = Column(Integer, nullable=True)
    sample_rate = Column(Integer, nullable=False)
    channels = Column(Integer, nullable=False)

    # Processing status
    status = Column(Enum(AudioStatus, native_enum=False), nullable=True)

    # Analysis data
    analysis_data = Column(JSON, nullable=True)
    transcription = Column(Text, nullable=True)
    silence_detection = Column(JSON, nullable=True)
    volume_analysis = Column(JSON, nullable=True)

    # Processing metadata
    processing_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Any = relationship("User", back_populates="audios")
    project: Any = relationship("Project", back_populates="audios")

    def __repr__(self) -> str:
        return f"<Audio(id={self.id}, filename='{self.filename}', status={self.status})>"
