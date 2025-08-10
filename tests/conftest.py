from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.dependencies import get_db

# So that middleware does not hit Redis in tests
settings.rate_limit_enabled = False

from app.main import app  # noqa: E402
from app.models.audio import Audio, AudioCodec, AudioStatus  # noqa: E402
from app.models.project import Project, ProjectStatus, ProjectType  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.video import Video, VideoCodec, VideoStatus  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402

pytest_plugins = ["pytest_asyncio"]

# Add timeout configuration to prevent hanging tests
# Using pytest-timeout plugin which is configured in pyproject.toml
# Default timeout is 30 seconds


DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[httpx.AsyncClient]:
    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    # Disable rate limiter at runtime too
    app_state: Any = app.state
    if hasattr(app_state, "limiter"):
        app_state.limiter.enabled = False
    # Do not run lifespan to avoid external services
    transport = httpx.ASGITransport(app=app)
    # Use a standard base URL
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides = {}


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    user_data = {
        "email": "test@example.com",
        "hashed_password": hash_password("password123"),
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_superuser": False,
    }
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_superuser(db: AsyncSession) -> User:
    user_data = {
        "email": "admin@example.com",
        "hashed_password": hash_password("admin123"),
        "first_name": "Admin",
        "last_name": "Super",
        "is_active": True,
        "is_superuser": True,
    }
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def token_headers(db: AsyncSession, test_user: User) -> dict[str, str]:
    auth_service = AuthService(db)
    token = await auth_service.create_token(test_user)
    return {"Authorization": f"Bearer {token.access_token}"}


@pytest_asyncio.fixture
async def superuser_token_headers(db: AsyncSession, test_superuser: User) -> dict[str, str]:
    auth_service = AuthService(db)
    token = await auth_service.create_token(test_superuser)
    return {"Authorization": f"Bearer {token.access_token}"}


@pytest_asyncio.fixture
async def test_project(db: AsyncSession, test_user: User) -> Project:
    project_data = {
        "name": "Test Project",
        "description": "A test project for testing",
        "user_id": test_user.id,
        "project_type": ProjectType.DYNAMIC,
        "status": ProjectStatus.DRAFT,
        "total_duration": 0.0,
        "processing_progress": 0.0,
    }
    project = Project(**project_data)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@pytest_asyncio.fixture
async def test_video(db: AsyncSession, test_user: User, test_project: Project) -> Video:
    test_dir = Path("test_uploads")
    test_dir.mkdir(exist_ok=True)
    file_path = str(test_dir / "test_video.mp4")
    video_data = {
        "filename": "test_video.mp4",
        "original_filename": "original_test_video.mp4",
        "title": "Test Video",
        "description": "A test video for testing",
        "project_id": test_project.id,
        "user_id": test_user.id,
        "file_path": file_path,
        "file_size": 1024,
        "mime_type": "video/mp4",
        "duration": 60.0,
        "width": 1920,
        "height": 1080,
        "fps": 30.0,
        "codec": VideoCodec.H264,
        "status": VideoStatus.UPLOADED,
    }
    video = Video(**video_data)
    db.add(video)
    await db.commit()
    await db.refresh(video)
    return video


@pytest_asyncio.fixture
async def test_audio(db: AsyncSession, test_user: User, test_project: Project) -> Audio:
    test_dir = Path("test_uploads")
    test_dir.mkdir(exist_ok=True)
    file_path = str(test_dir / "test_audio.mp3")
    audio_data = {
        "filename": "test_audio.mp3",
        "original_filename": "original_test_audio.mp3",
        "title": "Test Audio",
        "description": "A test audio file for testing",
        "project_id": test_project.id,
        "user_id": test_user.id,
        "file_path": file_path,
        "file_size": 512,
        "mime_type": "audio/mp3",
        "duration": 180.0,
        "codec": AudioCodec.MP3,
        "bitrate": 320,
        "sample_rate": 44100,
        "channels": 2,
        "status": AudioStatus.UPLOADED,
    }
    audio = Audio(**audio_data)
    db.add(audio)
    await db.commit()
    await db.refresh(audio)
    return audio
