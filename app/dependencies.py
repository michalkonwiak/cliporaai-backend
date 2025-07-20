import logging
from collections.abc import Generator

import redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


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