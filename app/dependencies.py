import logging
from typing import Dict, Any, AsyncGenerator, cast
from datetime import datetime, timezone

import redis.asyncio as redis
import aioboto3

from fastapi import Depends, HTTPException, status, Security, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import credentials_exception, TokenExpiredError
from app.core.security import decode_access_token

from app.db.session import get_async_session
from app.models.user import User

logger = logging.getLogger(__name__)

# Security scheme for JWT authentication
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get an async database session.
    Yields an AsyncSession and ensures it's closed after use.
    """
    async for session in get_async_session():
        yield session


async def get_redis_client(request: Request) -> redis.Redis:
    """
    Dependency function to get a Redis client.
    Uses the singleton client from app.state.
    Raises 503 error if Redis client is not available.
    
    Returns:
        A redis.asyncio.Redis client instance
    """
    if not hasattr(request.app.state, "redis_client"):
        raise HTTPException(status_code=503, detail="Redis client not ready")
    return cast(redis.Redis, request.app.state.redis_client)


async def get_s3_client(request: Request) -> "aioboto3.client.S3":
    """
    Dependency function to get an S3 client.
    Uses the singleton client from app.state.
    Raises 503 error if S3 client is not available.
    
    Returns:
        An aioboto3 S3 client instance
    """
    if not hasattr(request.app.state, "s3_client"):
        raise HTTPException(status_code=503, detail="S3 client not ready")
    return request.app.state.s3_client


# Authentication dependencies


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> str:
    """Extract JWT token from Authorization header"""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return str(credentials.credentials)


async def verify_token(token: str = Depends(get_current_user_token)) -> Dict[str, Any]:
    """Verify JWT token and extract payload"""
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Token validation is now handled in decode_access_token
        # including expiration check with leeway

        return payload
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    db: AsyncSession = Depends(get_db), token_payload: Dict[str, Any] = Depends(verify_token)
) -> User:
    """Get current authenticated user from token"""
    user_id = token_payload.get("sub")
    if not user_id:
        raise credentials_exception

    # Use SQLAlchemy ORM 2.0 style
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user: User | None = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    # Update last_login_at with timezone-aware datetime
    now = datetime.now(timezone.utc)
    last_login = user.last_login_at
    # Normalize to timezone-aware (UTC) if stored as naive in SQLite
    if last_login is not None and last_login.tzinfo is None:
        last_login = last_login.replace(tzinfo=timezone.utc)
    if not last_login or (now - last_login).total_seconds() > 900:  # 15 minutes
        user.last_login_at = now
        await db.commit()
        await db.refresh(user)

    return user
