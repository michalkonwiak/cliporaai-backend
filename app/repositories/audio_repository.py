from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audio import Audio
from app.domain.enums import AudioStatus
from app.repositories.base import BaseRepository
from app.schemas.file import AudioCreate, FileUpdate


class AudioRepository(BaseRepository[Audio, AudioCreate, FileUpdate]):
    """Async repository for Audio model with custom methods."""

    def __init__(self, db: AsyncSession):
        super().__init__(Audio, db)

    async def create_with_owner(
        self, obj_in: AudioCreate, owner_id: int, file_path: str
    ) -> Audio:
        """Create a new audio file with owner."""
        from app.domain.enums import AudioCodec
        codec = AudioCodec(obj_in.codec)

        obj_data = obj_in.model_dump(exclude={"codec"})
        db_obj = Audio(
            **obj_data,
            user_id=owner_id,
            file_path=file_path,
            codec=codec,
            status=AudioStatus.UPLOADING,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_by_project(self, project_id: int) -> List[Audio]:
        """Get all audio files for a project."""
        stmt = select(Audio).where(Audio.project_id == project_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user(self, user_id: int) -> List[Audio]:
        """Get all audio files for a user."""
        stmt = select(Audio).where(Audio.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, db_obj: Audio, status: AudioStatus) -> Audio:
        """Update audio status."""
        db_obj.status = status
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_analysis_data(self, db_obj: Audio, analysis_data: dict) -> Audio:
        """Update audio analysis data."""
        db_obj.analysis_data = analysis_data
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj