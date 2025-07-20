from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    Repository for User model with custom methods for user-specific operations
    """

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        """
        Get a user by email
        """
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, user_in: UserCreate) -> User:
        """
        Create a new user with hashed password
        """
        user_data = user_in.model_dump(exclude={"password"})
        db_user = User(
            **user_data,
            hashed_password=hash_password(user_in.password)
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
        
    def update_password(self, user: User, new_password: str) -> User:
        """
        Update user's password
        """
        hashed_password = hash_password(new_password)
        user.hashed_password = hashed_password
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
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