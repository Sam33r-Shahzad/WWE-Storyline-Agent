from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from workflow import run_agent

app = FastAPI(title="WWE Creative Story Writer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SANDBOX_DIR = Path(__file__).parent / "sandbox"
SANDBOX_DIR.mkdir(exist_ok=True)

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default-session"


@app.post("/chat")
def chat(request: ChatRequest):
    return run_agent(request.message, request.thread_id)


@app.get("/scripts")
def list_scripts():
    files = [f.name for f in SANDBOX_DIR.glob("*.md")]
    return {"scripts": files}


@app.get("/download/{filename}")
def download_script(filename: str):
    file_path = SANDBOX_DIR / filename
    if not file_path.exists():
        return {"error": "File not found"}
    return FileResponse(file_path, filename=filename, media_type="text/markdown")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)