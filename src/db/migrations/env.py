import asyncio
from logging.config import fileConfig

import os  # Re-import os to get environment variable
import sys
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# --- Project Path Setup ---
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

# --- Model Imports for Alembic --- # noqa: E402 module level import not at top
# Explicitly import all models to ensure they are registered with Base.metadata
from src.db.base import Base                          # noqa: E402
from src.db.models.user import User                 # noqa: E402, F401
from src.db.models.conversation import Conversation # noqa: E402, F401
from src.db.models.message import Message           # noqa: E402, F401
from src.db.models.job import Job                   # noqa: E402, F401


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# --- Database URL Configuration --- #
# Get the database URL from the environment variable first.
# This ensures the command line `export DATABASE_URL=...` takes precedence.
db_url_from_env = os.getenv('DATABASE_URL')

if db_url_from_env:
    # If DATABASE_URL is set, use it directly for the 'sqlalchemy.url' setting
    # This ensures async_engine_from_config finds the 'url' key
    config.set_main_option('sqlalchemy.url', db_url_from_env)
    print(f"--- Alembic using DATABASE_URL from environment: {db_url_from_env} ---")
else:
    # Fallback to alembic.ini if env var is not set (though we commented it out)
    # If sqlalchemy.url is also commented out in ini, this will raise an error later,
    # which is correct behavior if no URL is provided.
    print("--- Alembic DATABASE_URL environment variable not set, relying on alembic.ini ---")
    pass # Let async_engine_from_config handle missing url from ini if necessary

# Hardcoded URL section removed/commented out in previous steps.

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# IMPORTANT: This must come AFTER all model imports
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Get the possibly updated sqlalchemy.url from the config object
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise ValueError("Database URL not configured. Set DATABASE_URL environment variable or sqlalchemy.url in alembic.ini")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Define how migrations are run within a transaction."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # async_engine_from_config reads from the config section directly,
    # which now includes 'sqlalchemy.url' if DATABASE_URL was set.
    try:
        connectable = async_engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    except KeyError as e:
        if 'url' in str(e):
             raise ValueError(
                "Database URL key 'url' not found in Alembic config. "
                "Ensure DATABASE_URL environment variable is set or "
                "sqlalchemy.url is configured in alembic.ini."
            ) from e
        raise # Re-raise other KeyErrors

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
