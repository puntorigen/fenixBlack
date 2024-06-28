import json, os, asyncio, base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from contextlib import asynccontextmanager
from utils import ConnectionManager, get_encryption_key_base64, decryptJSON
from dotenv import load_dotenv

from meeting import Meeting
#from db.models import Session
from db.database import Database
db = Database()
load_dotenv()
public_url = None

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

@app.websocket("/meeting/{meeting_id}")
async def websocket_endpoint_meeting(websocket: WebSocket, meeting_id: str):
    manager = ConnectionManager() #websocket
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
            elif from_frontend["cmd"] == "phone_call":
                print(f"DEBUG: Received phone call command: {from_frontend}")
                await manager.send_message(json.dumps({
                    "cmd": "phone_call_ended",
                    "data": "Phone call ended." 
                }), meeting_id)
                pass
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
from twilio.rest import Client
from pydantic import BaseModel
from utils import CallManager

#mulaw
twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
call_managers = {}
meeting_to_callsid = {}

class CallRequest(BaseModel):
    to_number: str
    meeting_id: str
    voice_id: str

#@app.post("/call")
@app.get("/call/{to_number}")
async def make_call(to_number: str): #request: CallRequest):
    request = {
        "to_number": to_number,
        "meeting_id": "1235",
        "voice_id": "1234"
    }
    # Fetch the list of purchased phone numbers
    incoming_phone_numbers = twilio_client.incoming_phone_numbers.list()
    
    if not incoming_phone_numbers:
        raise HTTPException(status_code=400, detail="No available phone numbers.")
    
    # Grab the first available phone number
    from_number = incoming_phone_numbers[0].phone_number

    # Make a call using Twilio and connect it to the websocket endpoint with meeting_id and voice_id parameters
    call = twilio_client.calls.create(
        twiml=f'<Response><Connect><Stream url="wss://{public_url}/audio/{request["meeting_id"]}"/></Connect></Response>',
        to=request["to_number"],
        from_=from_number
    )
    return {"status": "call initiated", "sid": call.sid, "from": from_number, "url": f"wss://{public_url}/audio/{request["meeting_id"]}" }

async def deepgram_connect():
    import websockets
    DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen?encoding=mulaw&sample_rate=8000&channels=1&multichannel=false&model=nova-2&language=es&punctuate=true&smart_format=false"
    extra_headers = {
        'Authorization': f'Token {os.getenv("DEEPGRAM_API_KEY")}'
    }
    deepgram_ws = await websockets.connect(DEEPGRAM_WS_URL, extra_headers=extra_headers)
    return deepgram_ws

@app.websocket("/audio/{meeting_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str):
    print("Audio websocket connected")
    ### the websocket endpoint should be kept here
    audio_manager = ConnectionManager()
    await audio_manager.connect(websocket, meeting_id)
    audio_queue = asyncio.Queue()
    callsid_queue = asyncio.Queue()
    deepgram_ws = await deepgram_connect()
    stream_sids = {} #dict mapping callsid to streamSid

    try:
        await asyncio.gather(
            deepgram_sender(deepgram_ws, audio_queue),
            deepgram_receiver(deepgram_ws, callsid_queue, meeting_id, audio_manager, stream_sids),
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
async def deepgram_receiver(deepgram_ws, callsid_queue, meeting_id, audio_manager, stream_sids):
    global call_managers
    global meeting_to_callsid
    callsid = await callsid_queue.get()
    meeting_to_callsid[meeting_id] = callsid
    if callsid not in call_managers:
        call_managers[callsid] = CallManager(audio_manager, meeting_id, callsid, stream_sids, os.getenv("GROQ_API_KEY"), os.getenv("ELEVEN_LABS_API_KEY"))
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
        except WebSocketDisconnect:
            break

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
