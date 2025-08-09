from enum import Enum


class FileType(str, Enum):
    """Type of file in the domain (stable API values)."""

    VIDEO = "video"
    AUDIO = "audio"


class FileStatus(str, Enum):
    """Processing status shared across audio/video files."""

    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"

# Backward-compatible aliases for model-specific statuses
VideoStatus = FileStatus
AudioStatus = FileStatus


class VideoCodec(str, Enum):
    H264 = "H264"
    H265 = "H265"
    VP9 = "VP9"
    AV1 = "AV1"


class AudioCodec(str, Enum):
    MP3 = "MP3"
    AAC = "AAC"
    WAV = "WAV"
    FLAC = "FLAC"
    OGG = "OGG"
