import asyncio
import json
import uuid

import pytest

from sentinelai.platform.config import get_settings
from sentinelai.platform.messaging import create_consumer, create_producer

pytestmark = pytest.mark.integration

TOPIC = "sentinelai.smoke-test"


async def test_produced_message_is_consumed_end_to_end() -> None:
    settings = get_settings()
    producer = create_producer(settings)
    consumer = create_consumer(settings, TOPIC, group_id=f"test-{uuid.uuid4()}")

    await producer.start()
    await consumer.start()
    try:
        # This topic is long-lived (manual `rpk topic produce` testing, prior
        # runs) and retains history, so a fresh "earliest" consumer reads
        # every old message first, not just the one we're about to send.
        # Tag this run with a unique marker and scan for it instead of
        # assuming our message is the first one returned.
        marker = str(uuid.uuid4())
        payload = {"hello": "sentinelai", "marker": marker}
        await producer.send_and_wait(TOPIC, key=b"smoke-test", value=json.dumps(payload).encode())

        async def find_our_message() -> None:
            async for record in consumer:
                if record.value is None:
                    continue
                data = json.loads(record.value)
                if data.get("marker") != marker:
                    continue  # someone else's message (manual test, old run) — keep scanning
                assert record.topic == TOPIC
                assert record.key == b"smoke-test"
                assert data == payload
                return

        await asyncio.wait_for(find_our_message(), timeout=10)
    finally:
        await producer.stop()
        await consumer.stop()
