import asyncio
import json
import uuid

import pytest
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer, ConsumerRecord

from sentinelai.platform.config import get_settings

pytestmark = pytest.mark.integration

TOPIC = "sentinelai.smoke-test"


async def _find_message(consumer: AIOKafkaConsumer, marker: str) -> ConsumerRecord:
    """The topic accumulates messages across every test run and manual demo
    (e.g. Phase 0.7's `rpk topic produce`). A real consumer can never assume
    the next message on the wire is *its* message — it must correlate. Tag
    our message with a unique marker and skip anything that isn't ours."""
    async for record in consumer:
        try:
            if json.loads(record.value).get("marker") == marker:
                return record
        except (json.JSONDecodeError, AttributeError, TypeError):
            continue
    raise AssertionError("consumer stream ended without finding our message")


async def test_produced_message_is_consumed_end_to_end() -> None:
    settings = get_settings()
    producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=f"test-{uuid.uuid4()}",  # fresh group -> reads from the start
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    await producer.start()
    await consumer.start()
    try:
        marker = str(uuid.uuid4())
        payload = {"hello": "sentinelai", "marker": marker}
        await producer.send_and_wait(TOPIC, key=b"smoke-test", value=json.dumps(payload).encode())

        record = await asyncio.wait_for(_find_message(consumer, marker), timeout=10)

        assert record.topic == TOPIC
        assert record.key == b"smoke-test"
        assert json.loads(record.value) == payload
    finally:
        await producer.stop()
        await consumer.stop()
