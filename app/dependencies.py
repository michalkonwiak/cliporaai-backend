import logging
from collections.abc import Generator
from typing import Dict, Any
from datetime import datetime

import redis

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import credentials_exception, TokenExpiredError
from app.core.security import decode_access_token

from app.db.session import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

# Security scheme for JWT authentication
security = HTTPBearer()


def get_db() -> Generator[Session]:
    """
    Dependency function to get a database session.
    Yields a SQLAlchemy session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis_client() -> Generator[redis.Redis]:
    """
    Dependency function to get a Redis client.
    Yields a Redis client with connection parameters from settings.
    """
    try:
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            socket_connect_timeout=5,
        )
        yield redis_client
    finally:
        # Redis connections are automatically closed when the client object is garbage collected
        pass


# Authentication dependencies

async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """Extract JWT token from Authorization header"""
    if not credentials:
        raise credentials_exception
    return credentials.credentials

async def verify_token(token: str = Depends(get_current_user_token)) -> Dict[str, Any]:
    """Verify JWT token and extract payload"""
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            raise TokenExpiredError("Token has expired")

        return payload
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )



async def get_current_user(
    db: Session = Depends(get_db),
    token_payload: Dict[str, Any] = Depends(verify_token)
) -> User:
    """Get current authenticated user from token"""
    user_id = token_payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # Update last login
    user.last_login_at = datetime.utcnow()  # type: ignore[assignment]
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
