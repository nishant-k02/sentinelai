from __future__ import annotations

import asyncio
import contextlib
import signal

from aiokafka import AIOKafkaConsumer
from structlog.stdlib import BoundLogger

from sentinelai.platform.config import get_settings
from sentinelai.platform.logging import configure_logging, get_logger
from sentinelai.platform.messaging import create_consumer

SMOKE_TEST_TOPIC = "sentinelai.smoke-test"
CONSUMER_GROUP = "sentinelai-worker"


async def _consume_loop(consumer: AIOKafkaConsumer, log: BoundLogger) -> None:
    async for record in consumer:
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
    log = get_logger(__name__)

    consumer = create_consumer(settings, SMOKE_TEST_TOPIC, group_id=CONSUMER_GROUP)
    await consumer.start()
    log.info("worker_ready", topic=SMOKE_TEST_TOPIC, group=CONSUMER_GROUP)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    consume_task = asyncio.create_task(_consume_loop(consumer, log))
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
