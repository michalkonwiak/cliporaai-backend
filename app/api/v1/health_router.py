import logging
from typing import NotRequired, TypedDict

import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_redis_client


class ServiceStatus(TypedDict):
    status: str
    error: NotRequired[str]


class Services(TypedDict):
    app: ServiceStatus
    database: ServiceStatus
    redis: ServiceStatus


class HealthStatus(TypedDict):
    status: str
    services: Services

router = APIRouter(prefix="/health", tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("")
def health_check(
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
) -> HealthStatus:
    """
    Comprehensive health check endpoint that verifies the status of:
    - Database connection
    - Redis connection
    - Application itself
    """
    app_status: ServiceStatus = {"status": "ok"}
    database_status: ServiceStatus = {"status": "ok"}
    redis_status: ServiceStatus = {"status": "ok"}
    
    services: Services = {
        "app": app_status,
        "database": database_status,
        "redis": redis_status,
    }
    
    health_status: HealthStatus = {
        "status": "ok",
        "services": services,
    }

    # Check database connection
    try:
        # Execute a simple query to check database connectivity
        db.execute(text("SELECT 1"))
        logger.debug("Database health check passed")
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_status["status"] = "error"
        database_status["error"] = str(e)
        health_status["status"] = "error"

    # Check Redis connection
    try:
        # Ping Redis to check connectivity
        if not redis_client.ping():
            raise Exception("Redis ping failed")
        logger.debug("Redis health check passed")
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status["status"] = "error"
        redis_status["error"] = str(e)
        health_status["status"] = "error"

    # If any service is down, return a 503 Service Unavailable status
    if health_status["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status,
        )

    return health_status