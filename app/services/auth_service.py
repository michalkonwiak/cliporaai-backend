from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import Token, TokenPayload, UserCreate


class AuthService:
    """
    Service for authentication operations
    """

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def register(self, user_data: UserCreate) -> User:
        """
        Register a new user
        """
        existing_user = self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
            )

        return self.user_repository.create_user(user_data)

    def authenticate(self, email: str, password: str) -> User | None:
        """
        Authenticate a user by email and password
        """
        user = self.user_repository.get_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    def create_token(self, user: User) -> Token:
        """
        Create access token for user
        """
        token_data = {"sub": str(user.id)}

        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(data=token_data, expires_delta=expires_delta)

        return Token(access_token=access_token)

    def get_current_user(self, token: str) -> User:
        """
        Get current user from token
        """
        try:
            payload = decode_access_token(token)
            token_data = TokenPayload(**payload)

            if token_data.sub is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )

            user = self.user_repository.get(int(token_data.sub))
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )

            if not self.user_repository.is_active(user):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Inactive user",
                )

            return user

        except (ValueError, HTTPException) as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            ) from None
