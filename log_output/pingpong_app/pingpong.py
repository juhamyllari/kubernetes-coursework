from fastapi import FastAPI
import uvicorn

app = FastAPI()

counter = 0

@app.get("/pingpong")
# In exercise 2.1, there is no file. We just return the counter in memory.
def pingpong():
    global counter
    counter += 1
    return {"message": "pong", "counter": counter}

# In addition, there is the GET /pings endpoint, which returns the current counter value without incrementing it.
@app.get("/pings")
def get_pings():
    return {"counter": counter}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
