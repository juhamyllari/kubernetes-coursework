from fastapi import FastAPI, Body, status
from pydantic import constr
import uvicorn

app = FastAPI()

todos: list[str] = ["Learn k3d", "????", "Profit!"]


@app.get("/api/todos")
def get_todos() -> list[str]:
    return todos


@app.put("/api/todos", status_code=status.HTTP_201_CREATED)
def create_todo(todo: constr(max_length=140) = Body(...)) -> str:
    todos.append(todo)
    return todo

if __name__ == "__main__":
	port = 3000
	print("Server started in port " + str(port), flush=True)
	uvicorn.run("todo_backend:app", host="0.0.0.0", port=port, reload=True)
