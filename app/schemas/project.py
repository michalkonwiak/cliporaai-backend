from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel


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
    project_type: ProjectType = ProjectType.DYNAMIC


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass


class ProjectRead(ProjectBase):
    """Schema for reading project metadata."""
    
    id: int
    user_id: int
    status: str  # Changed from ProjectStatus to str
    total_duration: float
    processing_progress: float
    timeline_data: Optional[Dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    """Schema for updating project metadata."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    timeline_data: Optional[Dict] = None