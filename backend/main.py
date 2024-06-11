import json, os, logging
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
#from chain import chain
from db.database import Database
from utils.ConnectionManager import ConnectionManager
#from db.models import Comment, Scanned

from urllib.parse import urlparse

# Configure logging
#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)

#db = Database()
#schemas = None

def setup():
    openai_api_key = os.getenv('OPENAI_API_KEY')
    # set OpenAI api key or install & use Ollama
    if openai_api_key:
        os.environ["LLM_TYPE"] = "openai"
        os.environ["OPENAI_API_KEY"] = openai_api_key
        os.environ["OPENAI_MODEL_NAME"] = "gpt-4" # the best model for these tasks
    else:
        os.environ["LLM_TYPE"] = "ollama"
        os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:11434" # Ollama API base URL; use docker instance name inside actions
        os.environ["OPENAI_API_KEY"] = "ollama"

@asynccontextmanager
async def lifespan(app: FastAPI):
    global schemas
    setup()
    print("Application has started.")
    yield
    # Cleanup code can go here (if needed)
    print("Application shutdown.")

app = FastAPI(lifespan=lifespan)

@app.websocket("/meeting/{meeting_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str):
    manager = ConnectionManager()
    await manager.connect(websocket, meeting_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_message(f"Broadcast in {meeting_id}: {data}", meeting_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, meeting_id)

@app.get("/test")
async def test():
    #test endpoint
    print("DEBUG: hello called")
    return "hello "+os.environ["LLM_TYPE"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
