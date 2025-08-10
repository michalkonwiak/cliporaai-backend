from datetime import datetime
from enum import Enum
from typing import Dict, Optional

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
    description: Optional[str] = None
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
    timeline_data: Optional[Dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

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
    
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    timeline_data: Optional[Dict] = None