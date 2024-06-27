#from db.database import Database
#from db.models import UrlCache

from typing import Dict, Optional, List, Type, Any, Literal, Set
from langchain.pydantic_v1 import BaseModel, Field
from crewai_tools import tool
from crewai_tools import BaseTool

import hashlib, os, requests, base64, tempfile, json
from datetime import datetime
from utils import ws_client

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

    intro: Optional[str] = Field(None, description="Optional introduction to use before starting the call")
    user_name: Optional[str] = Field(None, description="Optional user name of target user to call; never invent it if unknown.")
    number: Optional[str] = Field(None, description="Mandatory international format number to dial to")
    language: Literal["en","es"] = Field("en", description="Language code to use for the conversation")
    objective: Optional[str] = Field(..., description="Objective to use as validation to know when the call should end.")
    queries: Optional[List[str]] = Field([], description="List of queries to perform during the call")
     
    expert_id: Optional[str] = Field(None, description="Expert ID to use for the call style and knowledge")
    max_duration: Optional[int] = Field(300, description="Maximum duration of the call in seconds") 
    context: Optional[Any] = Field(None, description="Optional addional context to use over the call")
    config: Optional[Dict[str, Any]] = Field(None, description="VectorDB configuration settings for the tool")
 
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
        
        print("Running phone call tool...")
        print(f"Calling {self.user_name} ({self.number})...") 

        # query expert data as object (role, backstory, studies, etc)
        # build payload for manager
        # connect to local ws to notify manager of events to perform a call
        # listen socket for call progress, responses and end status
        # when end status received, disconnect the ws and return the call data here

        # Placeholder for the actual call logic
        return "Nothing to run yet."