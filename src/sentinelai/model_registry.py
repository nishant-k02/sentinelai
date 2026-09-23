"""Import every module's SQLAlchemy models so they register on
Base.metadata.

Modules stay mutually independent in Python (Phase 1.2's "Independent
modules" import-linter contract) — nothing in the ordinary import graph
guarantees every model module gets loaded. A foreign key referenced by
table name (e.g. ``ForeignKey("organizations.id")`` in modules/service)
resolves lazily, against whatever happens to be registered on
Base.metadata at the moment it's needed — and fails with
``NoReferencedTableError`` if that table's model was never imported by
anything in the running process.

This module exists purely for that import side effect. Every real
entrypoint (the API, the worker) and Alembic's migrations/env.py import
it, once, before any of them can safely touch the database. This file
lives at the package root, not inside platform/, specifically because
platform must not import modules/ (Phase 0.3's layering contract) — this
is the one place allowed to import all three.
"""

from __future__ import annotations

from sentinelai.modules.ingestion import models as _ingestion_models  # noqa: F401
from sentinelai.modules.organization import models as _organization_models  # noqa: F401
from sentinelai.modules.service import models as _service_models  # noqa: F401
