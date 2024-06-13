from crewai import Agent, Task, Crew, Process
from crewai.tasks.task_output import TaskOutput
from utils.LLMs import get_llm, get_max_num_iterations
from pydantic import BaseModel, Field
from typing import Dict, Optional
from textwrap import dedent
from utils.utils import json2pydantic
import json, os, asyncio

import inspect
import functools

import instructor
from openai import AsyncOpenAI
from langchain_openai import ChatOpenAI

# TODO: add support for ollama here
client_instructor = instructor.apatch(AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))

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

class TaskContext(BaseModel):
    context: str = Field(..., description="The context of the task")
    schema: Optional[Dict] = Field(default=None, description="Optional and unrestricted schema dictionary")
    name: str = Field(..., description="The name of the task")
    task: str = Field(..., description="Description of the task")

class ImprovedTask(BaseModel):
    description: str = Field(..., description="An easier to understand description for the task to perform")
    expected_output: str = Field(..., description="A description of the expected output for the task")
    coordinator_backstory: str = Field(..., description="A backstory description for a coordinator LLM agent specific for delegating this task")

class Meeting:
    def __init__(self, manager, meeting_id, name, context, task, schema):
        self.manager = manager
        self.meeting_id = meeting_id
        self.name = name
        self.context = context
        self.task = task
        self.schema = schema
        self.tool_name_map = {} # map tool names to tool ids

    async def send_data(self, data):
        try:
            print("DEBUG: send_data called (meeting_id:"+self.meeting_id+")",data)
            await self.manager.send_message(json.dumps(data), self.meeting_id)
        except Exception as e:
            print("DEBUG: send_data ERROR",e)

    async def reportAgentSteps(self, step_output, expert_id: str = None, expert_role: str = None):
        # send the step output to the frontend
        try:
            # build step_object object
            step_object = [] 
            # This function will be called after each step of the agent's execution
            for step in step_output:
                if isinstance(step, tuple) and len(step) == 2:
                    action, observation = step

                    if isinstance(action, dict) and "tool" in action and "tool_input" in action and "log" in action:
                        action_ = {
                            "tool": action.tool,
                            "tool_input": action.tool_input,
                            "log": action.log
                        }
                        step_object.append({ "type":"action_obj", "data":action_ })

                    elif isinstance(action, str):
                        step_object.append({ "type":"action_str", "data":action })
                    else:
                        action_ = {}
                        action_["error"] = False
                        if action.tool:
                            action_["tool"] = action.tool
                            if action.tool == "_Exception":
                                action_["tool_id"] = "error"
                                action_["error"] = True
                                action_["error_message"] = action.tool_input
                            elif action.tool in self.tool_name_map:
                                action_["tool_id"] = self.tool_name_map[action.tool]
                                
                        if action.tool_input:
                            action_["tool_input"] = action.tool_input
                        if action.log:
                            action_["log"] = action.log
                        step_object.append({ "type":"tool", "data":action_ }) #str(action)

                    observation_ = {}
                    observation_["lines"] = []
                    if isinstance(observation, str):
                        observation_lines = observation.split('\n')
                        observation_["lines_raw"] = observation_lines
                        for line in observation_lines:
                            if line.startswith('Title: '):
                                observation_["title"] = line[7:]
                            elif line.startswith('Link: '):
                                observation_["link"] = line[6:]
                            elif line.startswith('Snippet: '):
                                observation_["snippet"] = line[9:]
                            elif line.startswith('-'):
                                observation_["line"] = line
                            else:
                                observation_["lines"].append(line)
                    else:
                        observation_["line"] = str(observation)

                    step_object.append({ "type":"response", "data":observation_ })
                    #step_object.append({ "type":"response_raw", "data":observation })
                else:
                    step_object.append({ "type":"step", "data":str(step) })

            # build payload
            payload = {
                "action": "reportAgentSteps",
                "data": step_object,
                "expert_id": expert_id,
                "expert_role": expert_role
            }
            await self.send_data(payload)
            #print('DEBUG: reportAgentSteps called',json.dumps(step_object))
        except Exception as e:
            print('DEBUG: reportAgentSteps ERROR',e)

    def reportAgentStepsSync(self, step_output):
        # Get the current running loop and create a new task
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(self.reportAgentSteps(step_output))
            else:
                print("reportAgentStepsSync->EVENT LOOP IS NOT RUNNING")
                #loop.run_until_complete(self.reportAgentSteps(step_output))
        except Exception as e:
            print("reportAgentStepsSync->EVENT LOOP ERROR",e)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.reportAgentSteps(step_output))

    def sendDataSync(self, data):
        # Get the current running loop and create a new task
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(self.send_data(data))
            else:
                print("sendDataSync->EVENT LOOP IS NOT RUNNING")
                #loop.run_until_complete(self.reportAgentSteps(step_output))
        except Exception as e:
            print("sendDataSync->EVENT LOOP ERROR",e)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_data(data))

    def create_expert(self, expert: ExpertModel):
        # create list of tools for this expert
        tools = []
        for key in expert.tools:
            print("DEBUG EXPERT TOOLS: key",key[0])
            tool = self.get_tool(key[0])
            self.tool_name_map[tool.name] = key[0]
            print("DEBUG EXPERT TOOLS: tool",str(tool))
            if tool is not None:
                tools.append(tool)
                
        # create report specific for Expert
        def reportAgentStepsSync(step_output):
            # Get the current running loop and create a new task
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(self.reportAgentSteps(step_output,expert.avatar_id,expert.role))
                else:
                    print("reportAgentStepsSync->EVENT LOOP IS NOT RUNNING")
                    #loop.run_until_complete(self.reportAgentSteps(step_output))
            except Exception as e:
                print("reportAgentStepsSync->EVENT LOOP ERROR",e)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.reportAgentSteps(step_output,expert.avatar_id,expert.role))

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
            step_callback=reportAgentStepsSync
        )
        return temp

    def create_task_agent(self, task: TaskContext, improvedTask: ImprovedTask):
        # create report specific for Expert
        def reportAgentStepsSync(step_output):
            # Get the current running loop and create a new task
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(self.reportAgentSteps(step_output,"coordinator","coordinator"))
                else:
                    print("reportAgentStepsSync->EVENT LOOP IS NOT RUNNING")
                    #loop.run_until_complete(self.reportAgentSteps(step_output))
            except Exception as e:
                print("reportAgentStepsSync->EVENT LOOP ERROR",e)
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self.reportAgentSteps(step_output,"coordinator","coordinator"))

        # creates an agent to start and coordinate the task assignment
        return Agent(
            role="Coordinator",
            goal=dedent(f"""
                # the user requested us to perform the following task:\n
                '{task.task}' 
                
                # Use the following as the task context given by the user:\n
                '{task.context}'

                # Also an advanced LLM provided us with the following improved task description:\n
                '{improvedTask.description}'

                # Start and delegate the task assignments within the team for achieving the task given by the user.'
            """),
            backstory=improvedTask.coordinator_backstory,
            allow_delegation=True,
            verbose=True,
            max_iter=get_max_num_iterations(10),
            llm=get_llm(),
            tools=[],
            step_callback=reportAgentStepsSync
        )

    async def launch_task(self, experts: list[ExpertModel], task: TaskContext):
        # build a better description for the task using the task context, name and task
        # let frontend kwnow that the task is being created/thinked
        await self.send_data({
            "action": "createTask",
            "data": "Improving task definition",
        })
        # TODO: create instructor call here
        improved = await client_instructor.chat.completions.create(
            model="gpt-4",
            response_model=ImprovedTask,
            messages=[
                {"role": "system", "content": "# act as an expert prompt engineer. Consider the following JSON object as the context for writing an easier to understand task 'description' that a junior analyst can understand, and a clear 'expected_output' field that describes the expected data output from the given schema in a couple of paragraphs."},
                {"role": "user", "content": dedent(f"""
                    # Use the following JSON schema to understand the expected_output:
                    ```{json.dumps(task.schema)}```

                    # It's most important that you never loose focus on the task expected to be achieved by the user, which is:
                    ```{task.task}```
                    # using the following context:
                    ```{task.context}```
                """)},
            ],
            temperature=0.02,
            stream=False,
        )
        await self.send_data({
            "action": "improvedTask",
            "data": improved.model_dump(),
        })
        print("Improved task", improved.model_dump())
        # create Task Agent (Coordinator)
        print("DEBUG: creating task agent (coordinator)")
        coordinator = self.create_task_agent(task, improved)
        # TODO: convert task JSON schema into Pydantic model
        pydantic_schema = json2pydantic(task.schema)
        print("Pydantic schema", pydantic_schema)
        # create a tool List with all of the tools used by the experts
        tools = []
        for expert in experts:
            for key in expert.tools:
                try: 
                    tool = expert.tools[key]
                    if tool is not None:
                        tools.append(tool)
                except Exception as e:
                    print("ERROR: tool not found", e)
        # create a task object
        def onTaskFinished(output:TaskOutput):
            # send the output to the frontend
            #pydantic_schema_ = json2pydantic(task.schema)
            #output_pydantic = pydantic_schema_(**output.exported_output)
            self.sendDataSync({ 
                "action": "finishedMeeting",
                "data": {
                    "raw": output.raw_output
                }
            })

        task = Task(
            description=improved.description,
            output_pydantic=pydantic_schema,
            expected_output=improved.expected_output,
            async_execution=False,
            agent=coordinator,
            #tools=tools,
            #callback=onTaskFinished
        )
        # build crew
        crew = Crew(
            agents=experts,
            tasks=[task],
            verbose=True,
            process=Process.hierarchical,
            manager_llm=ChatOpenAI(model="gpt-4")
        )
        # launch the crew
        print("Starting CREW processing ..")
        result = await crew.kickoff_async()
        result_json = result.model_dump()
        print("DEBUG: result",result_json)
        # reply END to the frontend
        to_frontend = { 
            "action": "finishedMeeting",
            "data": result_json
        }
        await self.send_data(to_frontend)
        return result

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