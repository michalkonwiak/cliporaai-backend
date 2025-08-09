from typing import Any, Generic, Protocol, TypeVar, cast

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


class HasID(Protocol):
    id: Any


class HasDict(Protocol):
    def dict(self, **kwargs: Any) -> dict[str, Any]: ...


class ModelProtocol(HasID, Protocol):
    pass


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Async base repository with default CRUD operations."""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, obj_id: int) -> ModelType | None:
        """Get a single record by id."""
        return await self.db.get(self.model, obj_id)

    async def get_by(self, **kwargs: Any) -> ModelType | None:
        """Get a single record by arbitrary filters."""
        # Use the model class directly in select() which is the SQLAlchemy 2.0 pattern
        stmt = select(self.model)  # type: ignore
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.db.execute(stmt)
        obj = result.scalar_one_or_none()
        return cast(ModelType | None, obj)

    async def list(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Get multiple records with pagination."""
        # Use the model class directly in select() which is the SQLAlchemy 2.0 pattern
        stmt = select(self.model)  # type: ignore
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        objects = list(result.scalars().all())
        return cast(list[ModelType], objects)

    async def create(self, obj_in: CreateSchemaType | dict[str, Any]) -> ModelType:
        """Create a new record."""
        obj_data = obj_in if isinstance(obj_in, dict) else jsonable_encoder(obj_in)
        db_obj: ModelType = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(
        self, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        """Update an existing record."""
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Pydantic v2 compatibility
            if hasattr(obj_in, "model_dump"):
                update_data = obj_in.model_dump(exclude_unset=True)
            else:
                obj_with_dict = cast(HasDict, obj_in)
                update_data = obj_with_dict.dict(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, obj_id: int) -> ModelType:
        """Delete a record."""
        obj = await self.get(obj_id)
        if obj is None:
            raise ValueError(f"Record with id {obj_id} not found")
        db_obj: ModelType = obj
        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj
