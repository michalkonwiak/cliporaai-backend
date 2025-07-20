import logging
import os
import subprocess

from fastapi import FastAPI

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def apply_migrations() -> None:
    try:
        logger.info("Applying database migrations...")
        alembic_ini_path = os.path.join(os.getcwd(), "alembic.ini")
        alembic_path = os.path.join(os.getcwd(), ".venv", "bin", "alembic")
        subprocess.run([alembic_path, "-c", alembic_ini_path, "upgrade", "head"], check=True)  # noqa: S603
        logger.info("Database migrations applied successfully")
    except Exception as e:
        logger.error(f"Error applying database migrations: {e}")
        raise


apply_migrations()

app = FastAPI(title="CliporaAI Backend")

app.include_router(api_v1_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
