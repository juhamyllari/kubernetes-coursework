import json
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import os
import uvicorn
import time

app = FastAPI()
templates = Jinja2Templates(directory="templates")

STORAGE_DIR = os.environ.get("STORAGE_DIR", "/data")
IMAGE_PATH = os.path.join(STORAGE_DIR, "cached_image.jpg")
IMAGE_SOURCE_URL = "https://picsum.photos/800/600"
IMAGE_MAX_AGE = 600  # In seconds

print("Storage directory: " + STORAGE_DIR, flush=True)

def get_image_age():
		if os.path.exists(IMAGE_PATH):
				return time.time() - os.path.getmtime(IMAGE_PATH)
		else:
				return float('inf')

# Get new image from the source URL and save it to the storage directory.
def fetch_new_image():
		response = requests.get(IMAGE_SOURCE_URL)
		if response.status_code == 200:
				with open(IMAGE_PATH, "wb") as f:
						f.write(response.content)
				print("Fetched new image from source URL.", flush=True)
		else:
				print("Failed to fetch image from source URL.", flush=True)

@app.get("/image")
async def serve_image():
    """Serves the raw image bytes directly from the persistent volume."""
    if os.path.exists(IMAGE_PATH):
        with open(IMAGE_PATH, "rb") as f:
            return Response(content=f.read(), media_type="image/jpeg")
    return Response(status_code=404, content="No image cached yet.")

@app.get("/")
def read_root(request: Request):
	image_age = get_image_age()
	if image_age > IMAGE_MAX_AGE:
		print(f"Cached image age {image_age:.2f}s exceeds max age {IMAGE_MAX_AGE:.2f}s. Fetching new image.", flush=True)
		fetch_new_image()
	else:
		print(f"Cached image age {image_age:.2f}s is within max age {IMAGE_MAX_AGE:.2f}s. Using cached image.", flush=True)
	return templates.TemplateResponse(request, "index.html")

if __name__ == "__main__":
	port = int(os.environ.get("PORT", 3000))
	print("Server started in port " + str(port), flush=True)
	uvicorn.run("todo_app:app", host="0.0.0.0", port=port, reload=True)
