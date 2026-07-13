from fastapi import FastAPI
import os
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
	return {"message": "Todo app is running"}

if __name__ == "__main__":
	port = int(os.environ.get("PORT", 8000))
	print("Server started in port " + str(port), flush=True)
	uvicorn.run("todo_app:app", host="127.0.0.1", port=port, reload=True)
