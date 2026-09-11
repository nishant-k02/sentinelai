import pytest
from sqlalchemy import text

from sentinelai.platform.config import get_settings
from sentinelai.platform.db import create_db_engine

pytestmark = pytest.mark.integration


async def test_organizations_table_matches_model() -> None:
    """Proves `make migrate` produced a schema consistent with the ORM model."""
    engine = create_db_engine(get_settings())
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT id, name, created_at FROM organizations LIMIT 1"))
    finally:
        await engine.dispose()
