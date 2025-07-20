# ruff: noqa: S101, S105
from fastapi.testclient import TestClient

from app.models.user import User


def test_register_new_user(client: TestClient) -> None:
    """Test registering a new user via the API"""
    # Arrange
    user_data = {"email": "newuser@example.com", "password": "testpassword"}

    # Act
    response = client.post("/api/v1/auth/register", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert data["is_active"] is True
    assert data["is_superuser"] is False


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


def test_get_current_user_no_token(client: TestClient) -> None:
    """Test getting the current user without a token via the API"""
    # Act
    response = client.get("/api/v1/auth/me")

    # Assert
    assert response.status_code == 401
    data = response.json()
    assert "Not authenticated" in data["detail"]
