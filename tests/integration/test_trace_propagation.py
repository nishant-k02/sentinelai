import asyncio
import uuid

import pytest
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer, ConsumerRecord
from opentelemetry import trace

from sentinelai.platform.config import get_settings
from sentinelai.platform.messaging import extract_trace_context, inject_trace_headers
from sentinelai.platform.tracing import configure_tracing

pytestmark = pytest.mark.integration

TOPIC = "sentinelai.smoke-test"


async def _find_message(consumer: AIOKafkaConsumer, marker: bytes) -> ConsumerRecord:
    """Same reasoning as test_worker_kafka.py: this topic has a backlog from
    every prior test run and manual demo. Correlate by a marker header
    instead of assuming the next message is ours."""
    async for record in consumer:
        if dict(record.headers).get("test-marker") == marker:
            return record
    raise AssertionError("consumer stream ended without finding our message")


async def test_trace_context_survives_the_kafka_hop() -> None:
    """A span started before producing, and a span started after consuming,
    must share the same trace_id — proof the traceparent header round-tripped
    through Kafka intact."""
    settings = get_settings()
    configure_tracing(settings)
    tracer = trace.get_tracer(__name__)

    producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=f"test-{uuid.uuid4()}",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )
    await producer.start()
    await consumer.start()
    try:
        marker = str(uuid.uuid4()).encode()
        with tracer.start_as_current_span("test.produce") as producer_span:
            expected_trace_id = producer_span.get_span_context().trace_id
            headers = [*inject_trace_headers(), ("test-marker", marker)]
            await producer.send_and_wait(TOPIC, value=b"{}", headers=headers)

        record = await asyncio.wait_for(_find_message(consumer, marker), timeout=10)
        ctx = extract_trace_context(record.headers)
        with tracer.start_as_current_span("test.consume", context=ctx) as consumer_span:
            assert consumer_span.get_span_context().trace_id == expected_trace_id
    finally:
        await producer.stop()
        await consumer.stop()
