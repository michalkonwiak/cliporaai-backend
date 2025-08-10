from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any

from app.models.project import Project, ProjectStatus, ProjectType as ModelProjectType
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.repositories.project_repository import ProjectRepository


class ProjectService:
    """
    Service for project operations
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repository = ProjectRepository(db)

    async def get_project(self, project_id: int, user_id: int) -> Project:
        project = await self.project_repository.get(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found",
            )
        if project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project",
            )
        return project

    async def list_projects(self, user_id: int) -> List[Project]:
        return await self.project_repository.get_by_user(user_id)

    async def create_project(self, project_in: ProjectCreate, user_id: int) -> Project:
        # Defaults and enum mapping
        data = project_in.model_dump()
        # Map provided string to model enum
        data["project_type"] = ModelProjectType[str(project_in.project_type).upper()]
        data.update({
            "user_id": user_id,
            "status": ProjectStatus.DRAFT,
            "total_duration": 0.0,
            "processing_progress": 0.0,
        })
        return await self.project_repository.create(data)

    async def update_project(self, project_id: int, update_data: ProjectUpdate, user_id: int) -> Project:
        project = await self.get_project(project_id, user_id)
        payload: dict[str, Any] = (
            update_data.model_dump(exclude_unset=True)
            if hasattr(update_data, "model_dump")
            else {}
        )
        # Map enum if provided
        if update_data.project_type is not None:
            payload["project_type"] = ModelProjectType[str(update_data.project_type).upper()]
        return await self.project_repository.update(project, payload)

    async def delete_project(self, project_id: int, user_id: int) -> None:
        project = await self.get_project(project_id, user_id)
        await self.project_repository.delete(project.id)
        return None
