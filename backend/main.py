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

            current_meeting = Meeting(
                manager=manager,
                meeting_id=meeting_id,
                name=from_frontend["meta"]["name"], 
                context=from_frontend["meta"]["context"], 
                task=from_frontend["meta"]["task"], 
                schema=from_frontend["meta"]["schema"]
            )
            #print("data received",from_frontend)
            # build experts
            # for every expert on from_frontend["experts"] (Dict), create an expert, append to experts list
            experts = []
            for expert in from_frontend["experts"]:
                expert_object = from_frontend["experts"][expert]
                expert_json = ExpertModel(**expert_object)
                expert_ = current_meeting.create_expert(expert=expert_json)
                experts.append(expert_)
            print("DEBUG: experts",experts) 
            # build task and crew
            #result = await current_meeting.launch_task(experts,TaskContext(**from_frontend["meta"]))
            await current_meeting.launch_task(experts,TaskContext(**from_frontend["meta"]))
            # end meeting

    except WebSocketDisconnect:
        manager.disconnect(websocket, meeting_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
