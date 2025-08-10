# ruff: noqa: S101
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video, VideoCodec, VideoStatus
from app.repositories.video_repository import VideoRepository
from app.schemas.file import FileUpdate, VideoCreate


@pytest.mark.asyncio
async def test_create_video(db: AsyncSession, test_user: Video, test_project: Video) -> None:
    """Test creating a video"""
    # Arrange
    repo = VideoRepository(db)
    video_in = VideoCreate(
        title="New Test Video",
        description="A new test video for testing",
        project_id=test_project.id,
        original_filename="new_test_video.mp4",
        file_size=2048,
        mime_type="video/mp4",
        duration=120.0,
        width=1280,
        height=720,
        fps=24.0,
        codec=VideoCodec.H264,
    )

    # Act
    video = await repo.create_with_owner(video_in, owner_id=test_user.id, file_path="/test/path/new_test_video.mp4")

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
    assert video.codec == VideoCodec.H264
    assert video.status == VideoStatus.UPLOADING
    assert video.created_at is not None
    assert isinstance(video.created_at, datetime)


@pytest.mark.asyncio
async def test_get_video_by_id(db: AsyncSession, test_video: Video) -> None:
    """Test getting a video by ID"""
    # Arrange
    repo = VideoRepository(db)

    # Act
    video = await repo.get(test_video.id)

    # Assert
    assert video is not None
    assert video.id == test_video.id
    assert video.title == test_video.title
    assert video.file_path == test_video.file_path


@pytest.mark.asyncio
async def test_get_videos_by_project(db: AsyncSession, test_video: Video, test_project: Video) -> None:
    """Test getting videos by project ID"""
    # Arrange
    repo = VideoRepository(db)

    # Act
    videos = await repo.get_by_project(test_project.id)

    # Assert
    assert len(videos) == 1
    assert videos[0].id == test_video.id
    assert videos[0].project_id == test_project.id


@pytest.mark.asyncio
async def test_get_videos_by_user(db: AsyncSession, test_video: Video, test_user: Video) -> None:
    """Test getting videos by user ID"""
    # Arrange
    repo = VideoRepository(db)

    # Act
    videos = await repo.get_by_user(test_user.id)

    # Assert
    assert len(videos) == 1
    assert videos[0].id == test_video.id
    assert videos[0].user_id == test_user.id


@pytest.mark.asyncio
async def test_update_video(db: AsyncSession, test_video: Video) -> None:
    """Test updating a video"""
    # Arrange
    repo = VideoRepository(db)
    update_data = FileUpdate(
        title="Updated Test Video",
        description="An updated test video for testing",
    )

    # Act
    video = await repo.update(test_video, update_data)

    # Assert
    assert video.title == "Updated Test Video"
    assert video.description == "An updated test video for testing"
    assert video.updated_at is not None
    assert isinstance(video.updated_at, datetime)


@pytest.mark.asyncio
async def test_update_video_status(db: AsyncSession, test_video: Video) -> None:
    """Test updating a video's status"""
    # Arrange
    repo = VideoRepository(db)

    # Act
    video = await repo.update_status(test_video, VideoStatus.PROCESSING)

    # Assert
    assert video.status == VideoStatus.PROCESSING
    assert video.updated_at is not None
    assert isinstance(video.updated_at, datetime)


@pytest.mark.asyncio
async def test_delete_video(db: AsyncSession, test_video: Video) -> None:
    """Test deleting a video"""
    # Arrange
    repo = VideoRepository(db)
    video_id = test_video.id

    # Act
    await repo.delete(video_id)

    # Assert
    video = await repo.get(video_id)
    assert video is None