from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
	return HTMLResponse(
		content="""
		<!doctype html>
		<html lang="en">
		  <head>
		    <meta charset="utf-8" />
		    <meta name="viewport" content="width=device-width, initial-scale=1" />
		    <title>To Do app</title>
		  </head>
		  <body>
		    <h1>Welcome to the To Do app</h1>
		  </body>
		</html>
		""",
		media_type="text/html",
	)

if __name__ == "__main__":
	port = int(os.environ.get("PORT", 3000))
	print("Server started in port " + str(port), flush=True)
	uvicorn.run("todo_app:app", host="0.0.0.0", port=port, reload=True)
