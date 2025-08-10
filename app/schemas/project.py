from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_serializer


class ProjectType(str, Enum):
    DYNAMIC = "dynamic"
    CINEMATIC = "cinematic"
    DOCUMENTARY = "documentary"
    SOCIAL = "social"
    CUSTOM = "custom"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPORTED = "exported"


class ProjectBase(BaseModel):
    """Base schema for project metadata."""
    
    name: str
    description: str | None = None
    project_type: str = ProjectType.DYNAMIC.value


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass


class ProjectRead(ProjectBase):
    """Schema for reading project metadata."""
    
    id: int
    user_id: int
    status: str
    total_duration: float
    processing_progress: float
    timeline_data: dict | None = None
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None

    @staticmethod
    def _to_lower_str(value: object) -> str:
        try:
            return str(getattr(value, "value", value)).lower()
        except Exception:
            return str(value).lower()

    @field_serializer("status", "project_type")
    def serialize_enums(self, value: object) -> str:
        return self._to_lower_str(value)
    
    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    """Schema for updating project metadata."""
    
    name: str | None = None
    description: str | None = None
    project_type: str | None = None
    timeline_data: dict | None = None