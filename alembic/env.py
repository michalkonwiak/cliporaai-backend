import os
import sys
from pathlib import Path
from logging.config import fileConfig
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import engine_from_config, pool

from alembic import context

# Load environment variables from .env file
load_dotenv()

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

from app.db.base import Base  # noqa: E402

# Import all models to ensure they are registered with Base.metadata
from app.models import (  # noqa: F401, E402
    User,
    Project,
    Video,
    CuttingPlan,
    ExportJob,
    Audio,
)

config = context.config

# Set the SQLAlchemy URL from environment variables
config.set_main_option(
    "sqlalchemy.url",
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}",
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = config.get_main_option("sqlalchemy.url")
    connectable = engine_from_config(
        {"url": url},
        prefix="",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
