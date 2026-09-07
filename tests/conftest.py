from collections.abc import Iterator

import pytest

from sentinelai.platform.config import get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    """Clear the cached Settings around every test so env overrides take effect."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
