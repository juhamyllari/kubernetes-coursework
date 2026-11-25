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
# The URL may be a credential (e.g. a Discord webhook): never log it.
# If it is not set (staging), the messages are only logged, not forwarded.
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
# "generic": {"user", "message"}; "discord": {"username", "content"}.
WEBHOOK_FORMAT = os.environ.get("WEBHOOK_FORMAT", "generic")

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
    if WEBHOOK_FORMAT == "discord":
        return {"username": "todo-bot", "content": text}
    return {"user": "bot", "message": text}


async def main():
    http = httpx.AsyncClient(timeout=5)

    async def handler(msg):
        payload = build_payload(msg.data)
        if payload is None:
            logger.warning("Ignoring malformed event")
            return
        if WEBHOOK_URL is None:
            logger.info("Not forwarded (no webhook configured)", message=payload.get("message") or payload["content"])
            return
        try:
            resp = await http.post(WEBHOOK_URL, json=payload)
            resp.raise_for_status()
            logger.info("Forwarded", message=payload.get("message") or payload["content"])
        except httpx.HTTPError as e:
            # At-most-once: a lost message is acceptable, a duplicate is not.
            # str(e) can embed the URL, so log only the status or error type.
            status = e.response.status_code if isinstance(e, httpx.HTTPStatusError) else None
            logger.warning("Forwarding failed", status=status, error=type(e).__name__)

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
