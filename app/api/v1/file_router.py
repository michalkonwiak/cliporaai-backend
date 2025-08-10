import logging
from typing import cast

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.domain.enums import AudioCodec, VideoCodec
from app.models.user import User
from app.schemas.file import (
    AudioCreate,
    AudioRead,
    FileStatus,
    FileType,
    FileUpdate,
    FileUploadResponse,
    VideoCreate,
    VideoRead,
)
from app.services.audio_service import AudioService
from app.services.video_service import VideoService

router = APIRouter(prefix="/files", tags=["files"])
logger = logging.getLogger(__name__)


@router.post("/videos/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    project_id: int = Form(...),
    title: str | None = Form(None),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileUploadResponse:
    """
    Upload a video file.
    
    The file will be stored in the configured storage service and metadata will be saved in the database.
    """
    video_data = VideoCreate(
        title=title,
        description=description,
        project_id=project_id,
        original_filename=(file.filename or ""),
        file_size=0,
        mime_type=(file.content_type or ""),
        duration=0.0,
        width=1920,
        height=1080,
        fps=30.0,
        codec=VideoCodec.H264,
    )
    
    video_service = VideoService(db)
    video = await video_service.create_video(video_data, current_user.id, file)

    return FileUploadResponse(
        id=video.id,
        filename=video.filename,
        original_filename=video.original_filename,
        status=FileStatus.UPLOADED,
        file_type=FileType.VIDEO,
    )


@router.post("/audios/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio(
    project_id: int = Form(...),
    title: str | None = Form(None),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileUploadResponse:
    """
    Upload an audio file.
    
    The file will be stored in the configured storage service and metadata will be saved in the database.
    """
    audio_data = AudioCreate(
        title=title,
        description=description,
        project_id=project_id,
        original_filename=(file.filename or ""),
        file_size=0,
        mime_type=(file.content_type or ""),
        duration=0.0,
        codec=AudioCodec.MP3,
        bitrate=320,
        sample_rate=44100,
        channels=2,
    )
    
    audio_service = AudioService(db)
    audio = await audio_service.create_audio(audio_data, current_user.id, file)

    return FileUploadResponse(
        id=audio.id,
        filename=audio.filename,
        original_filename=audio.original_filename,
        status=FileStatus.UPLOADED,
        file_type=FileType.AUDIO,
    )


@router.get("/videos", response_model=list[VideoRead])
async def list_videos(
    project_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[VideoRead]:
    """
    List videos.
    
    If project_id is provided, only videos for that project will be returned.
    Otherwise, all videos for the current user will be returned.
    """
    video_service = VideoService(db)
    
    if project_id is not None:
        videos = cast(list[VideoRead], await video_service.get_videos_by_project(project_id, current_user.id))
    else:
        videos = cast(list[VideoRead], await video_service.get_videos_by_user(current_user.id))
    
    return videos


@router.get("/audios", response_model=list[AudioRead])
async def list_audios(
    project_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AudioRead]:
    """
    List audios.
    
    If project_id is provided, only audios for that project will be returned.
    Otherwise, all audios for the current user will be returned.
    """
    audio_service = AudioService(db)
    
    if project_id is not None:
        audios = cast(list[AudioRead], await audio_service.get_audios_by_project(project_id, current_user.id))
    else:
        audios = cast(list[AudioRead], await audio_service.get_audios_by_user(current_user.id))
    
    return audios


@router.get("/videos/{video_id}", response_model=VideoRead)
async def get_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VideoRead:
    """
    Get a video by ID.
    """
    video_service = VideoService(db)
    return await video_service.get_video(video_id, current_user.id)


@router.get("/audios/{audio_id}", response_model=AudioRead)
async def get_audio(
    audio_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AudioRead:
    """
    Get an audio by ID.
    """
    audio_service = AudioService(db)
    return await audio_service.get_audio(audio_id, current_user.id)


@router.patch("/videos/{video_id}", response_model=VideoRead)
async def update_video(
    video_id: int,
    update_data: FileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VideoRead:
    """
    Update a video's metadata.
    """
    video_service = VideoService(db)
    return await video_service.update_video(video_id, update_data, current_user.id)


@router.patch("/audios/{audio_id}", response_model=AudioRead)
async def update_audio(
    audio_id: int,
    update_data: FileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AudioRead:
    """
    Update an audio's metadata.
    """
    audio_service = AudioService(db)
    return await audio_service.update_audio(audio_id, update_data, current_user.id)


@router.delete("/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a video.
    """
    video_service = VideoService(db)
    await video_service.delete_video(video_id, current_user.id)
    return


@router.delete("/audios/{audio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audio(
    audio_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an audio.
    """
    audio_service = AudioService(db)
    await audio_service.delete_audio(audio_id, current_user.id)
    return