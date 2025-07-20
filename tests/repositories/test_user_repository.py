# ruff: noqa: S101, S106, S105
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


def test_create_user(db: Session) -> None:
    """Test creating a user"""
    # Arrange
    repo = UserRepository(db)
    user_in = UserCreate(email="newuser@example.com", password="testpassword")

    # Act
    user = repo.create_user(user_in)

    # Assert
    assert user.email == "newuser@example.com"
    assert verify_password("testpassword", user.hashed_password)
    assert user.is_active is True
    assert user.is_superuser is False


def test_get_by_email(db: Session, test_user: User) -> None:
    """Test getting a user by email"""
    # Arrange
    repo = UserRepository(db)

    # Act
    user = repo.get_by_email(test_user.email)

    # Assert
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


def test_get_by_email_not_found(db: Session) -> None:
    """Test getting a user by email when the user doesn't exist"""
    # Arrange
    repo = UserRepository(db)

    # Act
    user = repo.get_by_email("nonexistent@example.com")

    # Assert
    assert user is None


def test_get_by_id(db: Session, test_user: User) -> None:
    """Test getting a user by ID"""
    # Arrange
    repo = UserRepository(db)

    # Act
    user = repo.get(test_user.id)

    # Assert
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


def test_update_password(db: Session, test_user: User) -> None:
    """Test updating a user's password"""
    # Arrange
    repo = UserRepository(db)
    new_password = "newpassword123"

    # Act
    user = repo.update_password(test_user, new_password)

    # Assert
    assert user is not None
    assert verify_password(new_password, user.hashed_password)


def test_is_active(db: Session, test_user: User) -> None:
    """Test checking if a user is active"""
    # Arrange
    repo = UserRepository(db)

    # Act
    is_active = repo.is_active(test_user)

    # Assert
    assert is_active is True

    test_user.is_active = False
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    is_active = repo.is_active(test_user)
    assert is_active is False


def test_is_superuser(db: Session, test_user: User, test_superuser: User) -> None:
    """Test checking if a user is a superuser"""
    # Arrange
    repo = UserRepository(db)

    # Act & Assert
    assert repo.is_superuser(test_user) is False
    assert repo.is_superuser(test_superuser) is True
