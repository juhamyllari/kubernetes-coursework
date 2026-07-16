import asyncio
import sys
from datetime import datetime, timezone
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

# Global state to keep track of the generated string and the last log time
app_state = {
    "uuid": str(uuid.uuid4()),
    "last_logged_at": None,
}

# 1. Adapt your loop to be cooperative (async)
async def log_periodically():
    while True:
        now_utc = datetime.now(timezone.utc)
        iso_string = now_utc.isoformat().replace("+00:00", "Z")
        
        # Update state
        app_state["last_logged_at"] = iso_string
        
        # Original print & flush behavior
        print(f"{iso_string}: {app_state['uuid']}")
        sys.stdout.flush()
        
        # Yield control to the event loop for 5 seconds
        await asyncio.sleep(5)

# 2. Manage the background task lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the logger in the background
    logging_task = asyncio.create_task(log_periodically())
    yield
    # Clean up on shutdown
    logging_task.cancel()
    try:
        await logging_task
    except asyncio.CancelledError:
        pass

# 3. Create the app and define the endpoint
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return {
        "status": "running",
        "last_log": app_state["last_logged_at"],
        "uuid": app_state["uuid"]
    }

if __name__ == "__main__":
    uvicorn.run("log_output:app", host="0.0.0.0", port=8000, log_level="info")
