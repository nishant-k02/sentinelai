"""Deterministic synthetic telemetry for a fleet of pretend services.

Pure data generation: no database, no HTTP, no imports from modules/. The
`seed-demo` command turns these plain dataclasses into rows. Kept separate
because this is the seed of the failure-injection simulator planned for M14:
the same generator, later driven live instead of in one batch.

The story baked into the data: `checkout-api` is deployed, and a few
minutes later its error rate, latency and CPU climb together. Nothing in
the system understands that yet. Anomaly detection (M2), incidents (M3) and
the investigation agent (M7) are what will, and this data is what they get
tested against.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta

METRIC_NAMES = (
    "cpu_percent",
    "memory_percent",
    "latency_p95_ms",
    "error_rate_percent",
    "requests_per_second",
)


@dataclass(frozen=True)
class ServiceProfile:
    name: str
    environment: str  # "production" | "staging": plain strings keep this module model-free
    cpu: float
    memory: float
    latency_p95: float
    error_rate: float
    rps: float
    incident: bool = False


@dataclass(frozen=True)
class MetricPoint:
    metric_name: str
    value: float
    recorded_at: datetime


@dataclass(frozen=True)
class LogPoint:
    level: str
    message: str
    attributes: dict[str, object]
    recorded_at: datetime


@dataclass(frozen=True)
class DeploymentPoint:
    version: str
    commit_sha: str
    deployed_by: str
    deployed_at: datetime


FLEET = (
    ServiceProfile("checkout-api", "production", 38, 55, 180, 0.4, 120, incident=True),
    ServiceProfile("payments-api", "production", 30, 48, 240, 0.2, 60),
    ServiceProfile("inventory-service", "production", 25, 62, 95, 0.1, 90),
    ServiceProfile("notification-worker", "production", 18, 40, 400, 0.3, 15),
    ServiceProfile("search-api", "staging", 22, 45, 130, 0.5, 12),
)

# How long before "now" the incident story begins.
DEPLOY_MINUTES_AGO = 28
DEGRADATION_MINUTES_AGO = 24


def _ramp(minutes_since_start: float, ramp_minutes: float = 10.0) -> float:
    """0 -> 1 over `ramp_minutes`, then flat: how fast the damage develops."""
    return max(0.0, min(1.0, minutes_since_start / ramp_minutes))


def generate_metrics(
    profile: ServiceProfile, *, end: datetime, minutes: int, rng: random.Random
) -> list[MetricPoint]:
    """One point per metric per minute for the `minutes` ending at `end`."""
    points: list[MetricPoint] = []
    for i in range(minutes):
        at = end - timedelta(minutes=minutes - 1 - i)
        minutes_ago = minutes - 1 - i
        # Slow wave (period ~ 90 min) standing in for daily traffic shape.
        wave = math.sin(i / 90 * 2 * math.pi)
        damage = _ramp(DEGRADATION_MINUTES_AGO - minutes_ago) if profile.incident else 0.0

        cpu = profile.cpu * (1 + 0.12 * wave) + rng.gauss(0, 1.5) + damage * 45
        memory = profile.memory + 2 * wave + rng.gauss(0, 0.6) + damage * 8
        latency = profile.latency_p95 * (1 + 0.1 * wave) + rng.gauss(0, 8) + damage * 1200
        errors = max(0.0, profile.error_rate * (1 + 0.2 * wave) + rng.gauss(0, 0.05) + damage * 9)
        rps = max(0.0, profile.rps * (1 + 0.25 * wave) + rng.gauss(0, 2) - damage * 25)

        for name, value in zip(METRIC_NAMES, (cpu, memory, latency, errors, rps), strict=True):
            clamped = min(value, 100.0) if name.endswith("_percent") else value
            points.append(MetricPoint(name, round(max(clamped, 0.0), 2), at))
    return points


def generate_logs(
    profile: ServiceProfile, *, end: datetime, minutes: int, rng: random.Random
) -> list[LogPoint]:
    logs: list[LogPoint] = []
    for minutes_ago in range(minutes - 1, -1, -1):
        at = end - timedelta(minutes=minutes_ago)
        if minutes_ago % 9 == 0:
            logs.append(
                LogPoint("info", "health check passed", {"latency_ms": rng.randint(2, 9)}, at)
            )
        if profile.incident and minutes_ago <= DEGRADATION_MINUTES_AGO and minutes_ago % 2 == 0:
            logs.append(
                rng.choice(
                    [
                        LogPoint(
                            "error",
                            "upstream timeout calling payments-api",
                            {"attempt": 3, "timeout_ms": 1000},
                            at,
                        ),
                        LogPoint(
                            "error",
                            "database connection pool exhausted",
                            {"pool_size": 20, "waiting": rng.randint(12, 40)},
                            at,
                        ),
                        LogPoint("warning", "retrying request", {"attempt": 2}, at),
                    ]
                )
            )
    return logs


def generate_deployments(profile: ServiceProfile, *, end: datetime) -> list[DeploymentPoint]:
    history = [
        DeploymentPoint("2.12.3", "9c1f4e7a2b8d", "ci-bot", end - timedelta(days=2, hours=3)),
        DeploymentPoint("2.13.0", "4d7a90c1e5f2", "priya", end - timedelta(hours=9)),
    ]
    if profile.incident:
        history.append(
            DeploymentPoint(
                "2.14.0", "e83b21f0a9c4", "ci-bot", end - timedelta(minutes=DEPLOY_MINUTES_AGO)
            )
        )
    return history
