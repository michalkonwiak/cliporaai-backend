import os
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import VideoStatus
from app.models.video import Video
from app.repositories.video_repository import VideoRepository
from app.schemas.file import FileUpdate, VideoCreate
from app.services.storage_service import get_storage_service


class VideoService:
    """
    Service for video operations
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.video_repository = VideoRepository(db)
        self.storage_service = get_storage_service()

    async def get_video(self, video_id: int, user_id: int) -> Video:
        """
        Get a video by ID
        """
        video = await self.video_repository.get(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video with ID {video_id} not found",
            )
        
        if video.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this video",
            )
        
        return video

    async def get_videos_by_project(self, project_id: int, user_id: int) -> list[Video]:
        """
        Get all videos for a project
        """
        videos = await self.video_repository.get_by_project(project_id)
        # Filter videos by user_id for security
        return [video for video in videos if video.user_id == user_id]

    async def get_videos_by_user(self, user_id: int) -> list[Video]:
        """
        Get all videos for a user
        """
        return await self.video_repository.get_by_user(user_id)

    async def create_video(self, video_in: VideoCreate, user_id: int, file: UploadFile) -> Video:
        """
        Create a new video
        """
        filename = file.filename or ""
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        destination_path = f"{user_id}/videos/{unique_filename}"
        
        file_path = await self.storage_service.save_file(file, destination_path, user_id)
        
        obj_data = video_in.model_dump()
        obj_data["filename"] = unique_filename
        video_create = VideoCreate(**obj_data)
        
        return await self.video_repository.create_with_owner(video_create, user_id, file_path)

    async def update_video(self, video_id: int, update_data: FileUpdate, user_id: int) -> Video:
        """
        Update a video
        """
        video = await self.get_video(video_id, user_id)
        return await self.video_repository.update(video, update_data)

    async def update_video_status(self, video_id: int, status: VideoStatus, user_id: int) -> Video:
        """
        Update a video's status
        """
        video = await self.get_video(video_id, user_id)
        return await self.video_repository.update_status(video, status)

    async def delete_video(self, video_id: int, user_id: int) -> None:
        """
        Delete a video
        """
        video = await self.get_video(video_id, user_id)
        
        # Delete the file
        await self.storage_service.delete_file(video.file_path)
        
        # Delete the database record
        await self.video_repository.delete(video_id)