import logging
from typing import List, Optional, Tuple
from pathlib import Path

import magic
from fastapi import UploadFile, HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

mime_magic = magic.Magic(mime=True)

async def validate_file(
    file: UploadFile,
    allowed_mime_types: List[str],
    max_size_mb: Optional[int] = None,
) -> Tuple[str, int]:
    """
    Validate a file using magic bytes to check its actual type.
    
    Args:
        file: The uploaded file to validate
        allowed_mime_types: List of allowed MIME types
        max_size_mb: Maximum file size in MB (defaults to settings.max_upload_size_mb)
        
    Returns:
        Tuple of (detected_mime_type, file_size)
        
    Raises:
        HTTPException: If the file is invalid
    """
    if max_size_mb is None:
        max_size_mb = settings.max_upload_size_mb
    
    max_size_bytes = max_size_mb * 1024 * 1024
    
    content_type = file.content_type
    if content_type not in allowed_mime_types:
        logger.warning(f"Rejected file with Content-Type: {content_type}, allowed types: {allowed_mime_types}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {content_type}. Allowed types: {allowed_mime_types}",
        )
    
    sample = await file.read(2048)
    await file.seek(0)  # Reset file position
    
    file_size = len(sample)
    chunk_size = 8192  # 8KB chunks
    
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        file_size += len(chunk)
        
        if file_size > max_size_bytes:
            await file.seek(0)  # Reset file position
            logger.warning(f"Rejected file exceeding size limit: {file_size} bytes > {max_size_bytes} bytes")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {max_size_mb} MB.",
            )
    
    await file.seek(0)
    
    detected_mime_type = mime_magic.from_buffer(sample)
    
    if detected_mime_type not in allowed_mime_types:
        logger.warning(
            f"Rejected file with mismatched MIME type. "
            f"Content-Type: {content_type}, Detected: {detected_mime_type}"
        )
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"File content doesn't match the declared type. "
                f"Detected: {detected_mime_type}, Expected: {content_type}"
            ),
        )
    
    logger.info(
        f"Validated file: size={file_size} bytes, "
        f"content_type={content_type}, detected_type={detected_mime_type}"
    )
    
    return detected_mime_type, file_size


async def validate_audio_file(file: UploadFile) -> Tuple[str, int]:
    """
    Validate an audio file using magic bytes.
    
    Args:
        file: The uploaded audio file
        
    Returns:
        Tuple of (detected_mime_type, file_size)
    """
    return await validate_file(
        file=file,
        allowed_mime_types=settings.allowed_audio_types,
        max_size_mb=settings.max_upload_size_mb,
    )


async def validate_video_file(file: UploadFile) -> Tuple[str, int]:
    """
    Validate a video file using magic bytes.
    
    Args:
        file: The uploaded video file
        
    Returns:
        Tuple of (detected_mime_type, file_size)
    """
    return await validate_file(
        file=file,
        allowed_mime_types=settings.allowed_video_types,
        max_size_mb=settings.max_upload_size_mb,
    )


def validate_file_path(file_path: Path, allowed_mime_types: List[str]) -> str:
    """
    Validate a file on disk using magic bytes.
    
    Args:
        file_path: Path to the file
        allowed_mime_types: List of allowed MIME types
        
    Returns:
        Detected MIME type
        
    Raises:
        ValueError: If the file is invalid
    """
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")
    
    file_size = file_path.stat().st_size
    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        raise ValueError(
            f"File too large: {file_size} bytes. Maximum size is {settings.max_upload_size_mb} MB."
        )
    
    detected_mime_type = mime_magic.from_file(str(file_path))
    
    if detected_mime_type not in allowed_mime_types:
        raise ValueError(
            f"Unsupported file type: {detected_mime_type}. Allowed types: {allowed_mime_types}"
        )
    
    return detected_mime_type