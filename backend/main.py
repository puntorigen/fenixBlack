import json, os, asyncio, base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from contextlib import asynccontextmanager
from utils.ConnectionManager import ConnectionManager
from dotenv import load_dotenv

from meeting import Meeting
from utils.cypher import get_encryption_key_base64, decryptJSON

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
async def websocket_endpoint(websocket: WebSocket, meeting_id: str):
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
import elevenlabs, io, httpx
from twilio.rest import Client
from pydantic import BaseModel
from pydub import AudioSegment
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    PrerecordedOptions,
    FileSource,
)

#mulaw
DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen?encoding=mulaw&sample_rate=8000&channels=1&multichannel=false&model=nova-2&language=es"
twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
deepgram_client = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))

class CallRequest(BaseModel):
    to_number: str
    meeting_id: str
    voice_id: str

#@app.post("/call")
@app.get("/call")
async def make_call(): #request: CallRequest):
    request = {
        "to_number": "+56900000000", #put your test phone number here
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

### the websocket endpoint should be kept here
audio_manager = ConnectionManager()

async def deepgram_connect():
    import websockets
    extra_headers = {
        'Authorization': f'Token {os.getenv("DEEPGRAM_API_KEY")}'
    }
    deepgram_ws = await websockets.connect(DEEPGRAM_WS_URL, extra_headers=extra_headers)
    return deepgram_ws

@app.websocket("/audio/{meeting_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str):
    print("Audio websocket connected")
    await audio_manager.connect(websocket, meeting_id)
    audio_queue = asyncio.Queue()
    callsid_queue = asyncio.Queue()
    deepgram_ws = await deepgram_connect()

    try:
        await asyncio.gather(
            deepgram_sender(deepgram_ws, audio_queue),
            deepgram_receiver(deepgram_ws, callsid_queue, meeting_id, audio_manager),
            twilio_receiver(websocket, audio_queue, callsid_queue, meeting_id)
        )
    except WebSocketDisconnect:
        audio_manager.disconnect(websocket, meeting_id)
    finally:
        if deepgram_ws.open:
            await deepgram_ws.send(json.dump({
                "type": "CloseStream"
            }))
            await deepgram_ws.close()

async def deepgram_sender(deepgram_ws, audio_queue):
    while True:
        chunk = await audio_queue.get()
        if chunk is None:  # Signal to close
            break
        if deepgram_ws.open:
            await deepgram_ws.send(chunk)
        else:
            print("Websocket to Deepgram is closed, dropping audio chunk")

# get the transcription 
async def deepgram_receiver(deepgram_ws, callsid_queue, meeting_id, audio_manager):
    callsid = await callsid_queue.get()
    async for message in deepgram_ws:
        #print(f"Received transcription for call {callsid}: {message}")
        transcription = json.loads(message).get('channel', {}).get('alternatives', [{}])[0].get('transcript', '')
        if transcription:
            print(f"Transcription for call {callsid}: {transcription}")
            #await audio_manager.send_message(transcription, meeting_id)
            # Process transcription with LLM
            #llm_response = await process_with_llm(transcription)
            # Synthesize audio from LLM response
            #audio_content = synthesize_audio(llm_response)
            # Send synthesized audio back to Twilio
            #await audio_manager.send_message(json.dumps({
            #    "event": "media",
            #    "streamSid": callsid,
            #    "media": {
            #        "payload": base64.b64encode(audio_content).decode('utf-8')
            #    }
            #}), meeting_id)
        
async def twilio_receiver(twilio_ws, audio_queue, callsid_queue, room):
    while True:
        try:
            message = await twilio_ws.receive_text()
            data = json.loads(message)
            if data['event'] == 'start':
                callsid = data['start']['callSid']
                await callsid_queue.put(callsid)
            elif data['event'] == 'media':
                chunk = base64.b64decode(data['media']['payload'])
                await audio_queue.put(chunk)
            elif data['event'] == 'stop':
                await audio_queue.put(None)  # Signal the end of stream
                break
        except WebSocketDisconnect:
            break

# TODO
async def process_with_llm(transcription: str) -> str:
    pass

# TODO
def synthesize_audio(text: str) -> bytes:
    pass
### 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
