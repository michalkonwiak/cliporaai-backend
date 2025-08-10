# ruff: noqa: S101, S106, S105
from datetime import datetime
from typing import no_type_check

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


@pytest.mark.asyncio
@no_type_check
async def test_register_new_user(db: AsyncSession) -> None:
    """Test registering a new user"""
    # Arrange
    auth_service = AuthService(db)
    user_data = UserCreate(
        email="newuser@example.com",
        password="testpassword",
        first_name="John",
        last_name="Doe",
    )

    # Act
    user = await auth_service.register(user_data)

    # Assert
    assert user.email == "newuser@example.com"
    assert verify_password("testpassword", user.hashed_password)
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.created_at is not None
    assert isinstance(user.created_at, datetime)
    assert user.updated_at is None
    assert user.last_login_at is None


@pytest.mark.asyncio
async def test_register_existing_email(db: AsyncSession, test_user: User) -> None:
    """Test registering a user with an existing email"""
    # Arrange
    auth_service = AuthService(db)
    user_data = UserCreate(email=test_user.email, password="testpassword")

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.register(user_data)

    assert excinfo.value.status_code == 400
    assert "Email already registered" in excinfo.value.detail


@pytest.mark.asyncio
async def test_authenticate_valid_credentials(db: AsyncSession, test_user: User) -> None:
    """Test authenticating a user with valid credentials"""
    # Arrange
    auth_service = AuthService(db)

    # Act
    user = await auth_service.authenticate(test_user.email, "password123")

    # Assert
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_authenticate_invalid_email(db: AsyncSession) -> None:
    """Test authenticating a user with an invalid email"""
    # Arrange
    auth_service = AuthService(db)

    # Act
    user = await auth_service.authenticate("nonexistent@example.com", "password123")

    # Assert
    assert user is None


@pytest.mark.asyncio
async def test_authenticate_invalid_password(db: AsyncSession, test_user: User) -> None:
    """Test authenticating a user with an invalid password"""
    # Arrange
    auth_service = AuthService(db)

    # Act
    user = await auth_service.authenticate(test_user.email, "wrongpassword")

    # Assert
    assert user is None


@pytest.mark.asyncio
async def test_create_token(db: AsyncSession, test_user: User) -> None:
    """Test creating a token for a user"""
    # Arrange
    auth_service = AuthService(db)

    # Act
    token = await auth_service.create_token(test_user)

    # Assert
    assert token.access_token is not None
    assert token.token_type == "bearer"


@pytest.mark.asyncio
async def test_get_current_user_valid_token(db: AsyncSession, test_user: User) -> None:
    """Test getting the current user with a valid token"""
    # Arrange
    auth_service = AuthService(db)
    token = await auth_service.create_token(test_user)

    # Act
    user = await auth_service.get_current_user(token.access_token)

    # Assert
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_get_current_user_inactive_user(db: AsyncSession, test_user: User) -> None:
    """Test getting the current user when the user is inactive"""
    # Arrange
    auth_service = AuthService(db)
    token = await auth_service.create_token(test_user)

    # Make the user inactive
    test_user.is_active = False
    db.add(test_user)
    await db.commit()
    await db.refresh(test_user)

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.get_current_user(token.access_token)

    assert excinfo.value.status_code == 401
    assert "Inactive user" in excinfo.value.detail


@pytest.mark.asyncio
@no_type_check
async def test_register_user_with_minimal_data(db: AsyncSession) -> None:
    """Test registering a user with only required fields"""
    # Arrange
    auth_service = AuthService(db)
    user_data = UserCreate(email="minimal@example.com", password="testpassword")

    # Act
    user = await auth_service.register(user_data)

    # Assert
    assert user.email == "minimal@example.com"
    assert user.first_name is None
    assert user.last_name is None
    assert user.created_at is not None
    assert user.updated_at is None
    assert user.last_login_at is None


@pytest.mark.asyncio
async def test_register_user_with_profile_fields(db: AsyncSession) -> None:
    """Test registering a user with profile information"""
    # Arrange
    auth_service = AuthService(db)
    user_data = UserCreate(
        email="profile@example.com",
        password="testpassword",
        first_name="Jane",
        last_name="Smith",
    )

    # Act
    user = await auth_service.register(user_data)

    # Assert
    assert user.email == "profile@example.com"
    assert user.first_name == "Jane"
    assert user.last_name == "Smith"
    assert verify_password("testpassword", user.hashed_password)


@pytest.mark.asyncio
async def test_create_token_includes_user_id(db: AsyncSession, test_user: User) -> None:
    """Test that created token contains user ID in payload"""
    # Arrange
    auth_service = AuthService(db)

    # Act
    token = await auth_service.create_token(test_user)

    # Assert
    assert token.access_token is not None
    assert token.token_type == "bearer"

    # Verify token contains user ID by decoding it
    from app.core.security import decode_access_token

    payload = decode_access_token(token.access_token)
    assert payload.get("sub") == str(test_user.id)


@pytest.mark.asyncio
async def test_get_current_user_with_profile_data(db: AsyncSession) -> None:
    """Test getting current user includes profile data"""
    # Arrange
    auth_service = AuthService(db)
    user_data = UserCreate(
        email="userprofile@example.com",
        password="testpassword",
        first_name="Profile",
        last_name="User",
    )
    user = await auth_service.register(user_data)
    token = await auth_service.create_token(user)

    # Act
    current_user = await auth_service.get_current_user(token.access_token)

    # Assert
    assert current_user.id == user.id
    assert current_user.email == user.email
    assert current_user.first_name == "Profile"
    assert current_user.last_name == "User"
    assert current_user.created_at is not None
    assert current_user.last_login_at is None
