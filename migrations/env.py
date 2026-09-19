"""Alembic migration environment (async).

- Pulls the database URL from application Settings (single source of truth).
- Builds ``target_metadata`` by importing every module's models so their
  tables register on ``Base.metadata``; autogenerate diffs that against the DB.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from sentinelai.modules.ingestion import models as _ingestion_models  # noqa: F401

# ``_organization_models`` is imported only for its import side effect:
# it registers the ``organizations`` table on Base.metadata.
from sentinelai.modules.organization import models as _organization_models  # noqa: F401
from sentinelai.modules.service import models as _service_models  # noqa: F401
from sentinelai.platform.config import get_settings
from sentinelai.platform.db import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def _run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # detect column type changes, not just add/drop
    )
    with context.begin_transaction():
        context.run_migrations()


async def _run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # a migration is one short-lived connection
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_run_migrations)
    await connectable.dispose()


def run_migrations_offline() -> None:
    """`alembic upgrade --sql` mode: emit SQL without a live DB."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(_run_async_migrations())
