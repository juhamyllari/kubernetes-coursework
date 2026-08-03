import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, StringConstraints
from typing import Annotated
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select

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

# Pydantic schema for validation
TodoText = Annotated[str, StringConstraints(max_length=140)]

class TodoCreate(BaseModel):
    text: TodoText

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
        return new_todo.text

if __name__ == "__main__":
    BACKEND_PORT = int(os.environ["BACKEND_PORT"])
    import uvicorn
    uvicorn.run("todo_backend:app", host="0.0.0.0", port=BACKEND_PORT, reload=True)
    