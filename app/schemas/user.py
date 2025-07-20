
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None

class UserRead(UserBase):
    id: int
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True

TOKEN_TYPE_BEARER = "bearer"  # noqa: S105

class Token(BaseModel):
    access_token: str
    token_type: str = TOKEN_TYPE_BEARER

class TokenPayload(BaseModel):
    sub: str | None = None
