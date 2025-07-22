# ruff: noqa: S101, S105
from datetime import datetime
from fastapi.testclient import TestClient

from app.models.user import User


def test_register_new_user(client: TestClient) -> None:
    """Test registering a new user via the API"""
    # Arrange
    user_data = {
        "email": "newuser@example.com",
        "password": "testpassword",
        "first_name": "John",
        "last_name": "Doe",
    }

    # Act
    response = client.post("/api/v1/auth/register", json=user_data)

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


def test_register_existing_email(client: TestClient, test_user: User) -> None:
    """Test registering a user with an existing email via the API"""
    # Arrange
    user_data = {"email": test_user.email, "password": "testpassword"}

    # Act
    response = client.post("/api/v1/auth/register", json=user_data)

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Email already registered" in data["detail"]


def test_login_valid_credentials(client: TestClient, test_user: User) -> None:
    """Test logging in with valid credentials via the API"""
    # Arrange
    login_data = {"username": test_user.email, "password": "password123"}

    # Act
    response = client.post("/api/v1/auth/login", data=login_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient) -> None:
    """Test logging in with invalid credentials via the API"""
    # Arrange
    login_data = {"username": "nonexistent@example.com", "password": "wrongpassword"}

    # Act
    response = client.post("/api/v1/auth/login", data=login_data)

    # Assert
    assert response.status_code == 401
    data = response.json()
    assert "Incorrect email or password" in data["detail"]


def test_get_current_user(client: TestClient, token_headers: dict) -> None:
    """Test getting the current user via the API"""
    # Act
    response = client.get("/api/v1/auth/me", headers=token_headers)

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


def test_get_current_user_no_token(client: TestClient) -> None:
    """Test getting the current user without a token via the API"""
    # Act
    response = client.get("/api/v1/auth/me")

    # Assert
    assert response.status_code == 401
    data = response.json()
    assert "Not authenticated" in data["detail"]


def test_register_user_minimal_data(client: TestClient) -> None:
    """Test registering a user with only required fields via the API"""
    # Arrange
    user_data = {"email": "minimal@example.com", "password": "testpassword"}

    # Act
    response = client.post("/api/v1/auth/register", json=user_data)

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


def test_register_user_with_profile_fields(client: TestClient) -> None:
    """Test registering a user with profile information via the API"""
    # Arrange
    user_data = {
        "email": "profile@example.com",
        "password": "testpassword",
        "first_name": "Jane",
        "last_name": "Smith",
    }

    # Act
    response = client.post("/api/v1/auth/register", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "profile@example.com"
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Smith"
    assert "id" in data
    assert data["is_active"] is True
    assert data["is_superuser"] is False


def test_register_user_partial_profile(client: TestClient) -> None:
    """Test registering a user with only first name via the API"""
    # Arrange
    user_data = {
        "email": "partial@example.com",
        "password": "testpassword",
        "first_name": "Only",
    }

    # Act
    response = client.post("/api/v1/auth/register", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "partial@example.com"
    assert data["first_name"] == "Only"
    assert data["last_name"] is None


def test_response_includes_timestamps(client: TestClient) -> None:
    """Test that user registration response includes proper timestamps"""
    # Arrange
    user_data = {
        "email": "timestamps@example.com",
        "password": "testpassword",
        "first_name": "Timestamp",
        "last_name": "Test",
    }

    # Act
    response = client.post("/api/v1/auth/register", json=user_data)

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
