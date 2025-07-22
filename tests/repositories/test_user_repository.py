# ruff: noqa: S101, S106, S105
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


def test_create_user(db: Session) -> None:
    """Test creating a user"""
    # Arrange
    repo = UserRepository(db)
    user_in = UserCreate(
        email="newuser@example.com",
        password="testpassword",
        first_name="John",
        last_name="Doe",
    )

    # Act
    user = repo.create_user(user_in)

    # Assert
    assert user.email == "newuser@example.com"
    assert verify_password("testpassword", user.hashed_password)
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.created_at is not None
    assert isinstance(user.created_at, datetime)
    assert user.updated_at is None  # Should be None on creation
    assert user.last_login_at is None


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

    test_user.is_active = False  # type: ignore[assignment]
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


def test_create_user_with_minimal_data(db: Session) -> None:
    """Test creating a user with only required fields"""
    # Arrange
    repo = UserRepository(db)
    user_in = UserCreate(email="minimal@example.com", password="testpassword")

    # Act
    user = repo.create_user(user_in)

    # Assert
    assert user.email == "minimal@example.com"
    assert verify_password("testpassword", user.hashed_password)
    assert user.first_name is None
    assert user.last_name is None
    assert user.created_at is not None
    assert user.updated_at is None
    assert user.last_login_at is None


def test_user_timestamps_on_update(db: Session, test_user: User) -> None:
    """Test that updated_at is set when user is updated"""
    # Arrange
    original_updated_at = test_user.updated_at

    # Act
    test_user.first_name = "Updated Name"  # type: ignore[assignment]
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    # Assert
    assert test_user.updated_at is not None
    assert test_user.updated_at != original_updated_at
    assert isinstance(test_user.updated_at, datetime)


def test_user_profile_fields(db: Session) -> None:
    """Test user profile fields functionality"""
    # Arrange
    repo = UserRepository(db)
    user_in = UserCreate(
        email="profile@example.com",
        password="testpassword",
        first_name="Jane",
        last_name="Smith",
    )

    # Act
    user = repo.create_user(user_in)

    # Assert
    assert user.first_name == "Jane"
    assert user.last_name == "Smith"

    user.first_name = "Janet"  # type: ignore[assignment]
    user.last_name = "Johnson"  # type: ignore[assignment]
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.first_name == "Janet"
    assert user.last_name == "Johnson"


def test_user_last_login_tracking(db: Session, test_user: User) -> None:
    """Test that last_login_at can be set and updated"""
    # Arrange
    login_time = datetime.utcnow()
    assert test_user.last_login_at is None

    # Ac
    test_user.last_login_at = login_time  # type: ignore[assignment]
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    # Assert
    assert test_user.last_login_at is not None
    assert isinstance(test_user.last_login_at, datetime)
    # Allow for small time differences in comparison
    time_diff = abs((test_user.last_login_at - login_time).total_seconds())
    assert time_diff < 1  # Less than 1 second difference
