from crewai import Agent, Task, Crew, Process
from utils.LLMs import get_llm, get_max_num_iterations
from pydantic import BaseModel, Field
from typing import Dict, Optional
from textwrap import dedent
import json

class AvatarDetails(BaseModel):
    bgColor: Optional[str] = Field(None, description="Background color of the avatar")
    hairColor: Optional[str] = Field(None, description="Hair color of the avatar")
    shirtColor: Optional[str] = Field(None, description="Shirt color of the avatar")
    skinColor: Optional[str] = Field(None, description="Skin color of the avatar")
    earSize: Optional[str] = Field(None, description="Ear size style of the avatar")
    hairStyle: Optional[str] = Field(None, description="Hair style of the avatar")
    noseStyle: Optional[str] = Field(None, description="Nose style of the avatar")
    shirtStyle: Optional[str] = Field(None, description="Shirt style of the avatar")
    facialHairStyle: Optional[str] = Field(None, description="Facial hair style of the avatar")
    glassesStyle: Optional[str] = Field(None, description="Glasses style of the avatar")
    eyebrowsStyle: Optional[str] = Field(None, description="Eyebrows style of the avatar")
    speakSpeed: Optional[int] = Field(None, description="Speed at which the avatar speaks")
    blinkSpeed: Optional[int] = Field(None, description="Speed at which the avatar blinks")

class Tools(BaseModel):
    search: Dict[str, str] = Field(..., description="Tool for searching information with a description of the activity")
    scrape: Dict[str, str] = Field(..., description="Tool for scraping data with a description of the activity")

class ExpertModel(BaseModel):
    type: Optional[str] = Field(None, description="Type of the object, e.g., 'expert'")
    name: str = Field(..., description="Name of the expert")
    age: Optional[int] = Field(None, description="Age of the expert")
    role: str = Field(..., description="Role of the expert, e.g., 'Designer'")
    goal: str = Field(..., description="Goal or objective of the expert")
    backstory: str = Field(..., description="Backstory of the expert detailing previous experiences and specializations")
    collaborate: bool = Field(..., description="Flag indicating whether the expert is open to collaboration")
    avatar: Optional[AvatarDetails] = Field(None, description="Detailed avatar settings of the expert")
    tools: Tools = Field(..., description="Tools associated with the expert and their specific functions")
    avatar_id: str = Field(..., description="Identifier for the field associated with the avatar")

class meeting:
    def __init__(self, ws_manager, ws_meetingid, name, context, task, schema):
        self.ws_manager = ws_manager
        self.ws_meetingid = ws_meetingid
        self.name = name
        self.context = context
        self.task = task
        self.schema = schema

    def reportAgentSteps(self, step_output):
        # send the step output to the frontend
        payload = {
            "action": "reportAgentSteps",
            "data": step_output,
        }
        self.ws_manager.send_message(json.dumps(payload), self.ws_meetingid)
        print('DEBUG: testStep called',step_output)

    def create_expert(self, expert: ExpertModel):
        # create list of tools for this expert
        tools = []
        for key in expert.tools:
            tool = self.get_tool(key)
            if tool is not None:
                tools.append(tool)
        # create an expert
        temp = Agent(
            role=expert.role,
            goal=expert.goal,
            backstory=expert.backstory,
            verbose=True,
            allow_delegation=expert.collaborate,
            max_iter=get_max_num_iterations(5),
            llm=get_llm(),
            tools=tools,
            step_callback=self.reportAgentSteps
        )
        return temp

    def create_task(self, task):
        # build a better description for the task using the task context, name and task
        # let frontend kwnow that the task is being created/thinked
        payload = {
            "action": "createTask",
            "data": "Creating task...",
        }
        self.ws_manager.send_message(json.dumps(payload), self.ws_meetingid)
        # TODO: create instructor call here
        # TODO: convert task JSON schema into Pydantic model
        # create a task object
        pass 

    def get_tool(self, tool_id):
        # get the tool object given the tool_id
        if tool_id == "search":
            from crewai_tools import SerperDevTool
            return SerperDevTool()
        elif tool_id == "scrape":
            from crewai_tools import ScrapeWebsiteTool
            return ScrapeWebsiteTool()
        return None
    
    def create_meeting(self, request):
        print("DEBUG: called meeting")
        return request.hello