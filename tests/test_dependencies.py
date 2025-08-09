# ruff: noqa: S101, S106, S105
from datetime import datetime
import pytest
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from typing import no_type_check

from app.models.user import User
from app.services.auth_service import AuthService
from app.core.security import decode_access_token


@pytest.mark.asyncio
@no_type_check
async def test_user_creation_with_timestamps(db: AsyncSession) -> None:
    """Test that user creation includes proper timestamps"""
    # Arrange
    auth_service = AuthService(db)
    from app.schemas.user import UserCreate

    user_data = UserCreate(
        email="timestamp@example.com",
        password="testpassword",
        first_name="Time",
        last_name="Stamp",
    )

    # Act
    user = await auth_service.register(user_data)

    # Assert
    assert user.created_at is not None
    assert isinstance(user.created_at, datetime)
    assert user.updated_at is None  # Should be None on creation  # type: ignore[unreachable]
    assert user.last_login_at is None  # Should be None until first login  # type: ignore[unreachable]
    assert user.first_name == "Time"
    assert user.last_name == "Stamp"


@pytest.mark.asyncio
async def test_user_profile_fields_in_response(client: httpx.AsyncClient) -> None:
    """Test that API responses include new profile fields"""
    # Arrange
    user_data = {
        "email": "profile@example.com",
        "password": "testpassword",
        "first_name": "Profile",
        "last_name": "Test",
    }

    # Act - Register user
    response = await client.post("/api/v1/auth/register", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()

    # Check profile fields
    assert data["first_name"] == "Profile"
    assert data["last_name"] == "Test"

    # Check timestamps
    assert "created_at" in data
    assert data["created_at"] is not None
    assert data["updated_at"] is None
    assert data["last_login_at"] is None


@pytest.mark.asyncio
async def test_minimal_user_registration(client: httpx.AsyncClient) -> None:
    """Test registration with only required fields"""
    # Arrange
    user_data = {"email": "minimal@example.com", "password": "testpassword"}

    # Act
    response = await client.post("/api/v1/auth/register", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()

    assert data["email"] == "minimal@example.com"
    assert data["first_name"] is None
    assert data["last_name"] is None
    assert data["is_active"] is True
    assert data["is_superuser"] is False


@pytest.mark.asyncio
async def test_user_me_endpoint_returns_profile_data(client: httpx.AsyncClient) -> None:
    """Test that /me endpoint returns complete user profile"""
    # Arrange - Register user with profile data
    user_data = {
        "email": "metest@example.com",
        "password": "testpassword",
        "first_name": "Me",
        "last_name": "Test",
    }

    register_response = await client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 201

    # Login to get token
    login_data = {"username": "metest@example.com", "password": "testpassword"}
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token_data = login_response.json()

    # Act - Call /me endpoint
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)

    # Assert
    assert me_response.status_code == 200
    me_data = me_response.json()

    # Verify profile data
    assert me_data["email"] == "metest@example.com"
    assert me_data["first_name"] == "Me"
    assert me_data["last_name"] == "Test"

    # Verify timestamps are included
    assert "created_at" in me_data
    assert "updated_at" in me_data
    assert "last_login_at" in me_data


@pytest.mark.asyncio
async def test_token_creation_and_validation(db: AsyncSession, test_user: User) -> None:
    """Test token creation and payload validation"""
    # Arrange
    auth_service = AuthService(db)

    # Act - Create token
    token = await auth_service.create_token(test_user)

    # Assert token structure
    assert token.access_token is not None
    assert token.token_type == "bearer"

    # Verify token payload
    payload = decode_access_token(token.access_token)
    assert payload["sub"] == str(test_user.id)
    assert "exp" in payload


@pytest.mark.asyncio
async def test_user_authentication_flow_complete(client: httpx.AsyncClient) -> None:
    """Complete authentication flow test with profile data"""
    # Step 1: Register user
    user_data = {
        "email": "flow@example.com",
        "password": "testpassword",
        "first_name": "Flow",
        "last_name": "Test",
    }

    register_response = await client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 201
    register_data = register_response.json()

    # Verify initial state
    assert register_data["last_login_at"] is None
    user_id = register_data["id"]

    # Step 2: Login
    login_data = {"username": "flow@example.com", "password": "testpassword"}
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token_data = login_response.json()

    # Step 3: Access protected endpoint
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.json()

    # Verify user data is complete
    assert me_data["id"] == user_id
    assert me_data["email"] == "flow@example.com"
    assert me_data["first_name"] == "Flow"
    assert me_data["last_name"] == "Test"
    assert me_data["is_active"] is True


@pytest.mark.asyncio
async def test_user_with_partial_profile_data(client: httpx.AsyncClient) -> None:
    """Test user registration with only first name"""
    # Arrange
    user_data = {
        "email": "partial@example.com",
        "password": "testpassword",
        "first_name": "OnlyFirst",
    }

    # Act
    response = await client.post("/api/v1/auth/register", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()

    assert data["first_name"] == "OnlyFirst"
    assert data["last_name"] is None


@pytest.mark.asyncio
async def test_timestamp_format_in_api_response(client: httpx.AsyncClient) -> None:
    """Test that timestamps are properly formatted in API responses"""
    # Arrange
    user_data = {
        "email": "timestamp@example.com",
        "password": "testpassword",
        "first_name": "Time",
        "last_name": "Check",
    }

    # Act
    response = await client.post("/api/v1/auth/register", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()

    # Verify created_at is a valid ISO datetime string
    created_at_str = data["created_at"]
    assert created_at_str is not None

    # Should be parseable as datetime
    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    assert isinstance(created_at, datetime)


@pytest.mark.asyncio
@no_type_check
async def test_user_model_with_all_fields(db: AsyncSession) -> None:
    """Test user model creation with all profile fields"""
    # Arrange
    from app.core.security import hash_password

    user_data = {
        "email": "complete@example.com",
        "hashed_password": hash_password("testpassword"),
        "first_name": "Complete",
        "last_name": "User",
        "is_active": True,
        "is_superuser": False,
    }

    # Act
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Assert
    assert user.email == "complete@example.com"
    assert user.first_name == "Complete"
    assert user.last_name == "User"
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.created_at is not None
    assert user.updated_at is None
    assert user.last_login_at is None


@pytest.mark.asyncio
async def test_invalid_token_handling(client: httpx.AsyncClient) -> None:
    """Test API behavior with invalid tokens"""
    # Arrange
    invalid_headers = {"Authorization": "Bearer invalid-token"}

    # Act
    response = await client.get("/api/v1/auth/me", headers=invalid_headers)

    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_missing_authorization_header(client: httpx.AsyncClient) -> None:
    """Test API behavior without authorization header"""
    # Act
    response = await client.get("/api/v1/auth/me")

    # Assert
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
