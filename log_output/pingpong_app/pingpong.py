import os

from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import asyncpg

user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
db = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql://{user}:{password}@postgres:5432/{db}"

# Shared connection pool across requests
pool: asyncpg.Pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    global pool
    pool = await asyncpg.create_pool(dsn=DATABASE_URL)
    
    # Initialize table and seed the counter row
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS counters (
                id INT PRIMARY KEY,
                val INT NOT NULL DEFAULT 0
            );
            INSERT INTO counters (id, val) 
            VALUES (1, 0) 
            ON CONFLICT (id) DO NOTHING;
        """)
    
    yield  # The app runs while paused here

    # --- SHUTDOWN LOGIC ---
    await pool.close()

# Pass lifespan context manager directly to FastAPI initialization
app = FastAPI(lifespan=lifespan)

@app.get("/pingpong")
async def increment_counter():
    async with pool.acquire() as conn:
        val = await conn.fetchval("""
            UPDATE counters 
            SET val = val + 1 
            WHERE id = 1 
            RETURNING val;
        """)
        return {"message": "pong", "counter": val}

@app.get("/pings")
async def get_counter():
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT val FROM counters WHERE id = 1;")
        return {"counter": val}

# For GKE health checks we need a simple endpoint that returns 200 OK
@app.get("/")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
