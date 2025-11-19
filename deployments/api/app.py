from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def read_root():
    env_name = os.environ.get("ENV_NAME", "not set")
    return {"message": f"Hello from the API endpoint in environment: {env_name}"}

@app.get("/health")
def health():
    return {"status": "healthy"}