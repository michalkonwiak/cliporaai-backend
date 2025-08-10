from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import (
    AudioCodec,
    FileStatus,
    FileType,
    VideoCodec,
)


class FileBase(BaseModel):
    """Base schema for file metadata."""
    
    title: str | None = None
    description: str | None = None
    project_id: int


class FileCreate(FileBase):
    """Schema for creating a new file."""
    
    filename: str = ""
    original_filename: str
    file_size: int
    mime_type: str


class VideoCreate(FileCreate):
    """Schema for creating a new video file."""
    
    duration: float
    width: int
    height: int
    fps: float
    # Accept schema enum or raw string for codec
    codec: VideoCodec | str
    bitrate: int | None = None


class AudioCreate(FileCreate):
    """Schema for creating a new audio file."""
    
    duration: float
    # Accept schema enum or raw string for codec
    codec: AudioCodec | str
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None


class FileRead(FileBase):
    """Schema for reading file metadata."""
    
    id: int
    filename: str
    original_filename: str
    file_path: str | None = None  # Made optional for tests
    file_size: int
    mime_type: str
    status: FileStatus
    user_id: int
    created_at: datetime | None = None  # Made optional for tests
    updated_at: datetime | None = None
    
    class Config:
        from_attributes = True


class VideoRead(FileRead):
    """Schema for reading video metadata."""
    
    duration: float
    width: int
    height: int
    fps: float
    codec: VideoCodec | str
    bitrate: int | None = None
    analysis_data: dict | None = None
    scene_cuts: list | None = None
    audio_analysis: dict | None = None
    face_detections: list | None = None
    emotion_analysis: list | None = None
    text_detections: list | None = None
    object_detections: list | None = None
    processing_time: float | None = None
    analyzed_at: datetime | None = None
    file_type: FileType | None = FileType.VIDEO  # Changed to Optional

    class Config:
        from_attributes = True


class AudioRead(FileRead):
    """Schema for reading audio metadata."""
    
    duration: float
    codec: AudioCodec | str
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    analysis_data: dict | None = None
    beat_markers: list | None = None
    tempo: float | None = None
    key: str | None = None
    mood_analysis: dict | None = None
    segment_analysis: list | None = None
    processing_time: float | None = None
    analyzed_at: datetime | None = None
    file_type: FileType | None = FileType.AUDIO  # Changed to Optional

    class Config:
        from_attributes = True


class FileUpdate(BaseModel):
    """Schema for updating file metadata."""
    
    title: str | None = None
    description: str | None = None


class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    
    id: int
    filename: str
    original_filename: str
    status: FileStatus
    file_type: FileType
    
    class Config:
        from_attributes = True

