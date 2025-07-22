from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import hash_password
from app.db.base import Base
from app.dependencies import get_db
from app.main import app
from app.models.user import User
from app.services.auth_service import AuthService

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db() -> Generator[Session]:
    """
    Create a fresh database for each test
    """
    # Create the database tables
    Base.metadata.create_all(bind=engine)

    # Create a new session for the test
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop the database tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db: Session) -> Generator[TestClient]:
    """
    Create a test client with a database session
    """

    def override_get_db() -> Generator[Session]:
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides = {}


@pytest.fixture
def test_user(db: Session) -> User:
    """
    Create a test user
    """
    user_data = {
        "email": "test@example.com",
        "hashed_password": hash_password("password123"),
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_superuser": False,
    }
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_superuser(db: Session) -> User:
    """
    Create a test superuser
    """
    user_data = {
        "email": "admin@example.com",
        "hashed_password": hash_password("admin123"),
        "first_name": "Admin",
        "last_name": "Super",
        "is_active": True,
        "is_superuser": True,
    }
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def token_headers(db: Session, test_user: User) -> dict[str, str]:
    """
    Get token headers for the test user
    """
    auth_service = AuthService(db)
    token = auth_service.create_token(test_user)
    return {"Authorization": f"Bearer {token.access_token}"}


@pytest.fixture
def superuser_token_headers(db: Session, test_superuser: User) -> dict[str, str]:
    """
    Get token headers for the test superuser
    """
    auth_service = AuthService(db)
    token = auth_service.create_token(test_superuser)
    return {"Authorization": f"Bearer {token.access_token}"}
