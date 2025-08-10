"""Type definitions for the application."""
from typing import Any, Protocol

import redis.asyncio as redis

try:
    from types_aiobotocore_s3 import S3Client
except ImportError:
    from typing import Any as S3Client  # type: ignore


class AppState(Protocol):
    """Protocol for FastAPI app.state to provide type hints."""
    redis_client: redis.Redis
    s3_client: S3Client
    s3_cm: Any  # Context manager for S3 client
    limiter: Any
