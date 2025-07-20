from typing import Any, Protocol, TypeVar, cast

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

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


class BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]:
    """
    Base repository with default CRUD operations
    """

    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, obj_id: int) -> ModelType | None:
        """Get a single record by id"""
        model = cast(type[ModelProtocol], self.model)
        return self.db.query(self.model).filter(model.id == obj_id).first()

    def get_by(self, **kwargs: Any) -> ModelType | None:
        """Get a single record by arbitrary filters"""
        query = self.db.query(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.first()

    def list(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Get multiple records with pagination"""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: CreateSchemaType | dict[str, Any]) -> ModelType:
        """Create a new record"""
        obj_data = obj_in if isinstance(obj_in, dict) else jsonable_encoder(obj_in)
        
        db_obj: ModelType = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        """Update an existing record"""
        obj_data = jsonable_encoder(db_obj)
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            obj_with_dict = cast(HasDict, obj_in)
            update_data = obj_with_dict.dict(exclude_unset=True)
            
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, obj_id: int) -> ModelType:
        """Delete a record"""
        obj = self.db.query(self.model).get(obj_id)
        if obj is None:
            raise ValueError(f"Record with id {obj_id} not found")
        db_obj: ModelType = obj
        self.db.delete(db_obj)
        self.db.commit()
        return db_obj