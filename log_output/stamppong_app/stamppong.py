import os
import uuid
from datetime import datetime, timezone
import httpx
from fastapi import FastAPI, Response, status

app = FastAPI()

# Server UUID generated once at module startup
SERVER_UUID = str(uuid.uuid4())

# Read environment variable at startup
COUNTER_SERVICE_URL = os.environ.get(
    "COUNTER_SERVICE_URL", 
    "http://pingpong-svc:2345/pings"
)

if "COUNTER_SERVICE_URL" in os.environ:
    print(f"COUNTER_SERVICE_URL is set to: {COUNTER_SERVICE_URL}")
else:
    print(f"COUNTER_SERVICE_URL is not set, using default: {COUNTER_SERVICE_URL}")

# Read file content from ConfigMap at startup
CONFIG_FILE_PATH = "/etc/config/information.txt"
if os.path.exists(CONFIG_FILE_PATH):
    with open(CONFIG_FILE_PATH, "r") as file:
        config_file_content = file.read().rstrip("\n")
    print(f"ConfigMap file content:\n{config_file_content}")

# Read MESSAGE from ConfigMap at startup
MESSAGE = os.environ.get("MESSAGE", "Hello, World!")

combined_message = f"file content: {config_file_content}\nenv variable: MESSAGE={MESSAGE}"

async def get_pong_count() -> int:
    """Fetch the current counter value asynchronously from the pingpong service."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(COUNTER_SERVICE_URL)
            response.raise_for_status()
            data = response.json()
            return data.get("counter", 0)
    except Exception as e:
        print(f"Error fetching pong count: {e}")
        return -1


@app.get("/", response_class=Response)
async def read_root():
    pong_count = await get_pong_count()
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    body = f"{combined_message}\n{timestamp}: {SERVER_UUID}.\nPing / Pongs: {pong_count}"

    return Response(content=body, media_type="text/plain; charset=utf-8")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
