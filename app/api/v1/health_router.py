import logging
from typing import NotRequired, TypedDict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_redis_client, get_s3_client


class ServiceStatus(TypedDict):
    status: str
    error: NotRequired[str]


class Services(TypedDict):
    app: ServiceStatus
    database: ServiceStatus
    redis: ServiceStatus
    localstack: ServiceStatus


class HealthStatus(TypedDict):
    status: str
    services: Services


router = APIRouter(prefix="/health", tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("", response_model=HealthStatus)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis_client: Any = Depends(get_redis_client),
    s3_client: Any = Depends(get_s3_client),
) -> HealthStatus:
    """
    Comprehensive health check endpoint that verifies the status of:
    - Database connection
    - Redis connection
    - LocalStack (S3) connection
    - Application itself
    """
    app_status: ServiceStatus = {"status": "ok"}
    database_status: ServiceStatus = {"status": "ok"}
    redis_status: ServiceStatus = {"status": "ok"}
    localstack_status: ServiceStatus = {"status": "ok"}

    services: Services = {
        "app": app_status,
        "database": database_status,
        "redis": redis_status,
        "localstack": localstack_status,
    }

    health_status: HealthStatus = {
        "status": "ok",
        "services": services,
    }

    # Check database connection
    try:
        # Execute a simple query to check database connectivity
        await db.execute(text("SELECT 1"))
        logger.debug("Database health check passed")
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_status["status"] = "error"
        database_status["error"] = str(e)
        health_status["status"] = "error"

    # Check Redis connection
    try:
        if not await redis_client.ping():
            raise Exception("Redis ping failed")
        logger.debug("Redis health check passed")
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status["status"] = "error"
        redis_status["error"] = str(e)
        health_status["status"] = "error"
        
    # Check LocalStack (S3) connection
    try:
        from app.core.config import settings
        await s3_client.head_bucket(Bucket=settings.s3_bucket_name)
        logger.debug(f"LocalStack health check passed for bucket: {settings.s3_bucket_name}")
    except Exception as e:
        logger.error(f"LocalStack health check failed: {e}")
        localstack_status["status"] = "error"
        localstack_status["error"] = str(e)
        health_status["status"] = "error"

    if health_status["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status,
        )

    return health_status



@router.get("/live")
async def live() -> dict[str, str]:
    """Liveness probe: lightweight and always OK if the app is running."""
    return {"status": "ok"}


@router.get("/ready", response_model=HealthStatus)
async def ready(
    db: AsyncSession = Depends(get_db),
    redis_client: Any = Depends(get_redis_client),
    s3_client: Any = Depends(get_s3_client),
) -> HealthStatus:
    """Readiness probe: reuse full health check to ensure dependencies are ready."""
    return await health_check(db=db, redis_client=redis_client, s3_client=s3_client)
