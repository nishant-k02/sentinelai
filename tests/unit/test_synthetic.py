from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from sentinelai.simulator.synthetic import (
    DEPLOY_MINUTES_AGO,
    FLEET,
    METRIC_NAMES,
    ServiceProfile,
    generate_deployments,
    generate_metrics,
)

END = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
MINUTES = 180
INCIDENT = next(p for p in FLEET if p.incident)
HEALTHY = next(p for p in FLEET if not p.incident)


def _series(profile: ServiceProfile, metric: str, seed: str = "test") -> list[float]:
    points = generate_metrics(profile, end=END, minutes=MINUTES, rng=random.Random(seed))
    return [p.value for p in points if p.metric_name == metric]


def test_same_seed_produces_identical_data() -> None:
    a = generate_metrics(INCIDENT, end=END, minutes=MINUTES, rng=random.Random("same"))
    b = generate_metrics(INCIDENT, end=END, minutes=MINUTES, rng=random.Random("same"))
    assert a == b


def test_one_point_per_metric_per_minute() -> None:
    points = generate_metrics(HEALTHY, end=END, minutes=MINUTES, rng=random.Random("x"))
    assert len(points) == MINUTES * len(METRIC_NAMES)
    assert {p.metric_name for p in points} == set(METRIC_NAMES)
    assert max(p.recorded_at for p in points) == END
    assert min(p.recorded_at for p in points) == END - timedelta(minutes=MINUTES - 1)


def test_percentages_stay_within_0_to_100() -> None:
    for profile in FLEET:
        for metric in ("cpu_percent", "memory_percent", "error_rate_percent"):
            values = _series(profile, metric)
            assert all(0.0 <= v <= 100.0 for v in values), (profile.name, metric)


def test_the_incident_service_degrades_after_the_deploy() -> None:
    errors = _series(INCIDENT, "error_rate_percent")
    latency = _series(INCIDENT, "latency_p95_ms")

    assert max(errors[:60]) < 1.5  # an hour of normal behavior first
    assert errors[-1] > 5.0  # then it is clearly on fire
    assert latency[-1] > 3 * latency[0]


def test_healthy_services_stay_healthy() -> None:
    for profile in (p for p in FLEET if not p.incident):
        assert max(_series(profile, "error_rate_percent")) < 1.5, profile.name


def test_only_the_incident_service_has_a_recent_deployment() -> None:
    recent_cutoff = END - timedelta(minutes=DEPLOY_MINUTES_AGO + 1)
    for profile in FLEET:
        recent = [
            d for d in generate_deployments(profile, end=END) if d.deployed_at >= recent_cutoff
        ]
        assert bool(recent) == profile.incident, profile.name
