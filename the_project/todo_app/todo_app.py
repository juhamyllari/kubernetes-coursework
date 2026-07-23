import os
import time
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

STORAGE_DIR = os.environ.get("STORAGE_DIR", "/data")
IMAGE_PATH = os.path.join(STORAGE_DIR, "cached_image.jpg")
IMAGE_SOURCE_URL = "https://picsum.photos/600/450"
IMAGE_MAX_AGE = 600

def get_image_age():
    if os.path.exists(IMAGE_PATH):
        return time.time() - os.path.getmtime(IMAGE_PATH)
    return float('inf')

def fetch_new_image():
    response = requests.get(IMAGE_SOURCE_URL)
    if response.status_code == 200:
        with open(IMAGE_PATH, "wb") as f:
            f.write(response.content)

@app.get("/image")
async def serve_image():
    if os.path.exists(IMAGE_PATH):
        with open(IMAGE_PATH, "rb") as f:
            return Response(content=f.read(), media_type="image/jpeg")
    return Response(status_code=404, content="No image cached yet.")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    if get_image_age() > IMAGE_MAX_AGE:
        fetch_new_image()
    return templates.TemplateResponse(request, "index.html")

if __name__ == "__main__":
	port = 3000
	print("Server started in port " + str(port), flush=True)
	uvicorn.run("todo_app:app", host="0.0.0.0", port=port, reload=True)
