import json, os, asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from utils.ConnectionManager import ConnectionManager

from meeting import Meeting
#from db.models import Comment, Scanned

from urllib.parse import urlparse
import asyncio

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
    manager = ConnectionManager(websocket)
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
                meet = await asyncio.to_thread(current_meeting.launch_task)
                meet.loop.stop()
                break
                #await current_meeting.launch_task()
                #break
            else:
                print("Unknown payload cmd received from frontend.", from_frontend)
                break

        # end meeting
        manager.disconnect(meeting_id)

    except WebSocketDisconnect:
        manager.disconnect(meeting_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
