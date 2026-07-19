from fastapi import FastAPI
import uvicorn

app = FastAPI()

data_file_path = "/data/pingpong_counter.txt"

# Initialize the counter from the file if it exists,
# otherwise create the file and start at 0.
try:
    with open(data_file_path, "r") as f:
        counter = int(f.read().strip())
except FileNotFoundError:
    counter = 0
    with open(data_file_path, "w") as f:
        f.write(str(counter))

@app.get("/pingpong")
# In this new version, we will write to a file in the /data directory,
# which is mounted to a persistent volume.
def pingpong():
    global counter
    counter += 1
    with open(data_file_path, "w") as f:
        f.write(str(counter))
    return {"message": "pong", "counter": counter}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
