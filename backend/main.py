import json, os, asyncio, base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Form
from contextlib import asynccontextmanager
from utils import ConnectionManager, get_encryption_key_base64, decryptJSON
from dotenv import load_dotenv

from meeting import Meeting
#from db.models import Session
from db.database import Database
db = Database()
load_dotenv()
public_url = None
call_sessions = {}

# Call related
from pydantic import BaseModel
from tools.phone.utils import CallManager
from schemas import ExpertModel
from utils import ExpertSolo, messages
from typing import Dict, Any

# Configure logging
#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)
                
def start_ngrok():
    global public_url
    from pyngrok import ngrok
    public_url = ngrok.connect(8000,"http").public_url.replace("tcp://", "").replace("http://", "").replace("https://", "")
    print(' * Tunnel URL:', public_url)

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
    start_ngrok()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global schemas
    setup()
    print("Application has started.")
    yield
    # Cleanup code can go here (if needed)
    print("Application shutdown.")

app = FastAPI(lifespan=lifespan)
manager = ConnectionManager() #websocket

@app.websocket("/meeting/{meeting_id}")
async def websocket_endpoint_meeting(websocket: WebSocket, meeting_id: str):
    global call_sessions    
    await manager.connect(websocket, meeting_id)
    try: 
        while True:
            data = await websocket.receive_text()
            from_frontend = json.loads(data)
            # TODO: detect command from frontend first
            if 'cmd' not in from_frontend: 
                continue
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
                    settings=from_frontend["settings"],
                    user_fingerprint=from_frontend["fingerprint"]
                )
                meet = await asyncio.to_thread(current_meeting.launch_task)
                meet.loop.stop()
                break
                #await current_meeting.launch_task()
                #break
            elif from_frontend["cmd"] == "phone_call":
                # from_frontend["settings"] => contains the USER decrypted envs
                print(f"DEBUG: Received phone call command: {from_frontend}")
                session_id = from_frontend["data"]["session_id"]
                session_envs = decryptJSON(from_frontend["data"]["envs"], from_frontend["data"]["user_fingerprint"])
                print(f"DEBUG: Decrypted envs: {session_envs}")
                # create a call session
                call_sessions[session_id] = from_frontend["data"]
                call_expert = ExpertModel(**from_frontend["data"]["expert"])
                # notify the user what the tool is doing ('creating expert for the call')
                notify = messages(
                    manager=manager,
                    session_id=session_id,
                    expert=call_expert,
                    meeting_id=meeting_id
                )
                call_sessions[session_id]["notify_ref"] = notify
                await notify.from_tool("phone_call", "I'm preparing for the call")
                # create an ExpertSolo instance with the expert data
                call_expert_solo = ExpertSolo( 
                    expert = call_expert,
                    session_data = from_frontend["data"],
                    vector_config = from_frontend["data"]["config"], 
                    session_id = session_id, 
                    language = from_frontend["data"]["language"],
                    envs = session_envs,
                    public_url = public_url
                )
                call_sessions[session_id]["expert_ref"] = call_expert_solo
                call_sessions[session_id]["envs"] = session_envs
                #await notify.from_tool("phone_call", "Expert ready to make call ..")                
                # TODO: trigger phone call to requested number
                await notify.from_tool("phone_call", f"Calling {call_sessions[session_id]["user_name"]} at {call_sessions[session_id]["number"]} ...")                
                await call_expert_solo.make_phone_call(call_sessions[session_id]["number"], meeting_id)
                # closing steps
                # TODO: when finished, send a message to the 'call tool' with the call data from the CallManager (not here)
                #await notify.to_tool("phone_call_ended",{ "text":"Phone call ended" })
                # also destroy the session
                #del call_sessions[session_id] 

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


### TESTING TWILIO ENDPOINT: we should move this later into the 'call' tool ###
#mulaw
call_managers = {}
meeting_to_callsid = {}
audio_manager = ConnectionManager()

async def deepgram_connect(language="es"):
    import websockets 
    print(f"DEBUG: connecting deepgram websocket for language: {language}")
    # english listening is the default
    DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen?encoding=mulaw&sample_rate=8000&channels=1&multichannel=false&model=nova-2-phonecall&language=en&punctuate=true&smart_format=true"
    if language in ["es","es-ES","es-CL"]:
        DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen?encoding=mulaw&sample_rate=8000&channels=1&multichannel=false&model=nova-2&language=es&punctuate=true&smart_format=false"
    extra_headers = {
        'Authorization': f'Token {os.getenv("DEEPGRAM_API_KEY")}'
    }
    deepgram_ws = await websockets.connect(DEEPGRAM_WS_URL, extra_headers=extra_headers)
    return deepgram_ws

