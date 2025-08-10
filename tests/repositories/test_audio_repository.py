# ruff: noqa: S101
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audio import Audio, AudioCodec, AudioStatus
from app.repositories.audio_repository import AudioRepository
from app.schemas.file import AudioCreate, FileUpdate


@pytest.mark.asyncio
async def test_create_audio(db: AsyncSession, test_user: Audio, test_project: Audio) -> None:
    """Test creating an audio file"""
    # Arrange
    repo = AudioRepository(db)
    audio_in = AudioCreate(
        title="New Test Audio",
        description="A new test audio file for testing",
        project_id=test_project.id,
        original_filename="new_test_audio.mp3",
        file_size=1024,
        mime_type="audio/mp3",
        duration=240.0,
        codec=AudioCodec.MP3,
        bitrate=192,
        sample_rate=44100,
        channels=2,
    )

    # Act
    audio = await repo.create_with_owner(audio_in, owner_id=test_user.id, file_path="/test/path/new_test_audio.mp3")

    # Assert
    assert audio.title == "New Test Audio"
    assert audio.description == "A new test audio file for testing"
    assert audio.project_id == test_project.id
    assert audio.user_id == test_user.id
    assert audio.file_path == "/test/path/new_test_audio.mp3"
    assert audio.file_size == 1024
    assert audio.mime_type == "audio/mp3"
    assert audio.duration == 240.0
    assert audio.codec == AudioCodec.MP3
    assert audio.bitrate == 192
    assert audio.sample_rate == 44100
    assert audio.channels == 2
    assert audio.status == AudioStatus.UPLOADING
    assert audio.created_at is not None
    assert isinstance(audio.created_at, datetime)


@pytest.mark.asyncio
async def test_get_audio_by_id(db: AsyncSession, test_audio: Audio) -> None:
    """Test getting an audio file by ID"""
    # Arrange
    repo = AudioRepository(db)

    # Act
    audio = await repo.get(test_audio.id)

    # Assert
    assert audio is not None
    assert audio.id == test_audio.id
    assert audio.title == test_audio.title
    assert audio.file_path == test_audio.file_path


@pytest.mark.asyncio
async def test_get_audios_by_project(db: AsyncSession, test_audio: Audio, test_project: Audio) -> None:
    """Test getting audio files by project ID"""
    # Arrange
    repo = AudioRepository(db)

    # Act
    audios = await repo.get_by_project(test_project.id)

    # Assert
    assert len(audios) == 1
    assert audios[0].id == test_audio.id
    assert audios[0].project_id == test_project.id


@pytest.mark.asyncio
async def test_get_audios_by_user(db: AsyncSession, test_audio: Audio, test_user: Audio) -> None:
    """Test getting audio files by user ID"""
    # Arrange
    repo = AudioRepository(db)

    # Act
    audios = await repo.get_by_user(test_user.id)

    # Assert
    assert len(audios) == 1
    assert audios[0].id == test_audio.id
    assert audios[0].user_id == test_user.id


@pytest.mark.asyncio
async def test_update_audio(db: AsyncSession, test_audio: Audio) -> None:
    """Test updating an audio file"""
    # Arrange
    repo = AudioRepository(db)
    update_data = FileUpdate(
        title="Updated Test Audio",
        description="An updated test audio file for testing",
    )

    # Act
    audio = await repo.update(test_audio, update_data)

    # Assert
    assert audio.title == "Updated Test Audio"
    assert audio.description == "An updated test audio file for testing"
    assert audio.updated_at is not None
    assert isinstance(audio.updated_at, datetime)


@pytest.mark.asyncio
async def test_update_audio_status(db: AsyncSession, test_audio: Audio) -> None:
    """Test updating an audio file's status"""
    # Arrange
    repo = AudioRepository(db)

    # Act
    audio = await repo.update_status(test_audio, AudioStatus.PROCESSING)

    # Assert
    assert audio.status == AudioStatus.PROCESSING
    assert audio.updated_at is not None
    assert isinstance(audio.updated_at, datetime)


@pytest.mark.asyncio
async def test_delete_audio(db: AsyncSession, test_audio: Audio) -> None:
    """Test deleting an audio file"""
    # Arrange
    repo = AudioRepository(db)
    audio_id = test_audio.id

    # Act
    await repo.delete(audio_id)

    # Assert
    audio = await repo.get(audio_id)
    assert audio is None