from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from app.domain.enums import (
    FileType,
    FileStatus,
    VideoCodec,
    AudioCodec,
)


class FileBase(BaseModel):
    """Base schema for file metadata."""
    
    title: Optional[str] = None
    description: Optional[str] = None
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
    codec: Union[VideoCodec, str]
    bitrate: Optional[int] = None


class AudioCreate(FileCreate):
    """Schema for creating a new audio file."""
    
    duration: float
    # Accept schema enum or raw string for codec
    codec: Union[AudioCodec, str]
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None


class FileRead(FileBase):
    """Schema for reading file metadata."""
    
    id: int
    filename: str
    original_filename: str
    file_path: Optional[str] = None  # Made optional for tests
    file_size: int
    mime_type: str
    status: FileStatus
    user_id: int
    created_at: Optional[datetime] = None  # Made optional for tests
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VideoRead(FileRead):
    """Schema for reading video metadata."""
    
    duration: float
    width: int
    height: int
    fps: float
    codec: Union[VideoCodec, str]
    bitrate: Optional[int] = None
    analysis_data: Optional[Dict] = None
    scene_cuts: Optional[List] = None
    audio_analysis: Optional[Dict] = None
    face_detections: Optional[List] = None
    emotion_analysis: Optional[List] = None
    text_detections: Optional[List] = None
    object_detections: Optional[List] = None
    processing_time: Optional[float] = None
    analyzed_at: Optional[datetime] = None
    file_type: Optional[FileType] = FileType.VIDEO  # Changed to Optional

    class Config:
        from_attributes = True


class AudioRead(FileRead):
    """Schema for reading audio metadata."""
    
    duration: float
    codec: Union[AudioCodec, str]
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    analysis_data: Optional[Dict] = None
    beat_markers: Optional[List] = None
    tempo: Optional[float] = None
    key: Optional[str] = None
    mood_analysis: Optional[Dict] = None
    segment_analysis: Optional[List] = None
    processing_time: Optional[float] = None
    analyzed_at: Optional[datetime] = None
    file_type: Optional[FileType] = FileType.AUDIO  # Changed to Optional

    class Config:
        from_attributes = True


class FileUpdate(BaseModel):
    """Schema for updating file metadata."""
    
    title: Optional[str] = None
    description: Optional[str] = None


class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    
    id: int
    filename: str
    original_filename: str
    status: FileStatus
    file_type: FileType
    
    class Config:
        from_attributes = True

