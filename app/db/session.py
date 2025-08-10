import datetime
from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

# Determine the database URL with sensible development fallback
_database_url = settings.database_url or str(settings.postgres_dsn)
# Normalize to asyncpg driver if plain postgresql scheme is used
if _database_url.startswith("postgresql://"):
    _database_url = _database_url.replace("postgresql://", "postgresql+asyncpg://", 1)


# Configure connect args depending on backend
connect_args: dict = {}
if _database_url.startswith("postgresql+asyncpg://"):
    connect_args = {
        "timeout": settings.connection_timeout,
        "command_timeout": settings.connection_timeout,
    }
elif _database_url.startswith("sqlite+aiosqlite://"):
    # aiosqlite accepts only "timeout"
    connect_args = {"timeout": settings.connection_timeout}

# Create async engine with retry configuration
engine = create_async_engine(
    _database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args,
)

# If using SQLite, register NOW()/now() SQL functions and enable foreign keys on connect
if _database_url.startswith("sqlite+aiosqlite://"):
    def _sqlite_on_connect(dbapi_connection: object, connection_record: object) -> None:
        # Register SQL functions NOW() and now() to return current UTC timestamp
        try:
            dbapi_connection.create_function(  # type: ignore[attr-defined]
                "NOW", 0, lambda: datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            )
            dbapi_connection.create_function(  # type: ignore[attr-defined]
                "now", 0, lambda: datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            )
        except Exception:
            # Best-effort; if not supported, ignore
            pass
        try:
            # Ensure foreign keys enforcement is enabled
            cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception:
            pass

    event.listen(engine.sync_engine, "connect", _sqlite_on_connect)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@retry(
    stop=stop_after_attempt(settings.max_retries),
    wait=wait_exponential(multiplier=settings.retry_backoff),
)
async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """Yield a new database session with retry logic."""
    async with AsyncSessionLocal() as session:
        yield session
