import json, os, logging
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
#from chain import chain
from db.database import Database
from utils.ConnectionManager import ConnectionManager

from meeting import meeting as new_meeting, ExpertModel
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

# brand schema example
class BrandColors(BaseModel):
    primary: str = Field(..., description='The primary color for the brand')
    secondary: str = Field(..., description='The secondary color for the brand')

class Brand(BaseModel):
    name: str = Field(..., description='The name of the brand')
    logo: str = Field(..., description='The URL of the logo image')
    colors: BrandColors = Field(..., description='The main colors for the brand')
    fonts: List[str] = Field(..., description='The fonts used by the brand')

class Product(BaseModel):
    name: str = Field(..., description='The name of the product')
    description: str = Field(..., description='The description of the product')
    price: float = Field(..., description='The price of the product')
    image: str = Field(..., description='The URL of the product image')

class BrandSchema(BaseModel):
    brand: Brand = Field(..., description='Brand details')
    products: List[Product] = Field(..., description='The products offered by the brand')

###

@app.websocket("/meeting/{meeting_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str):
    manager = ConnectionManager()
    await manager.connect(websocket, meeting_id)
    try:
        while True:
            data = await websocket.receive_text()
            from_frontend = json.loads(data)
            meeting = new_meeting(
                ws_manager=manager,
                ws_meetingid=meeting_id,
                name=from_frontend["meta"]["name"], 
                context=from_frontend["meta"]["context"], 
                task=from_frontend["meta"]["task"], 
                schema=from_frontend["meta"]["schema"]
            )
            print("data received",from_frontend)
            # build experts
            # for every expert on from_frontend["experts"] (Dict), create an expert, append to experts list
            experts = []
            for expert in from_frontend["experts"]:
                expert_object = from_frontend["experts"][expert]
                expert_json = ExpertModel(**expert_object)
                expert_ = new_meeting.create_expert(expert_json)
                experts.append(expert_)
            # build task and crew
            print("DEBUG: experts",experts)
            # reply END to the frontend
            to_frontend = {
                "action": "finishedMeeting",
                "data": "hello from server",
                "context": meeting.context
            }
            await manager.send_message(json.dumps(to_frontend), meeting_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, meeting_id)

@app.get("/test")
async def test():
    #test endpoint
    print("DEBUG: hello called")
    # hardcode agents for testing traceability
    # create an agent
    accountManager = Agent(
        role='Account Manager',
        goal='Manage client accounts and ensure customer satisfaction.',
        backstory="Experienced in leading customer success teams within tech industries, adept at solving complex client issues.",
        verbose=True,
        allow_delegation=True,
        max_iter=get_max_num_iterations(5),
        llm=get_llm()
    )
    designer = Agent(
        role='Designer',
        goal='Create visually appealing and user-friendly designs.',
        backstory="With a decade of experience in graphic and digital design, specializing in UX/UI and brand identity.",
        verbose=True,
        allow_delegation=False,
        max_iter=get_max_num_iterations(5),
        llm=get_llm()
    )
    # prepare the tools
    from crewai_tools import SerperDevTool
    from crewai_tools import ScrapeWebsiteTool
    tools = [SerperDevTool(), ScrapeWebsiteTool()]
    # create a task
    brand = Task(
        description=dedent(f"""\
            # context:
            A client has requested a new design for their brand, which includes a logo, color scheme, and brand guidelines.
            They have provided us their website for reference which is http://www.enecon.com

            # research the products, services and build the design brand guidelines.
        """),
        output_pydantic=BrandSchema,
        expected_output=dedent("""\
            A detailed brand design guidelines along with the products of the company found on their website."""),
        async_execution=False,
        agent=accountManager,
        tools=tools
    )

    # run the crew
    def testStep(step_output):
        print('DEBUG: testStep called',step_output)

    crew = Crew(
        agents=[accountManager, designer],
        tasks=[brand],
        step_callback=testStep

    )
    return crew.kickoff()
    return "hello "+os.environ["LLM_TYPE"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
