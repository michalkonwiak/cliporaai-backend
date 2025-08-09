from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token, verify_password, hash_password
from app.models.user import User
from app.schemas.user import Token, TokenPayload, UserCreate


class AuthService:
    """
    Service for authentication operations.
    """

    def __init__(self, db: Session | AsyncSession):
        self.db = db

    async def register(self, user_data: UserCreate) -> User:
        """Register a new user."""
        assert isinstance(self.db, AsyncSession), "Async register requires AsyncSession"
        result = await self.db.execute(select(User).where(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        user_dict = user_data.model_dump(exclude={"password"})
        db_user = User(**user_dict, hashed_password=hash_password(user_data.password))
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def authenticate(self, email: str, password: str) -> User | None:
        """Authenticate by email and password"""
        assert isinstance(self.db, AsyncSession), "Async authenticate requires AsyncSession"
        result = await self.db.execute(select(User).where(User.email == email))
        user: User | None = result.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def create_token(self, user: User) -> Token:
        """Create access token for user."""
        token_data = {"sub": str(user.id)}
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(data=token_data, expires_delta=expires_delta)
        return Token(access_token=access_token)

    async def get_current_user(self, token: str) -> User:
        """Get current user from token."""
        assert isinstance(self.db, AsyncSession), "Async get_current_user requires AsyncSession"
        payload = decode_access_token(token)
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        result = await self.db.execute(select(User).where(User.id == int(token_data.sub)))
        user: User | None = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
            )
        return user
