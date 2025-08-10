
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import VideoStatus
from app.models.video import Video
from app.repositories.base import BaseRepository
from app.schemas.file import FileUpdate, VideoCreate


class VideoRepository(BaseRepository[Video, VideoCreate, FileUpdate]):
    """Async repository for Video model with custom methods."""

    def __init__(self, db: AsyncSession):
        super().__init__(Video, db)

    async def create_with_owner(
        self, obj_in: VideoCreate, owner_id: int, file_path: str
    ) -> Video:
        """Create a new video with owner."""
        from app.domain.enums import VideoCodec
        codec = VideoCodec(obj_in.codec)

        obj_data = obj_in.model_dump(exclude={"codec"})
        db_obj = Video(
            **obj_data,
            user_id=owner_id,
            file_path=file_path,
            codec=codec,
            status=VideoStatus.UPLOADING,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_by_project(self, project_id: int) -> list[Video]:
        """Get all videos for a project."""
        stmt = select(Video).where(Video.project_id == project_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user(self, user_id: int) -> list[Video]:
        """Get all videos for a user."""
        stmt = select(Video).where(Video.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, db_obj: Video, status: VideoStatus) -> Video:
        """Update video status."""
        db_obj.status = status
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_analysis_data(self, db_obj: Video, analysis_data: dict) -> Video:
        """Update video analysis data."""
        db_obj.analysis_data = analysis_data
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj