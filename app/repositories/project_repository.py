from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.base import BaseRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectRepository(BaseRepository[Project, ProjectCreate, ProjectUpdate]):
    """Async repository for Project model with custom methods."""

    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)

    async def get_by_user(self, user_id: int) -> List[Project]:
        """Get all projects for a user."""
        stmt = select(Project).where(Project.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
