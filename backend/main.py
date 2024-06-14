import json, os, logging
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
#from chain import chain
from db.database import Database
from utils.ConnectionManager import ConnectionManager

from meeting import Meeting, ExpertModel, TaskContext
from crewai import Agent, Task, Crew, Process
from textwrap import dedent
from utils.LLMs import get_llm, get_max_num_iterations
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
            from_frontend = json.loads(data)
            # TODO: detect command from frontend first
            if not from_frontend["cmd"]: 
                break
            if from_frontend["cmd"] == "create_meeting":
                current_meeting = Meeting(
                    manager=manager,
                    experts=from_frontend["experts"],
                    meeting_id=meeting_id,
                    meta=from_frontend["meta"]
                )
                await current_meeting.launch_task()
                #break
            else:
                print("Unknown payload cmd received from frontend.", from_frontend)
                break

        # end meeting
        manager.disconnect(websocket, meeting_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, meeting_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
