import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, StringConstraints, field_validator
from typing import Annotated
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select
import logging
import structlog

logging.basicConfig(level=logging.INFO)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

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

@app.get("/api/todos", response_model=list[str])
async def get_todos():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(TodoItem.text))
        return list(result.scalars().all())

@app.put("/api/todos", status_code=status.HTTP_201_CREATED, response_model=str)
async def create_todo(payload: TodoCreate):
    async with AsyncSessionLocal() as session:
        new_todo = TodoItem(text=payload.text)
        session.add(new_todo)
        await session.commit()
        logger.info("Created new todo item", text=payload.text)
        return new_todo.text

if __name__ == "__main__":
    BACKEND_PORT = int(os.environ["BACKEND_PORT"])
    import uvicorn
    uvicorn.run("todo_backend:app", host="0.0.0.0", port=BACKEND_PORT, reload=True)
    