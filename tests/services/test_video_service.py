# ruff: noqa: S101
from datetime import datetime
import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import MagicMock, patch, AsyncMock

from app.models.video import Video, VideoStatus, VideoCodec
from app.schemas.file import VideoCreate, FileUpdate
from app.services.video_service import VideoService


@pytest.mark.asyncio
async def test_get_video(db: AsyncSession, test_video: Video) -> None:
    """Test getting a video by ID"""
    # Arrange
    service = VideoService(db)

    # Act
    video = await service.get_video(test_video.id, test_video.user_id)

    # Assert
    assert video is not None
    assert video.id == test_video.id
    assert video.title == test_video.title


@pytest.mark.asyncio
async def test_get_video_not_found(db: AsyncSession) -> None:
    """Test getting a video that doesn't exist"""
    # Arrange
    service = VideoService(db)

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.get_video(999, 1)
    
    assert excinfo.value.status_code == 404
    assert "Video with ID 999 not found" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_get_video_not_owned(db: AsyncSession, test_video: Video) -> None:
    """Test getting a video that belongs to another user"""
    # Arrange
    service = VideoService(db)
    other_user_id = test_video.user_id + 1

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.get_video(test_video.id, other_user_id)
    
    assert excinfo.value.status_code == 403
    assert "Not authorized" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_get_videos_by_project(db: AsyncSession, test_video: Video, test_project: Video) -> None:
    """Test getting videos by project ID"""
    # Arrange
    service = VideoService(db)

    # Act
    videos = await service.get_videos_by_project(test_project.id, test_video.user_id)

    # Assert
    assert len(videos) == 1
    assert videos[0].id == test_video.id
    assert videos[0].project_id == test_project.id


@pytest.mark.asyncio
async def test_get_videos_by_user(db: AsyncSession, test_video: Video, test_user: Video) -> None:
    """Test getting videos by user ID"""
    # Arrange
    service = VideoService(db)

    # Act
    videos = await service.get_videos_by_user(test_user.id)

    # Assert
    assert len(videos) == 1
    assert videos[0].id == test_video.id
    assert videos[0].user_id == test_user.id


@patch("app.services.video_service.get_storage_service")
@pytest.mark.asyncio
async def test_create_video(mock_get_storage_service: MagicMock, db: AsyncSession, test_user: Video, test_project: Video) -> None:
    """Test creating a video"""
    # Arrange
    mock_storage_service = AsyncMock()
    mock_get_storage_service.return_value = mock_storage_service
    
    # Use AsyncMock for async method
    mock_storage_service.save_file.return_value = "/test/path/new_test_video.mp4"

    service = VideoService(db)
    
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "new_test_video.mp4"
    mock_file.content_type = "video/mp4"
    
    # Create a mock file that returns bytes when read
    mock_file_obj = MagicMock()
    mock_file_obj.read.return_value = b"test video content"
    mock_file.file = mock_file_obj
    
    from typing import Any
    video_data: dict[str, Any] = {
        "title": "New Test Video",
        "description": "A new test video for testing",
        "project_id": test_project.id,
        "original_filename": "new_test_video.mp4",
        "file_size": 2048,
        "mime_type": "video/mp4",
        "duration": 120.0,
        "width": 1280,
        "height": 720,
        "fps": 24.0,
        "codec": VideoCodec.H264,
    }

    # Act
    video = await service.create_video(VideoCreate(**video_data), test_user.id, mock_file)

    # Assert
    assert video.title == "New Test Video"
    assert video.description == "A new test video for testing"
    assert video.project_id == test_project.id
    assert video.user_id == test_user.id
    assert video.file_path == "/test/path/new_test_video.mp4"
    assert video.file_size == 2048
    assert video.mime_type == "video/mp4"
    assert video.duration == 120.0
    assert video.width == 1280
    assert video.height == 720
    assert video.fps == 24.0
    assert (getattr(video.codec, "value", video.codec)) == "H264"
    assert video.status == VideoStatus.UPLOADING
    assert video.created_at is not None
    assert isinstance(video.created_at, datetime)


@pytest.mark.asyncio
async def test_update_video(db: AsyncSession, test_video: Video) -> None:
    """Test updating a video"""
    # Arrange
    service = VideoService(db)
    update_data = FileUpdate(
        title="Updated Test Video",
        description="An updated test video for testing",
    )

    # Act
    video = await service.update_video(test_video.id, update_data, test_video.user_id)

    # Assert
    assert video.title == "Updated Test Video"
    assert video.description == "An updated test video for testing"
    assert video.updated_at is not None
    assert isinstance(video.updated_at, datetime)


@pytest.mark.asyncio
async def test_update_video_not_found(db: AsyncSession) -> None:
    """Test updating a video that doesn't exist"""
    # Arrange
    service = VideoService(db)
    update_data = FileUpdate(
        title="Updated Test Video",
        description="An updated test video for testing",
    )

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.update_video(999, update_data, 1)
    
    assert excinfo.value.status_code == 404
    assert "Video with ID 999 not found" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_update_video_not_owned(db: AsyncSession, test_video: Video) -> None:
    """Test updating a video that belongs to another user"""
    # Arrange
    service = VideoService(db)
    other_user_id = test_video.user_id + 1
    update_data = FileUpdate(
        title="Updated Test Video",
        description="An updated test video for testing",
    )

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.update_video(test_video.id, update_data, other_user_id)
    
    assert excinfo.value.status_code == 403
    assert "Not authorized" in str(excinfo.value.detail)


@patch("app.services.video_service.get_storage_service")
@pytest.mark.asyncio
async def test_delete_video(mock_get_storage_service: MagicMock, db: AsyncSession, test_video: Video) -> None:
    """Test deleting a video"""
    # Arrange
    mock_storage_service = AsyncMock()
    mock_get_storage_service.return_value = mock_storage_service
    
    # Use AsyncMock for async method
    mock_storage_service.delete_file.return_value = True

    service = VideoService(db)
    video_id = test_video.id

    # Act
    await service.delete_video(video_id, test_video.user_id)

    # Assert
    video = await service.video_repository.get(video_id)
    assert video is None
    # Verify that delete_file was called
    mock_storage_service.delete_file.assert_called_once()


@pytest.mark.asyncio
async def test_delete_video_not_found(db: AsyncSession) -> None:
    """Test deleting a video that doesn't exist"""
    # Arrange
    service = VideoService(db)

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.delete_video(999, 1)
    
    assert excinfo.value.status_code == 404
    assert "Video with ID 999 not found" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_delete_video_not_owned(db: AsyncSession, test_video: Video) -> None:
    """Test deleting a video that belongs to another user"""
    # Arrange
    service = VideoService(db)
    other_user_id = test_video.user_id + 1

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.delete_video(test_video.id, other_user_id)
    
    assert excinfo.value.status_code == 403
    assert "Not authorized" in str(excinfo.value.detail)