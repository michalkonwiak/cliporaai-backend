import logging
import os
import asyncio
from typing import AsyncGenerator, Any

import redis.asyncio as redis
import aioboto3
from alembic.config import Config as AlembicConfig
from alembic import command
from botocore.config import Config as BotoConfig
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler
from app.middleware import RequestIdMiddleware, MaxBodySizeMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

setup_logging()
logger = logging.getLogger(__name__)


async def apply_migrations() -> None:
    """Apply database migrations using Alembic API instead of subprocess with advisory lock."""
    try:
        logger.info("Applying database migrations with advisory lock...")
        from sqlalchemy import text
        from app.db.session import get_async_session
        
        async for session in get_async_session():
            await session.execute(text("SELECT pg_advisory_lock(984321)"))
            try:
                alembic_cfg = AlembicConfig("alembic.ini")
                command.upgrade(alembic_cfg, "head")
            finally:
                await session.execute(text("SELECT pg_advisory_unlock(984321)"))
                
        logger.info("Database migrations applied successfully")
    except Exception as e:
        logger.error(f"Error applying database migrations: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for the FastAPI application.
    Creates and stores Redis and S3 clients in app.state.
    """
    # Use Any to work around mypy state typing issues
    app_state: Any = app.state

    if settings.auto_migrate:
        logger.info("Auto migrations enabled, applying migrations...")
        await apply_migrations()
    else:
        logger.info("Auto migrations disabled, skipping migrations")
        
    # Load JWT keys for asymmetric algorithms (if configured)
    try:
        from app.core.security import load_jwt_keys
        load_jwt_keys()
    except Exception as e:
        logger.error(f"JWT key loading failed: {e}")
        if settings.environment == "production":
            raise
        else:
            logger.warning("Continuing startup without loaded JWT keys (development mode)")
        
    # Create upload directories
    logger.info("Creating upload directories...")
    settings.upload_dir_path.mkdir(parents=True, exist_ok=True)
    settings.temp_upload_dir_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload directories created: {settings.upload_dir_path}, {settings.temp_upload_dir_path}")
    
    logger.info("Initializing Redis client...")
    redis_url = str(settings.redis_dsn)
    app_state.redis_client = redis.from_url(
        redis_url,
        socket_connect_timeout=settings.connection_timeout,
        socket_timeout=settings.connection_timeout,
        retry_on_timeout=True,
        decode_responses=settings.redis_decode_responses,
    )
    
    try:
        logger.info("Performing Redis sanity check...")
        ping_result = await asyncio.wait_for(
            app_state.redis_client.ping(),
            timeout=settings.connection_timeout
        )
        if ping_result:
            logger.info("Redis sanity check passed")
        else:
            logger.error("Redis sanity check failed: ping returned False")
            if settings.environment == "production":
                raise RuntimeError("Redis sanity check failed")
            else:
                logger.warning("Continuing startup without Redis (development mode)")
    except asyncio.TimeoutError:
        logger.error(f"Redis sanity check timed out after {settings.connection_timeout}s")
        if settings.environment == "production":
            raise RuntimeError(f"Redis connection timed out after {settings.connection_timeout}s")
        else:
            logger.warning("Continuing startup without Redis (development mode)")
    except Exception as e:
        logger.error(f"Redis sanity check failed: {e}")
        if settings.environment == "production":
            raise RuntimeError(f"Redis sanity check failed: {e}")
        else:
            logger.warning("Continuing startup without Redis (development mode)")
    
    if settings.storage_type == "s3":
        logger.info("Initializing S3 client...")
        session = aioboto3.Session()

        app_state.s3_cm = session.client(
            's3',
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=str(settings.aws_access_key_id.get_secret_value()) if settings.aws_access_key_id else None,
            aws_secret_access_key=str(settings.aws_secret_access_key.get_secret_value()) if settings.aws_secret_access_key else None,
            region_name=settings.s3_region,
            config=BotoConfig(
                signature_version='s3v4',
                connect_timeout=settings.connection_timeout,
                read_timeout=settings.connection_timeout * 2,
                # Skip retries configuration to avoid type issues
                # retries=retry_config,
                tcp_keepalive=True
            )
        )
        app_state.s3_client = await app_state.s3_cm.__aenter__()

        try:
            logger.info("Performing S3 sanity check...")
            await asyncio.wait_for(
                app_state.s3_client.head_bucket(Bucket=settings.s3_bucket_name),
                timeout=settings.connection_timeout
            )
            logger.info(f"S3 sanity check passed for bucket: {settings.s3_bucket_name}")
        except asyncio.TimeoutError:
            logger.error(f"S3 sanity check timed out after {settings.connection_timeout}s")
            if settings.environment == "production":
                raise RuntimeError(f"S3 connection timed out after {settings.connection_timeout}s")
            else:
                logger.warning("Continuing startup without S3 (development mode)")
        except Exception as e:
            logger.error(f"S3 sanity check failed: {e}")
            if settings.environment == "production":
                raise RuntimeError(f"S3 sanity check failed: {e}")
            else:
                logger.warning("Continuing startup without S3 (development mode)")
    
    logger.info("Application startup complete")
    
    yield
    
    logger.info("Shutting down application...")
    
    if hasattr(app_state, "redis_client"):
        logger.info("Closing Redis connection...")
        await app_state.redis_client.close()

    if hasattr(app_state, "s3_cm"):
        logger.info("Closing S3 client...")
        await app_state.s3_cm.__aexit__(None, None, None)

    logger.info("Application shutdown complete")



app = FastAPI(
    title="CliporaAI Backend",
    description="API for CliporaAI video and audio processing",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Use Any to work around mypy state typing issues
app_state: Any = app.state
app_state.limiter = limiter

from app.core.error_handlers import setup_error_handlers  # noqa: E402
setup_error_handlers(app)

# Configure rate limiting middleware only when enabled and not in development to avoid interfering with docs
if settings.rate_limit_enabled and settings.environment != "development":
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    logger.info("SlowAPI rate limiting enabled")
else:
    logger.info(
        "SlowAPI rate limiting middleware disabled (either rate_limit_enabled is False or environment is development)"
    )

app.add_middleware(RequestIdMiddleware)
app.add_middleware(MaxBodySizeMiddleware, max_size_mb=settings.max_upload_size_mb)

from starlette.middleware.trustedhost import TrustedHostMiddleware  # noqa: E402

# Handle optional ProxyHeadersMiddleware properly
ProxyHeadersMiddleware: Any = None
try:
    from starlette.middleware.proxy_headers import ProxyHeadersMiddleware  # type: ignore
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.trusted_hosts)
except ImportError:
    logger.warning("ProxyHeadersMiddleware not available, skipping")

allowed_hosts = ["*"] if settings.environment == "development" else settings.trusted_hosts
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
    expose_headers=["ETag", "Content-Range", "Content-Disposition"]
)

from fastapi.middleware.gzip import GZipMiddleware  # noqa: E402
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(api_v1_router, prefix="/api/v1")




if __name__ == "__main__":
    import uvicorn
    import multiprocessing

    is_dev = os.environ.get("ENVIRONMENT", "development") == "development"
    
    from app.core.logging import get_logging_config
    
    uvicorn_config: dict[str, Any] = {
        "host": settings.host,
        "port": settings.port,
        "log_level": settings.log_level.lower(),
        # Enable faster implementations if available
        "loop": "uvloop",
        "http": "httptools",
        # Timeouts
        "timeout_keep_alive": 65,
        "log_config": get_logging_config(),
    }
    
    try:
        import uvloop, httptools  # type: ignore # noqa
    except ImportError:
        logger.warning("uvloop and/or httptools not available, using standard event loop and http parser")
        uvicorn_config.pop("loop", None)
        uvicorn_config.pop("http", None)
    
    if is_dev:
        uvicorn_config["reload"] = True
        uvicorn.run("app.main:app", **dict(uvicorn_config))
    else:
        workers = multiprocessing.cpu_count() * 2
        uvicorn_config["workers"] = workers
        
        logger.info(f"Starting Uvicorn with {workers} workers in production mode")
        
        uvicorn.run("app.main:app", **dict(uvicorn_config))
