import os

import uvicorn
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()


@app.get("/")
def read_log() -> PlainTextResponse:
    log_file_path = os.environ.get("LOG_FILE_PATH", "/data/file_logger.log")
    if os.path.exists(log_file_path):
        with open(log_file_path, "r", encoding="utf-8") as log_file:
            contents = log_file.read()
    else:
        contents = ""
    return PlainTextResponse(contents)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
