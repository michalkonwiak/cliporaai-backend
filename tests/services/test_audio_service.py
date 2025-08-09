# ruff: noqa: S101
from datetime import datetime
import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import MagicMock, patch, AsyncMock

from app.models.audio import Audio, AudioStatus, AudioCodec
from app.models.user import User
from app.models.project import Project
from app.schemas.file import AudioCreate, FileUpdate
from app.services.audio_service import AudioService


@pytest.mark.asyncio
async def test_get_audio(db: AsyncSession, test_audio: Audio) -> None:
    """Test getting an audio file by ID"""
    # Arrange
    service = AudioService(db)

    # Act
    audio = await service.get_audio(test_audio.id, test_audio.user_id)

    # Assert
    assert audio is not None
    assert audio.id == test_audio.id
    assert audio.title == test_audio.title


@pytest.mark.asyncio
async def test_get_audio_not_found(db: AsyncSession) -> None:
    """Test getting an audio file that doesn't exist"""
    # Arrange
    service = AudioService(db)

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.get_audio(999, 1)
    
    assert excinfo.value.status_code == 404
    assert "Audio with ID 999 not found" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_get_audio_not_owned(db: AsyncSession, test_audio: Audio) -> None:
    """Test getting an audio file that belongs to another user"""
    # Arrange
    service = AudioService(db)
    other_user_id = test_audio.user_id + 1

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.get_audio(test_audio.id, other_user_id)
    
    assert excinfo.value.status_code == 403
    assert "Not authorized" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_get_audios_by_project(db: AsyncSession, test_audio: Audio, test_project: Project) -> None:
    """Test getting audio files by project ID"""
    # Arrange
    service = AudioService(db)

    # Act
    audios = await service.get_audios_by_project(test_project.id, test_audio.user_id)

    # Assert
    assert len(audios) == 1
    assert audios[0].id == test_audio.id
    assert audios[0].project_id == test_project.id


@pytest.mark.asyncio
async def test_get_audios_by_user(db: AsyncSession, test_audio: Audio, test_user: User) -> None:
    """Test getting audio files by user ID"""
    # Arrange
    service = AudioService(db)

    # Act
    audios = await service.get_audios_by_user(test_user.id)

    # Assert
    assert len(audios) == 1
    assert audios[0].id == test_audio.id
    assert audios[0].user_id == test_user.id


@patch("app.services.audio_service.get_storage_service")
@pytest.mark.asyncio
async def test_create_audio(mock_get_storage_service: MagicMock, db: AsyncSession, test_user: User, test_project: Project) -> None:
    """Test creating an audio file"""
    # Arrange
    mock_storage_service = AsyncMock()
    mock_get_storage_service.return_value = mock_storage_service
    
    # Use AsyncMock for async method
    mock_storage_service.save_file.return_value = "/test/path/new_test_audio.mp3"

    service = AudioService(db)
    
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "new_test_audio.mp3"
    mock_file.content_type = "audio/mp3"
    
    # Create a mock file that returns bytes when read
    mock_file_obj = MagicMock()
    mock_file_obj.read.return_value = b"test audio content"
    mock_file.file = mock_file_obj
    
    from typing import Any
    audio_data: dict[str, Any] = {
        "title": "New Test Audio",
        "description": "A new test audio file for testing",
        "project_id": test_project.id,
        "original_filename": "new_test_audio.mp3",
        "file_size": 1024,
        "mime_type": "audio/mp3",
        "duration": 240.0,
        "codec": AudioCodec.MP3,
        "bitrate": 192,
        "sample_rate": 44100,
        "channels": 2,
    }

    # Act
    audio = await service.create_audio(AudioCreate(**audio_data), test_user.id, mock_file)

    # Assert
    assert audio.title == "New Test Audio"
    assert audio.description == "A new test audio file for testing"
    assert audio.project_id == test_project.id
    assert audio.user_id == test_user.id
    assert audio.file_path == "/test/path/new_test_audio.mp3"
    assert audio.file_size == 1024
    assert audio.mime_type == "audio/mp3"
    assert audio.duration == 240.0
    assert (getattr(audio.codec, "value", audio.codec)) == "MP3"
    assert audio.bitrate == 192
    assert audio.sample_rate == 44100
    assert audio.channels == 2
    assert audio.status == AudioStatus.UPLOADING
    assert audio.created_at is not None
    assert isinstance(audio.created_at, datetime)


@pytest.mark.asyncio
async def test_update_audio(db: AsyncSession, test_audio: Audio) -> None:
    """Test updating an audio file"""
    # Arrange
    service = AudioService(db)
    update_data = FileUpdate(
        title="Updated Test Audio",
        description="An updated test audio file for testing",
    )

    # Act
    audio = await service.update_audio(test_audio.id, update_data, test_audio.user_id)

    # Assert
    assert audio.title == "Updated Test Audio"
    assert audio.description == "An updated test audio file for testing"
    assert audio.updated_at is not None
    assert isinstance(audio.updated_at, datetime)


@pytest.mark.asyncio
async def test_update_audio_not_found(db: AsyncSession) -> None:
    """Test updating an audio file that doesn't exist"""
    # Arrange
    service = AudioService(db)
    update_data = FileUpdate(
        title="Updated Test Audio",
        description="An updated test audio file for testing",
    )

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.update_audio(999, update_data, 1)
    
    assert excinfo.value.status_code == 404
    assert "Audio with ID 999 not found" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_update_audio_not_owned(db: AsyncSession, test_audio: Audio) -> None:
    """Test updating an audio file that belongs to another user"""
    # Arrange
    service = AudioService(db)
    other_user_id = test_audio.user_id + 1
    update_data = FileUpdate(
        title="Updated Test Audio",
        description="An updated test audio file for testing",
    )

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.update_audio(test_audio.id, update_data, other_user_id)
    
    assert excinfo.value.status_code == 403
    assert "Not authorized" in str(excinfo.value.detail)


@patch("app.services.audio_service.get_storage_service")
@pytest.mark.asyncio
async def test_delete_audio(mock_get_storage_service: MagicMock, db: AsyncSession, test_audio: Audio) -> None:
    """Test deleting an audio file"""
    # Arrange
    mock_storage_service = AsyncMock()
    mock_get_storage_service.return_value = mock_storage_service
    
    # Use AsyncMock for async method
    mock_storage_service.delete_file.return_value = True

    service = AudioService(db)
    audio_id = test_audio.id

    # Act
    await service.delete_audio(audio_id, test_audio.user_id)

    # Assert
    audio = await service.audio_repository.get(audio_id)
    assert audio is None
    # Verify that delete_file was called
    mock_storage_service.delete_file.assert_called_once()


@pytest.mark.asyncio
async def test_delete_audio_not_found(db: AsyncSession) -> None:
    """Test deleting an audio file that doesn't exist"""
    # Arrange
    service = AudioService(db)

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.delete_audio(999, 1)
    
    assert excinfo.value.status_code == 404
    assert "Audio with ID 999 not found" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_delete_audio_not_owned(db: AsyncSession, test_audio: Audio) -> None:
    """Test deleting an audio file that belongs to another user"""
    # Arrange
    service = AudioService(db)
    other_user_id = test_audio.user_id + 1

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.delete_audio(test_audio.id, other_user_id)
    
    assert excinfo.value.status_code == 403
    assert "Not authorized" in str(excinfo.value.detail)