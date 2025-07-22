from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None


class UserCreate(UserBase):
    password: str
    first_name: str | None = None
    last_name: str | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserRead(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime | None = None
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


TOKEN_TYPE_BEARER = "bearer"  # noqa: S105


class Token(BaseModel):
    access_token: str
    token_type: str = TOKEN_TYPE_BEARER


class TokenPayload(BaseModel):
    sub: str | None = None
