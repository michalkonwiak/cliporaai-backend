from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    Repository for User model with custom methods for user-specific operations
    """

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return cast(User | None, result.scalar_one_or_none())

    async def create_user(self, user_in: UserCreate) -> User:
        """Create a new user with hashed password."""
        user_data = user_in.model_dump(exclude={"password"})
        db_user = User(**user_data, hashed_password=hash_password(user_in.password))
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def update_password(self, user: User, new_password: str) -> User:
        """Update user's password."""
        hashed_password = hash_password(new_password)
        user.hashed_password = hashed_password
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    def is_active(self, user: User) -> bool:
        """
        Check if user is active
        """
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """
        Check if user is superuser
        """
        return user.is_superuser
