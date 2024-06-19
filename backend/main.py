import json, os, asyncio, base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from utils.ConnectionManager import ConnectionManager
from urllib.parse import urlparse
from Crypto.Cipher import AES
import asyncio

from meeting import Meeting
from utils.cypher import get_encryption_key_base64, decryptJSON

#from db.models import Session
#from db.database import Database
#db = Database()

# Configure logging
#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)

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
            if from_frontend["cmd"] == "req_session_key":
                # first cmd to be received
                # for secure exchange of data
                # @TODO save it in the database related to the fingerprint (Sessions model)
                encryption_key = get_encryption_key_base64(from_frontend["fingerprint"])
                await manager.send_message(json.dumps({
                    "action": "session_key",
                    "key": encryption_key 
                }), meeting_id)
                #session = Session(fingerprint=from_frontend["fingerprint"], encryption_key=encryption_key)
                #db.add(session)

            elif from_frontend["cmd"] == "create_meeting":
                try:
                    if from_frontend["settings"]:
                        from_frontend["settings"] = decryptJSON(from_frontend["settings"], from_frontend["fingerprint"])
                        print(f"DEBUG settings: {from_frontend['settings']}")
                    
                except Exception as e:
                    # error decrypting settings, abort meeting creation
                    print(f"Error decrypting settings: {str(e)}")
                    raise

                current_meeting = Meeting(
                    manager=manager,
                    experts=from_frontend["experts"],
                    meeting_id=meeting_id,
                    meta=from_frontend["meta"],
                    settings=from_frontend["settings"]
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
        try:
            manager.disconnect(websocket,meeting_id)
        except Exception as e:
            pass

    except WebSocketDisconnect:
        manager.disconnect(websocket,meeting_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
