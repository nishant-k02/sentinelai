"""Operational commands that don't belong behind an HTTP endpoint.

    python -m sentinelai.cli create-admin --org-name "Acme" --email you@example.com
    python -m sentinelai.cli seed-demo [--reset]

create-admin: POST /v1/users is admin-only, so the very first admin of an
organization has to come from somewhere that isn't an authenticated request.
Same idea as Django's `createsuperuser`. It calls the same `register_user`
use case the API does, so it is held to the same rules (password policy,
duplicate-email check); only the *caller authorization* differs, and here
the caller is whoever has shell access to the database.

seed-demo: a believable fleet of services with three hours of telemetry, so
the UI has something to show. One service is mid-incident on purpose.

This module is a composition root like main.py and worker/main.py: it sits
outside the platform < modules < api/worker layers and may import them all.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import random
import sys
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelai import model_registry  # noqa: F401  -- registers every model on Base.metadata
from sentinelai.modules.auth.models import RefreshToken, Role, User
from sentinelai.modules.auth.repository import UserRepository
from sentinelai.modules.auth.use_cases import register_user
from sentinelai.modules.ingestion.models import Deployment, LogEvent, LogLevel, MetricSample
from sentinelai.modules.organization.models import Organization
from sentinelai.modules.organization.repository import OrganizationRepository
from sentinelai.modules.service.models import Environment, Service
from sentinelai.modules.service.repository import ServiceRepository
from sentinelai.platform.config import get_settings
from sentinelai.platform.db import create_db_engine, create_session_factory
from sentinelai.platform.errors import SentinelError
from sentinelai.simulator.synthetic import (
    FLEET,
    generate_deployments,
    generate_logs,
    generate_metrics,
)

# A fixed id, so the frontend can point at the demo organization without any
# configuration, and a re-seed doesn't change what it points at. Temporary:
# once the UI has login (UI-2) the organization comes from the session.
DEMO_ORG_ID = uuid.UUID("00000000-0000-4000-8000-00000000d3a0")
DEMO_ORG_NAME = "SentinelAI Demo"
# Known password, on purpose, so you can log in. seed-demo refuses to run in
# any non-local environment for exactly this reason.
DEMO_PASSWORD = "sentinel-demo-password"
DEMO_USERS = (
    ("demo.admin@example.com", Role.ADMIN),
    ("demo.responder@example.com", Role.RESPONDER),
    ("demo.viewer@example.com", Role.VIEWER),
)
HISTORY_MINUTES = 180


async def create_admin(org_name: str, email: str, password: str) -> str:
    """Get-or-create the organization, then create an ADMIN in it."""
    engine = create_db_engine(get_settings())
    factory = create_session_factory(engine)
    try:
        async with factory() as session:
            org_repo = OrganizationRepository(session)
            org = await org_repo.get_by_name(org_name)
            if org is None:
                org = await org_repo.create(name=org_name)
            user = await register_user(
                org_repo,
                UserRepository(session),
                organization_id=org.id,
                email=email,
                password=password,
                role=Role.ADMIN,
            )
            await session.commit()
            return f"created admin {user.email} in organization {org.name!r}"
    finally:
        await engine.dispose()


async def _delete_demo_data(session: AsyncSession) -> None:
    """Remove the demo organization and everything hanging off it, children
    first: the foreign keys (deliberately) have no ON DELETE CASCADE."""
    service_ids = select(Service.id).where(Service.organization_id == DEMO_ORG_ID)
    for child in (MetricSample, LogEvent, Deployment):
        await session.execute(delete(child).where(child.service_id.in_(service_ids)))
    await session.execute(delete(Service).where(Service.organization_id == DEMO_ORG_ID))
    user_ids = select(User.id).where(User.organization_id == DEMO_ORG_ID)
    await session.execute(delete(RefreshToken).where(RefreshToken.user_id.in_(user_ids)))
    await session.execute(delete(User).where(User.organization_id == DEMO_ORG_ID))
    await session.execute(delete(Organization).where(Organization.id == DEMO_ORG_ID))


async def seed_demo(*, reset: bool) -> str:
    settings = get_settings()
    if not settings.is_local:
        raise SystemExit("seed-demo creates users with a known password; local environment only")

    engine = create_db_engine(settings)
    factory = create_session_factory(engine)
    try:
        async with factory() as session:
            org_repo = OrganizationRepository(session)
            if await org_repo.get(DEMO_ORG_ID) is not None:
                if not reset:
                    return "demo data already exists (run with --reset to regenerate it)"
                await _delete_demo_data(session)

            org = await org_repo.create(id=DEMO_ORG_ID, name=DEMO_ORG_NAME)
            user_repo = UserRepository(session)
            for email, role in DEMO_USERS:
                await register_user(
                    org_repo,
                    user_repo,
                    organization_id=org.id,
                    email=email,
                    password=DEMO_PASSWORD,
                    role=role,
                )

            end = datetime.now(UTC).replace(second=0, microsecond=0)
            service_repo = ServiceRepository(session)
            counts = {"metrics": 0, "logs": 0, "deployments": 0}
            for profile in FLEET:
                service = await service_repo.create(
                    organization_id=org.id,
                    name=profile.name,
                    environment=Environment(profile.environment),
                )
                # A str seed is hashed (sha512), so this is stable across
                # processes, unlike hash(), which is salted per interpreter.
                rng = random.Random(f"sentinelai-demo:{profile.name}")

                metrics = generate_metrics(profile, end=end, minutes=HISTORY_MINUTES, rng=rng)
                session.add_all(
                    MetricSample(
                        service_id=service.id,
                        metric_name=m.metric_name,
                        value=m.value,
                        recorded_at=m.recorded_at,
                    )
                    for m in metrics
                )
                logs = generate_logs(profile, end=end, minutes=HISTORY_MINUTES, rng=rng)
                session.add_all(
                    LogEvent(
                        service_id=service.id,
                        level=LogLevel(log.level),
                        message=log.message,
                        attributes=log.attributes,
                        recorded_at=log.recorded_at,
                    )
                    for log in logs
                )
                deployments = generate_deployments(profile, end=end)
                session.add_all(
                    Deployment(
                        service_id=service.id,
                        version=d.version,
                        commit_sha=d.commit_sha,
                        deployed_by=d.deployed_by,
                        deployed_at=d.deployed_at,
                    )
                    for d in deployments
                )
                counts["metrics"] += len(metrics)
                counts["logs"] += len(logs)
                counts["deployments"] += len(deployments)

            await session.commit()
            logins = "\n".join(f"  {email}  /  {DEMO_PASSWORD}" for email, _ in DEMO_USERS)
            return (
                f"seeded {DEMO_ORG_NAME!r} ({DEMO_ORG_ID}): {len(FLEET)} services, "
                f"{counts['metrics']} metric samples, {counts['logs']} log events, "
                f"{counts['deployments']} deployments\nlogins:\n{logins}"
            )
    finally:
        await engine.dispose()


def _read_password() -> str:
    # SENTINEL_ADMIN_PASSWORD exists for scripted/dev use. Interactive use
    # prompts instead, so the password never lands in shell history or `ps`.
    from_env = os.environ.get("SENTINEL_ADMIN_PASSWORD")
    if from_env:
        return from_env
    first = getpass.getpass("Password: ")
    if first != getpass.getpass("Repeat password: "):
        raise SystemExit("passwords do not match")
    return first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sentinelai.cli")
    commands = parser.add_subparsers(dest="command", required=True)

    admin = commands.add_parser("create-admin", help="create the first admin of an organization")
    admin.add_argument("--org-name", required=True)
    admin.add_argument("--email", required=True)

    seed = commands.add_parser("seed-demo", help="load a demo fleet with three hours of telemetry")
    seed.add_argument(
        "--reset", action="store_true", help="delete and regenerate existing demo data"
    )

    args = parser.parse_args(argv)

    try:
        if args.command == "create-admin":
            print(asyncio.run(create_admin(args.org_name, args.email, _read_password())))
        elif args.command == "seed-demo":
            print(asyncio.run(seed_demo(reset=args.reset)))
    except SentinelError as exc:
        print(f"error: {exc.message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
