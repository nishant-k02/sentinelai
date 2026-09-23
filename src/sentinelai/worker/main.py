from __future__ import annotations

import asyncio
import contextlib
import signal

from aiokafka import AIOKafkaConsumer
from opentelemetry import trace as otel_trace
from structlog.stdlib import BoundLogger

from sentinelai import model_registry  # noqa: F401  -- registers every model on Base.metadata
from sentinelai.platform.config import get_settings
from sentinelai.platform.logging import configure_logging, get_logger
from sentinelai.platform.messaging import create_consumer, extract_trace_context
from sentinelai.platform.tracing import configure_tracing

SMOKE_TEST_TOPIC = "sentinelai.smoke-test"
CONSUMER_GROUP = "sentinelai-worker"


async def _consume_loop(
    consumer: AIOKafkaConsumer, log: BoundLogger, tracer: otel_trace.Tracer
) -> None:
    async for record in consumer:
        ctx = extract_trace_context(record.headers)
        with tracer.start_as_current_span(
            "kafka.consume",
            context=ctx,
            kind=otel_trace.SpanKind.CONSUMER,
            attributes={"messaging.system": "kafka", "messaging.destination.name": record.topic},
        ):
            log.info(
                "message_received",
                topic=record.topic,
                partition=record.partition,
                offset=record.offset,
                key=record.key,
                value=record.value.decode() if record.value else None,
            )
            await consumer.commit()


async def run() -> None:
    settings = get_settings()
    configure_logging(settings)
    configure_tracing(settings)
    log = get_logger(__name__)
    tracer = otel_trace.get_tracer(__name__)

    consumer = create_consumer(settings, SMOKE_TEST_TOPIC, group_id=CONSUMER_GROUP)
    await consumer.start()
    log.info("worker_ready", topic=SMOKE_TEST_TOPIC, group=CONSUMER_GROUP)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    consume_task = asyncio.create_task(_consume_loop(consumer, log, tracer))
    try:
        await stop.wait()
        log.info("worker_shutting_down")
    finally:
        consume_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await consume_task
        await consumer.stop()
        log.info("worker_stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
