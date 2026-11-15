import asyncio
import os

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import uvicorn
import asyncpg

user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
db = os.getenv("POSTGRES_DB")


# Shared connection pool across requests; None until the database is reachable
pool: asyncpg.Pool = None


async def connect_to_db():
    """Keep trying until the database is reachable, then create the table.

    The app starts serving without the database so that /ready can report
    "not ready" (pod stays Running, but gets no traffic) instead of crashing.
    """
    global pool
    while pool is None:
        try:
            p = await asyncpg.create_pool(
                host="postgres", port=5432, user=user, password=password,
                database=db, timeout=5,
            )
            # Initialize table and seed the counter row
            async with p.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS counters (
                        id INT PRIMARY KEY,
                        val INT NOT NULL DEFAULT 0
                    );
                    INSERT INTO counters (id, val)
                    VALUES (1, 0)
                    ON CONFLICT (id) DO NOTHING;
                """)
            pool = p
        except Exception as e:
            print(f"Database not available, retrying: {e}", flush=True)
            await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(connect_to_db())
    yield  # The app runs while paused here
    task.cancel()
    if pool is not None:
        await pool.close()


def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise HTTPException(status_code=503, detail="database not connected")
    return pool

# Pass lifespan context manager directly to FastAPI initialization
app = FastAPI(lifespan=lifespan)

# Used by the GKE load balancer health check (see manifests/healthcheck.yaml).
# Must not touch the counter, unlike "/".
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# Readiness probe: ready only if the database answers a query right now.
@app.get("/ready")
async def ready():
    try:
        async with get_pool().acquire(timeout=2) as conn:
            await conn.fetchval("SELECT 1;", timeout=2)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="database not reachable")
    return {"status": "ready"}

# In exercise 3.4, we introduce route rewriting, so instead of the /pingpong route we will use the root route /.
@app.get("/")
async def increment_counter():
    async with get_pool().acquire() as conn:
        val = await conn.fetchval("""
            UPDATE counters 
            SET val = val + 1 
            WHERE id = 1 
            RETURNING val;
        """)
        return {"message": "pong", "counter": val}

@app.get("/pings")
async def get_counter():
    async with get_pool().acquire() as conn:
        val = await conn.fetchval("SELECT val FROM counters WHERE id = 1;")
        return {"counter": val}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
