import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator
from typing import Annotated
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select, text, false
import json
import logging
import structlog
import nats

# Plain message only, to stdout: Cloud Logging parses single-line JSON into
# jsonPayload and stderr output would otherwise be labelled ERROR.
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")


def add_gcp_severity(logger, method_name, event_dict):
    """Rename structlog's 'level' to the 'severity' field Cloud Logging reads."""
    level = event_dict.pop("level", method_name).upper()
    event_dict["severity"] = "WARNING" if level == "WARN" else level
    return event_dict


structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_gcp_severity,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

MAX_TODO_LENGTH = int(os.getenv("MAX_TODO_LENGTH"))
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
DB_HOST = os.environ.get("POSTGRES_HOST")
DB_PORT = os.environ.get("POSTGRES_PORT")
DB_NAME = os.environ.get("POSTGRES_DB")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class TodoItem(Base):
    __tablename__ = "todos"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(nullable=False)
    done: Mapped[bool] = mapped_column(default=False, server_default=false(), nullable=False)

NATS_URL = os.environ.get("NATS_URL")
NATS_SUBJECT = os.environ.get("NATS_SUBJECT", "todos.events")
nats_client = None

async def publish_event(event: str, todo_id: int):
    """Best-effort status event for the broadcaster. Carries only the event
    type and the todo id, never the todo text. Failures must not break the API."""
    global nats_client
    if not NATS_URL:
        return
    try:
        if nats_client is None or nats_client.is_closed:
            nats_client = await nats.connect(NATS_URL, connect_timeout=2, max_reconnect_attempts=-1)
        await nats_client.publish(NATS_SUBJECT, json.dumps({"event": event, "id": todo_id}).encode())
    except Exception as e:
        logger.warning("Publishing event failed", error=str(e))

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # create_all does not alter existing tables; bring databases created
        # by older versions of the app up to date.
        await conn.execute(text(
            "ALTER TABLE todos ADD COLUMN IF NOT EXISTS done BOOLEAN NOT NULL DEFAULT false"
        ))
    yield
    if nats_client is not None and not nats_client.is_closed:
        await nats_client.drain()

app = FastAPI(lifespan=lifespan)

class TodoCreate(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_length(cls, v: str) -> str:
        if not (1 <= len(v) <= MAX_TODO_LENGTH):
            truncated = v[:1000] + ("..." if len(v) > 1000 else "")
            logger.warning(
                "Rejected todo due to invalid length",
                length=len(v),
                max_length=MAX_TODO_LENGTH,
                text=truncated,
            )
            raise ValueError(
                f"Todo text length must be between 1 and {MAX_TODO_LENGTH} characters."
            )
        return v

class TodoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    text: str
    done: bool

class TodoUpdate(BaseModel):
    done: bool

@app.get("/api/todos", response_model=list[TodoOut])
async def get_todos():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(TodoItem).order_by(TodoItem.id))
        return list(result.scalars().all())

@app.put("/api/todos/{todo_id}", response_model=TodoOut)
async def update_todo(todo_id: int, payload: TodoUpdate):
    async with AsyncSessionLocal() as session:
        todo = await session.get(TodoItem, todo_id)
        if todo is None:
            raise HTTPException(status_code=404, detail="todo not found")
        todo.done = payload.done
        await session.commit()
        logger.info("Updated todo item", id=todo_id, done=payload.done)
        await publish_event("updated", todo_id)
        return todo

@app.put("/api/todos", status_code=status.HTTP_201_CREATED, response_model=str)
async def create_todo(payload: TodoCreate):
    async with AsyncSessionLocal() as session:
        new_todo = TodoItem(text=payload.text)
        session.add(new_todo)
        await session.commit()
        logger.info("Created new todo item", text=payload.text)
        await publish_event("created", new_todo.id)
        return new_todo.text

@app.get("/healthz")
async def ready():
    """Readiness: 200 only if the database answers a trivial query."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        logger.warning("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ready"}

@app.get("/")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    BACKEND_PORT = int(os.environ["BACKEND_PORT"])
    import uvicorn
    uvicorn.run("todo_backend:app", host="0.0.0.0", port=BACKEND_PORT, reload=False)
    