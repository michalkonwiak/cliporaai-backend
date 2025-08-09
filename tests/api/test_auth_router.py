from datetime import datetime
import pytest
import httpx

from app.models.user import User
from pytest import mark


@mark.asyncio
async def test_register_new_user(client: httpx.AsyncClient) -> None:
    """Test registering a new user via the API"""
    import json
    user_data = {
        "email": "newuser@example.com",
        "password": "testpassword",
        "first_name": "John",
        "last_name": "Doe",
    }

    # Act - Try with content parameter and explicit content-type header
    headers = {"Content-Type": "application/json"}
    response = await client.post(
        "/api/v1/auth/register", 
        content=json.dumps(user_data).encode('utf-8'),
        headers=headers
    )
    
    # Print response for debugging
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content.decode()}")
    print(f"Response headers: {response.headers}")
    print(f"Request headers: {headers}")

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert "id" in data
    assert data["is_active"] is True
    assert data["is_superuser"] is False
    assert "created_at" in data
    assert data["updated_at"] is None
    assert data["last_login_at"] is None


@pytest.mark.asyncio
async def test_register_existing_email(client: httpx.AsyncClient, test_user: User) -> None:
    """Test registering a user with an existing email via the API"""
    # Arrange
    user_data = {"email": test_user.email, "password": "testpassword"}

    # Act
    response = await client.post("/api/v1/auth/register", json=user_data)

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Email already registered" in data["detail"]


@pytest.mark.asyncio
async def test_login_valid_credentials(client: httpx.AsyncClient, test_user: User) -> None:
    """Test logging in with valid credentials via the API"""
    # Arrange
    login_data = {"username": test_user.email, "password": "password123"}

    # Act
    response = await client.post("/api/v1/auth/login", data=login_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: httpx.AsyncClient) -> None:
    """Test logging in with invalid credentials via the API"""
    # Arrange
    login_data = {"username": "nonexistent@example.com", "password": "wrongpassword"}

    # Act
    response = await client.post("/api/v1/auth/login", data=login_data)

    # Assert
    assert response.status_code == 401
    data = response.json()
    assert "Incorrect email or password" in data["detail"]


@pytest.mark.asyncio
async def test_get_current_user(client: httpx.AsyncClient, token_headers: dict) -> None:
    """Test getting the current user via the API"""
    # Act
    response = await client.get("/api/v1/auth/me", headers=token_headers)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "id" in data
    assert "is_active" in data
    assert "is_superuser" in data
    assert "created_at" in data
    assert "updated_at" in data  # May be None or have a value
    assert "last_login_at" in data  # May be None or have a value


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: httpx.AsyncClient) -> None:
    """Test getting the current user without a token via the API"""
    # Act
    response = await client.get("/api/v1/auth/me")

    # Assert
    assert response.status_code == 401
    data = response.json()
    assert "Not authenticated" in data["detail"]


@pytest.mark.asyncio
async def test_register_user_minimal_data(client: httpx.AsyncClient) -> None:
    """Test registering a user with only required fields via the API"""
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
    assert "id" in data
    assert data["is_active"] is True
    assert data["is_superuser"] is False
    assert "created_at" in data
    assert data["updated_at"] is None
    assert data["last_login_at"] is None


@pytest.mark.asyncio
async def test_register_user_with_profile_fields(client: httpx.AsyncClient) -> None:
    """Test registering a user with profile information via the API"""
    # Arrange
    user_data = {
        "email": "profile@example.com",
        "password": "testpassword",
        "first_name": "Jane",
        "last_name": "Smith",
    }

    # Act
    response = await client.post("/api/v1/auth/register", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "profile@example.com"
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Smith"
    assert "id" in data
    assert data["is_active"] is True
    assert data["is_superuser"] is False


@pytest.mark.asyncio
async def test_register_user_partial_profile(client: httpx.AsyncClient) -> None:
    """Test registering a user with only first name via the API"""
    # Arrange
    user_data = {
        "email": "partial@example.com",
        "password": "testpassword",
        "first_name": "Only",
    }

    # Act
    response = await client.post("/api/v1/auth/register", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "partial@example.com"
    assert data["first_name"] == "Only"
    assert data["last_name"] is None


@pytest.mark.asyncio
async def test_response_includes_timestamps(client: httpx.AsyncClient) -> None:
    """Test that user registration response includes proper timestamps"""
    # Arrange
    user_data = {
        "email": "timestamps@example.com",
        "password": "testpassword",
        "first_name": "Timestamp",
        "last_name": "Test",
    }

    # Act
    response = await client.post("/api/v1/auth/register", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()

    # Check that created_at is a valid datetime string
    assert "created_at" in data
    created_at_str = data["created_at"]
    # Should be able to parse as ISO datetime
    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    assert isinstance(created_at, datetime)

    # updated_at and last_login_at should be None for new user
    assert data["updated_at"] is None
    assert data["last_login_at"] is None