@app.post("/callstatus/{session_id}/{meeting_id}")
async def call_status(session_id: str, meeting_id: str, request: Request):
    global call_sessions
    item_data = await request.form()
    item = dict(item_data)
    print(f"Call status received for session {session_id} in meeting {meeting_id}",item)
    # check if we have a global session for this status first
    if session_id not in call_sessions:
        print(f"Session for status not found: {session_id}")
        return {"status": "Error", "message": "Session for status not found" }
    session_obj = call_sessions[session_id]
    if item.get("CallStatus", "") == "ringing":
        await session_obj["notify_ref"].from_tool("phone_call","Ringing ..")
    elif item.get("CallStatus", "") == "answered" or item.get("CallStatus", "") == "in-progress":
        await session_obj["notify_ref"].from_tool("phone_call","The user just picked up the phone ..")
    elif item.get("CallStatus", "") == "failed":
        # phone number seems to be invalid
        print(f"Call ended (failed) for session {session_id} in meeting {meeting_id}")
        await session_obj["notify_ref"].from_tool("phone_call","The user phone number seems to be invalid")
        await session_obj["notify_ref"].to_tool("phone_call_ended",{ "text":"Invalid phone number", "reason":"invalid" })
        # also destroy the session
        del call_sessions[session_id]
        return {"status": "OK", "message": "Call ended, because phone number seems to be invalid"}
    
    elif item.get("CallStatus", "") == "busy" or item.get("CallStatus", "") == "no-answer":
        # phone is busy
        print(f"Call ended ({item.get("CallStatus", "")}) for session {session_id} in meeting {meeting_id}")
        await session_obj["notify_ref"].from_tool("phone_call","The user was was busy or declined the call")
        await session_obj["notify_ref"].to_tool("phone_call_ended",{ "text":"Target phone was busy", "reason":"busy" })
        # also destroy the session
        del call_sessions[session_id] 
        return {"status": "OK", "message": "Call ended, because phone was busy"}

    elif item.get("CallStatus", "") == "completed":
        # call ended 
        print(f"Call ended for session {session_id} in meeting {meeting_id}")
        await session_obj["notify_ref"].from_tool("phone_call","Call ended")
        await session_obj["notify_ref"].to_tool("phone_call_ended",{ "text":"Phone call ended", "reason":"ended" })
        # also destroy the session
        del call_sessions[session_id]
        return {"status": "OK", "message": "Call ended"}

    return {"status": "OK"}

@app.websocket("/audio/{session_id}/{meeting_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, meeting_id: str):
    print("Audio websocket connected")
    ### the websocket endpoint should be kept here
    global call_sessions
    await audio_manager.connect(websocket, meeting_id)
    audio_queue = asyncio.Queue()
    callsid_queue = asyncio.Queue()
    session_obj = call_sessions[session_id]
    deepgram_ws = await deepgram_connect(session_obj["language"])
    stream_sids = {} #dict mapping callsid to streamSid

    try:
        await asyncio.gather(
            deepgram_sender(deepgram_ws, audio_queue),
            deepgram_receiver(deepgram_ws, callsid_queue, session_id, meeting_id, audio_manager, stream_sids),
            twilio_receiver(websocket, audio_queue, callsid_queue, stream_sids)
        )
    except WebSocketDisconnect:
        audio_manager.disconnect(websocket, meeting_id)
        await handle_call_end(meeting_id)
    finally:
        if deepgram_ws.open:
            await deepgram_ws.send(json.dumps({
                "type": "CloseStream"
            }))
            await deepgram_ws.close()
        # Cleanup resources for the callsid
        if meeting_id in meeting_to_callsid:
            await handle_call_end(meeting_id)

async def deepgram_sender(deepgram_ws, audio_queue):
    while True:
        chunk = await audio_queue.get()
        if chunk is None:  # Signal to close
            break
        if deepgram_ws.open:
            await deepgram_ws.send(chunk)
        else:
            # we should close the websocket here
            print("Websocket to Deepgram is closed, dropping audio chunk")
            break

# get the transcription 
async def deepgram_receiver(deepgram_ws, callsid_queue, session_id, meeting_id, audio_manager, stream_sids):
    global call_managers
    global meeting_to_callsid
    callsid = await callsid_queue.get()
    meeting_to_callsid[meeting_id] = callsid
    if callsid not in call_managers:
        session_obj = call_sessions[session_id]
        call_managers[callsid] = CallManager(audio_manager, session_obj, meeting_id, callsid, stream_sids, os.getenv("GROQ_API_KEY"), os.getenv("ELEVEN_LABS_API_KEY"))
    call_manager = call_managers[callsid]

    try:
        async for message in deepgram_ws:
            #transcript_session
            #print(f"Received transcription for call {callsid}: {message}")
            data = json.loads(message)
            transcription = data.get('channel', {}).get('alternatives', [{}])[0].get('transcript', '')
            call_manager.add_transcription_part(transcription)
    except Exception as e:
        if meeting_id in meeting_to_callsid:
            await handle_call_end(meeting_id)

async def handle_call_end(meeting_id):
    global call_managers
    global meeting_to_callsid
    callsid = meeting_to_callsid.get(meeting_id)
    if callsid:
        # Clean up resources for the callsid
        if callsid in call_managers:
            call_manager = call_managers.pop(callsid)
            print(f"Cleanup resources for callsid: {callsid}")
            # Add any cleanup code needed within SilenceManager
            call_manager.cleanup()
        
        # Remove the mapping once cleanup is complete
        del meeting_to_callsid[meeting_id]


async def twilio_receiver(twilio_ws, audio_queue, callsid_queue, stream_sids):
    while True:
        try:
            message = await twilio_ws.receive_text()
            data = json.loads(message)

            if data['event'] == 'start':
                callsid = data['start']['callSid']
                stream_sid = data['start']['streamSid']
                await callsid_queue.put(callsid)
                stream_sids[callsid] = stream_sid  # Store streamSid associated with callsid

            elif data['event'] == 'media':
                chunk = base64.b64decode(data['media']['payload'])
                await audio_queue.put(chunk)

            elif data['event'] == 'stop':
                await audio_queue.put(None)  # Signal the end of stream
                break
            else:
                print(f"Unknown message received from Twilio: {data}")
                #break

        except WebSocketDisconnect:
            break

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
