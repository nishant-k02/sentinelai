from __future__ import annotations

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from sentinelai.platform.config import Settings


def create_producer(settings: Settings) -> AIOKafkaProducer:
    """Build a producer. Call `.start()` before use, `.stop()` on shutdown —
    constructing it opens no connection yet."""
    return AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)


def create_consumer(settings: Settings, *topics: str, group_id: str) -> AIOKafkaConsumer:
    """Build a consumer subscribed to `topics` as part of consumer group
    `group_id`. Members of the same group divide the topic's partitions
    between them; a different group_id gets an independent full copy of
    every message.

    `enable_auto_commit=False`: we commit offsets ourselves, only after a
    message is fully processed. Auto-commit advances the offset on a timer
    regardless of whether processing succeeded — a crash mid-processing then
    loses the message silently (at-most-once). Manual commit-after-success
    gives us at-least-once instead: a crash means the message is redelivered.
    That's *why* Phase 0.6 built `mark_if_new` — at-least-once is only safe
    once duplicates are handled, which idempotency does.
    """
    return AIOKafkaConsumer(
        *topics,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )
