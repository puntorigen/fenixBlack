#from db.database import Database
#from db.models import UrlCache

from typing import Dict, Optional, List, Type, Any, Literal, Set
from langchain.pydantic_v1 import BaseModel, Field
from crewai_tools import tool
from crewai_tools import BaseTool

import hashlib, os, requests, base64, tempfile, json, asyncio
from datetime import datetime
from utils import ws_client, cypher
#from backend.schemas import ExpertModel

#db = Database()
class PhoneCallQuery(BaseModel):
    intro: Optional[str] = Field(None, description="Optional introduction to use before starting the call")
    user_name: Optional[str] = Field(None, description="Optional user name of target user to call; never invent it if unknown.")
    number: str = Field(..., description="Mandatory international format number to dial to")
    language: Literal["en","es"] = Field("en", description="Language code to use for the conversation")
    objective: str = Field(..., description="Objective to use as validation to know when the call should end.")
    queries: List[str] = Field([], description="List of queries to perform during the call")

class PhoneCall(BaseTool):
    name: str = "Have a conversation over a phone call with someone" 
    description: str = "A tool that can be used to perform queries over a phone call conversation to anyone about anything."
    args_schema: Type[BaseModel] = PhoneCallQuery

    # schema fields
    intro: Optional[str] = Field(None, description="Optional introduction to use before starting the call")
    user_name: Optional[str] = Field(None, description="Optional user name of target user to call; never invent it if unknown.")
    number: Optional[str] = Field(None, description="Mandatory international format number to dial to")
    language: Literal["en","es"] = Field("en", description="Language code to use for the conversation")
    objective: Optional[str] = Field(..., description="Objective to use as validation to know when the call should end.")
    queries: Optional[List[str]] = Field([], description="List of queries to perform during the call")
     
    # mandatory init fields 
    expert: Optional[Any] = Field(None, description="Expert to use for the call style and knowledge")
    meeting_id: Optional[str] = Field(None, description="Meeting ID of the active gathering") 
    user_fingerprint: Optional[str] = Field(None, description="User fingerprint to use for encrypted comms within user channel")
    max_duration: Optional[int] = Field(300, description="Maximum duration of the call in seconds") 
    context: Optional[Any] = Field(None, description="Optional addional context to use over the call")
    config: Optional[Dict[str, Any]] = Field(None, description="VectorDB configuration settings for the tool")
    meeting_meta: Optional[Dict[str, Any]] = Field(None, description="Requesting meeting meta data for context reference")
    envs: Optional[Dict[str, Any]] = Field(None, description="Specific meeting environment variables to use for the call")
 
    def configure(self, **kwargs):
        whitelist = set(self.args_schema.__fields__.keys())

        for key, value in kwargs.items():
            if key in whitelist:
                setattr(self, key, value)

        if 'context' in kwargs and isinstance(kwargs['context'], dict):
            self.context = json.dumps(kwargs['context'])

    def __call__(self, **kwargs):
        super().__init__(**kwargs)
        self.configure(**kwargs)

        if self.user_name and self.number:
            self.description = f"A tool that can be used to perform queries over a phone call conversation to {self.name} ({self.number}), using voice."
            self.args_schema = PhoneCallQuery
            self._generate_description()
    
    def _run(
        self,
        **kwargs: Any,
    ) -> Any:
        # Only update attributes if they are None, to preserve values set during initialization
        for key, value in kwargs.items():
            current_value = getattr(self, key, None)
            if current_value is None and value is not None:
                setattr(self, key, value)
        # overwrite these with the given values
        if kwargs.get("intro"):
            self.intro = kwargs.get("intro")
        if kwargs.get("objective"):
            self.objective = kwargs.get("objective")
        if kwargs.get("queries"):
            self.queries = kwargs.get("queries")
 
        print(f"DEBUG: Running phone call tool with data:", self.__dict__) 
        print(f"DEBUG: Running with expert data:", self.expert.__dict__)

        print("Running phone call tool...")
        print(f"Calling {self.user_name} ({self.number})...") 

        # query expert data as object (role, backstory, studies, etc)
        # invent random unique session id for the call (meeting room)
        expert_ = self.expert.model_dump()
        #expert_.pop('tools', None)  # remove expert_ 'tools'
        #expert_.pop('avatar', None)  # remove expert_ 'avatar' (visual style)
        # build payload for manager
        payload = {
            "cmd": "phone_call",
            "data": {
                #"session_id": session_id,
                "language": self.language,
                "user_name": self.user_name,
                "number": self.number,
                "intro": self.intro,
                "objective": self.objective,
                "queries": self.queries,
                "max_duration": self.max_duration, 
                "meeting_id": self.meeting_id, # the room where the user is
                "context": self.context,
                "expert": expert_,
                "config": self.config,
                "meeting_meta": self.meeting_meta,
                "user_fingerprint": self.user_fingerprint,
            },
        }
        payload_for_id = {
            "number": self.number,
            "user_name": self.user_name,
            "expert": expert_,
            "meeting_meta": {
                "name": self.meeting_meta.get("name"),
                "task": self.meeting_meta.get("task"),
            }
        }
        # assign the payload session_id as a hash of payload_for_id, for using it with memory
        payload["data"]["session_id"] = self.generate_md5_session_id(payload_for_id)
        # send envs encrypted by user_fingerprint
        payload["data"]["envs"] = cypher.encryptJSON(self.envs, self.user_fingerprint)
        print(f"DEBUG: Payload to send to manager of events", payload)
        # call call_loop with asyncio
        try:
            loop = asyncio.get_event_loop() 
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        response = loop.run_until_complete(self.call_loop(payload))

        print(f"DEBUG: Response from call_loop", response)
    
        # Placeholder for the actual call logic 
        return "Nothing to run yet." 
    
    def generate_md5_session_id(self, payload):
        hash_input = json.dumps(payload, sort_keys=True)
        hash_output = hashlib.md5(hash_input.encode()).hexdigest()
        return hash_output

    async def call_loop(self, payload):
        # connect to local ws to notify manager of events to perform a call
        client = ws_client.WebSocketClient(self.meeting_id) #the meeting room id from the manager
        connected = await client.connect()
        if connected:
            await client.send(payload)
            final_message = None
            async def on_message(message):
                nonlocal final_message
                if 'cmd' in message and message['cmd'] == 'phone_call_ended':
                    if message['session_id'] == payload['data']['session_id']:
                        print(f"End message for session_id received ({message['session_id']}). Closing connection. Received:",message)
                        final_message = message
                        return True # Return True to indicate the connection should close
                else: 
                    print(f"Received message: {message}")
                return False
            await client.listen_for_messages(on_message)
            await client.disconnect()
            return final_message
        # listen socket for call progress, responses and end status
        # when end status received, disconnect the ws and return the call data here
