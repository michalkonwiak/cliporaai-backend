import logging
from typing import Any

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_limiter(redis_url: str | None = None) -> Limiter:
    """
    Create a rate limiter instance with Redis as the backend.
    
    Args:
        redis_url: Optional Redis URL. If not provided, uses the URL from settings.
        
    Returns:
        A configured Limiter instance
    """
    if not redis_url:
        redis_url = str(settings.redis_dsn)

    limiter = Limiter(
        key_func=get_remote_address,  # Use IP address as the rate limit key
        storage_uri=redis_url,  # Redis URL already includes the redis:// prefix
        storage_options={"socket_connect_timeout": str(settings.connection_timeout)},
        strategy="fixed-window",  # Use fixed window strategy
        default_limits=[settings.rate_limit_default_limit],  # Default rate limit
        enabled=settings.rate_limit_enabled,  # Enable/disable based on settings
    )

    logger.info(
        f"Rate limiter initialized with Redis backend. "
        f"Default limit: {settings.rate_limit_default_limit}, "
        f"Enabled: {settings.rate_limit_enabled}"
    )

    return limiter


limiter = get_limiter()


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    """
    Custom exception handler for rate limit exceeded errors.
    Defensive against exceptions without `.detail` (e.g., TypeError) that may be
    passed by SlowAPI internals on some Python/FastAPI versions.
    
    Args:
        request: The request that triggered the rate limit
        exc: The exception raised (ideally RateLimitExceeded, but may be other)
        
    Returns:
        A JSON response with rate limit information
    """
    client_host = request.client.host if request.client else "unknown"
    logger.warning(
        f"Rate limit exceeded for {client_host} on {request.method} {request.url.path}"
    )

    detail = getattr(exc, "detail", None)
    if not detail:
        detail = str(exc) if str(exc) else "Too Many Requests"

    retry_after = getattr(exc, "retry_after", 1)

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded: {detail}",
            "retry_after": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


def auth_rate_limit() -> Any:
    """Decorator for auth endpoints with stricter rate limits."""
    return limiter.limit(settings.rate_limit_auth_limit)


def transform_rate_limit() -> Any:
    """Decorator for transform endpoints with stricter rate limits."""
    return limiter.limit(settings.rate_limit_transform_limit)
