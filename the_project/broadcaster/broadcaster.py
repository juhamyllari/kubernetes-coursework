import asyncio
import json
import logging
import os
import signal
import sys

import httpx
import nats
import structlog

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger()

NATS_URL = os.environ["NATS_URL"]
SUBJECT = os.environ.get("NATS_SUBJECT", "todos.events")
# All replicas join the same queue group, so NATS delivers each message to
# exactly one of them. This is what prevents duplicates when scaled.
QUEUE = os.environ.get("NATS_QUEUE", "broadcaster")
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

# Hygiene: the message text is built here from a fixed vocabulary. Nothing
# from the incoming payload is forwarded except the event type (checked
# against this list) and the numeric id.
EVENT_TEXT = {
    "created": "A todo was created",
    "updated": "A todo was updated",
}


def build_payload(raw: bytes) -> dict | None:
    try:
        event = json.loads(raw)
        text = EVENT_TEXT[event["event"]]
        todo_id = event.get("id")
    except (ValueError, KeyError, TypeError):
        return None
    if isinstance(todo_id, int) and not isinstance(todo_id, bool):
        text += f" (id {todo_id})"
    return {"user": "bot", "message": text}


async def main():
    http = httpx.AsyncClient(timeout=5)

    async def handler(msg):
        payload = build_payload(msg.data)
        if payload is None:
            logger.warning("Ignoring malformed event")
            return
        try:
            resp = await http.post(WEBHOOK_URL, json=payload)
            resp.raise_for_status()
            logger.info("Forwarded", message=payload["message"])
        except httpx.HTTPError as e:
            # At-most-once: a lost message is acceptable, a duplicate is not.
            logger.warning("Forwarding failed", error=str(e))

    nc = await nats.connect(NATS_URL, max_reconnect_attempts=-1)
    await nc.subscribe(SUBJECT, queue=QUEUE, cb=handler)
    logger.info("Subscribed", subject=SUBJECT, queue=QUEUE)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    await stop.wait()
    await nc.drain()
    await http.aclose()


if __name__ == "__main__":
    asyncio.run(main())
