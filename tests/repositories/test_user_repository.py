# ruff: noqa: S101, S106, S105
from datetime import datetime
from typing import no_type_check

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


@pytest.mark.asyncio
@no_type_check
async def test_create_user(db: AsyncSession) -> None:
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
    user = await repo.create_user(user_in)

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


@pytest.mark.asyncio
async def test_get_by_email(db: AsyncSession, test_user: User) -> None:
    """Test getting a user by email"""
    # Arrange
    repo = UserRepository(db)

    # Act
    user = await repo.get_by_email(test_user.email)

    # Assert
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_get_by_email_not_found(db: AsyncSession) -> None:
    """Test getting a user by email when the user doesn't exist"""
    # Arrange
    repo = UserRepository(db)

    # Act
    user = await repo.get_by_email("nonexistent@example.com")

    # Assert
    assert user is None


@pytest.mark.asyncio
async def test_get_by_id(db: AsyncSession, test_user: User) -> None:
    """Test getting a user by ID"""
    # Arrange
    repo = UserRepository(db)

    # Act
    user = await repo.get(test_user.id)

    # Assert
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_update_password(db: AsyncSession, test_user: User) -> None:
    """Test updating a user's password"""
    # Arrange
    repo = UserRepository(db)
    new_password = "newpassword123"

    # Act
    user = await repo.update_password(test_user, new_password)

    # Assert
    assert user is not None
    assert verify_password(new_password, user.hashed_password)


def test_is_active(db: AsyncSession, test_user: User) -> None:
    """Test checking if a user is active"""
    # Arrange
    repo = UserRepository(db)

    # Act
    is_active = repo.is_active(test_user)

    # Assert
    assert is_active is True

    test_user.is_active = False
    # No DB write needed for boolean property check

    is_active = repo.is_active(test_user)
    assert is_active is False


def test_is_superuser(db: AsyncSession, test_user: User, test_superuser: User) -> None:
    """Test checking if a user is a superuser"""
    # Arrange
    repo = UserRepository(db)

    # Act & Assert
    assert repo.is_superuser(test_user) is False
    assert repo.is_superuser(test_superuser) is True


@pytest.mark.asyncio
@no_type_check
async def test_create_user_with_minimal_data(db: AsyncSession) -> None:
    """Test creating a user with only required fields"""
    # Arrange
    repo = UserRepository(db)
    user_in = UserCreate(email="minimal@example.com", password="testpassword")

    # Act
    user = await repo.create_user(user_in)

    # Assert
    assert user.email == "minimal@example.com"
    assert verify_password("testpassword", user.hashed_password)
    assert user.first_name is None
    assert user.last_name is None
    assert user.created_at is not None
    assert user.updated_at is None
    assert user.last_login_at is None


@pytest.mark.asyncio
async def test_user_timestamps_on_update(db: AsyncSession, test_user: User) -> None:
    """Test that updated_at is set when user is updated"""
    # Arrange
    original_updated_at = test_user.updated_at

    # Act
    test_user.first_name = "Updated Name"
    db.add(test_user)
    await db.commit()
    await db.refresh(test_user)

    # Assert
    assert test_user.updated_at is not None
    assert test_user.updated_at != original_updated_at
    assert isinstance(test_user.updated_at, datetime)


@pytest.mark.asyncio
async def test_user_profile_fields(db: AsyncSession) -> None:
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
    user = await repo.create_user(user_in)

    # Assert
    assert user.first_name == "Jane"
    assert user.last_name == "Smith"

    user.first_name = "Janet"
    user.last_name = "Johnson"
    db.add(user)
    await db.commit()
    await db.refresh(user)

    assert user.first_name == "Janet"
    assert user.last_name == "Johnson"


@pytest.mark.asyncio
@no_type_check
async def test_user_last_login_tracking(db: AsyncSession, test_user: User) -> None:
    """Test that last_login_at can be set and updated"""
    # Arrange
    login_time = datetime.utcnow()
    assert test_user.last_login_at is None

    # Ac
    test_user.last_login_at = login_time
    db.add(test_user)
    await db.commit()
    await db.refresh(test_user)

    # Assert
    assert test_user.last_login_at is not None
    assert isinstance(test_user.last_login_at, datetime)
    # Allow for small time differences in comparison
    time_diff = abs((test_user.last_login_at - login_time).total_seconds())
    assert time_diff < 1  # Less than 1 second difference
