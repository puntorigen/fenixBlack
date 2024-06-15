from crewai import Agent, Task, Crew, Process
from crewai.tasks.task_output import TaskOutput
from utils.LLMs import get_llm, get_max_num_iterations
from schemas import TaskContext, ExpertModel, ImprovedTask

from textwrap import dedent
from utils.utils import json2pydantic
import json, os, asyncio

import instructor
from openai import AsyncOpenAI, OpenAI
from langchain_openai import ChatOpenAI

# TODO: add support for ollama here
client_instructor = instructor.apatch(AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))
client_instructor_sync = instructor.apatch(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))


class Meeting:
    def __init__(self, manager, experts, meeting_id, meta):
        self.tool_name_map = {} # map tool names to tool ids
        self.manager = manager
        self.experts = []
        for expert in experts:
            expert_json = ExpertModel(**experts[expert])
            expert_ = self.create_expert(expert=expert_json)
            self.experts.append(expert_)

        self.meeting_id = meeting_id
        self.meta = TaskContext(**meta) # full meta data
        self.name = meta["name"] # TODO refactor code below to use self.meta["key"] instead
        self.context = meta["context"]
        self.task = meta["task"]
        self.schema = meta["schema"]

    async def send_data(self, data): 
        try:
            print("DEBUG: send_data called (meeting_id:"+self.meeting_id+")",data)
            await self.manager.send_message(json.dumps(data), self.meeting_id)
        except Exception as e:
            print("DEBUG: send_data ERROR",e)

    def adaptTextToPersonality(self, text: str, expert: ExpertModel):
        from typing import Dict, Optional
        from pydantic import BaseModel, Field
        class AdaptedStyle(BaseModel):
            new_text: str = Field(None, description="New text adapted to the given personality using a maximum of 140 characters.")
        
        adaptText = client_instructor_sync.chat.completions.create(
            model="gpt-4o",
            response_model=AdaptedStyle,
            messages=[
                {"role": "system", "content": "# act as an excellent writer, expert in adapting text to a specific given personality and style. Always consider writing in the first person and using a maximum of 140 characters, in present tense."},
                {"role": "user", "content": dedent(f"""
                    # Consider the following personality instruction for adapting the text:
                    ```{expert.personality}```

                    # adapt the following text to the given personality: 
                    ```{text}``` 
                """)},
            ],
            temperature=0.2,
            stream=False,
        )
        print("Adapted TEXT FOR PERSONALITY: ", adaptText.model_dump())
        return adaptText.new_text

    def reportAgentStepsSync2(self, step_output, expert: ExpertModel):
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
                    observation_["lines_raw"] = []
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

                    # if length of observation["lines"] is same as 'lines_raw' then it's a single line observation
                    if len(observation_["lines"]) == len(observation_["lines_raw"]):
                        step_object.append({ "type":"response_str", "data":str(observation) })
                    else:
                        # delete observation_["lines"] key
                        del observation_["lines"]
                        step_object.append({ "type":"response_obj", "data":observation_ })
                    #step_object.append({ "type":"response_raw", "data":observation })
                else:
                    step_object.append({ "type":"step", "data":str(step) })

            # prepare/init the 'expert' ready to use 'expert_action' object
            expert_action = {} 
            expert_action["valid"] = False
            expert_action["kind"] = ""
            expert_action["speak"] = ""
            expert_action["expert_id"] = expert.avatar_id
            expert_action["tool_id"] = ""
            # build the real expert_action object
            for step in step_object:
                if step["type"] == "tool" and step["data"]["error"] == False:
                    expert_action["kind"] = "tool"
                    expert_action["valid"] = True
                    expert_action["tool_id"] = step["data"]["tool_id"]
                    expert_action["tool_input"] = step["data"]["tool_input"]
                    expert_action["speak"] = step["data"]["log"]
                    break
            # TODO: if expert.personality is not empty and expert_action is not empty
            if expert.personality and expert_action["valid"]:
                # adapt the expert_action to the expert's personality
                if expert_action["speak"]:
                    try:
                        speak_text = expert_action["speak"]
                        adapted_ = self.adaptTextToPersonality(speak_text, expert)
                        expert_action["speak"] = adapted_
                    except Exception as e2: 
                        print("DEBUG: adaptTextToPersonality ERROR",e2)
                        expert_action["speak"] = ". ".join(expert_action["speak"]) + "." # convert list to string
                else:
                    expert_action["speak"] = "" # convert list to string
            #else:
            #    expert_action["speak"] = ". ".join(expert_action["speak"]) + "." # convert list to string
            #expert_action["speak"] = ". ".join(expert_action["speak"]) + "." # convert list to string
            # TODO: create & call adaptExpertSpeak function to adapt the expert_action spoken & shown text
            # build payload
            payload = {
                "action": "reportAgentSteps",
                "data": step_object,
                "expert_id": expert.avatar_id,
                "expert_role": expert.role,
                "expert_action": expert_action
            }
            self.sendDataSync(payload)
            #print('DEBUG: reportAgentSteps called',json.dumps(step_object))
        except Exception as e:
            print('DEBUG: reportAgentSteps ERROR',e) 

    def sendDataSync(self, data):
        # Get the current running loop and create a new task
        def createNewLoop():
            loop = asyncio.new_event_loop()
            #asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_data(data))
            #asyncio.create_task(self.send_data(data))
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.send_data(data))
            #asyncio.create_task(self.send_data(data))

        except Exception as e:
            print("sendDataSync->EVENT LOOP ERROR; creating new",e)
            createNewLoop()

    def create_expert(self, expert: ExpertModel):
        # create list of tools for this expert
        tools = []
        for key in expert.tools:
            tool = self.get_tool(key[0])
            if tool is not None:
                self.tool_name_map[tool.name] = key[0]
                tools.append(tool)

        # create report specific for Expert
        def reportAgentStepsSync(step_output):
            self.reportAgentStepsSync2(step_output, expert)

        # create an expert
        temp = Agent(
            role=expert.role,
            goal=expert.goal,
            backstory=expert.backstory,
            verbose=True,
            memory=False,
            allow_delegation=expert.collaborate,
            max_iter=get_max_num_iterations(7),
            llm=get_llm(openai="gpt-4o", temperature=0),
            tools=tools,
            step_callback=reportAgentStepsSync
        )
        return temp

    def create_task_agent(self, task: TaskContext, improvedTask: ImprovedTask):
        # create report specific for Expert
        def reportAgentStepsSync(step_output):
            # Get the current running loop and create a new task
            coordinator_expert = ExpertModel(role="coordinator",goal="coordinator",backstory="coordinator",collaborate=True,avatar_id="coordinator")
            self.reportAgentStepsSync2(step_output,coordinator_expert)
            #try:
            #    loop = asyncio.get_running_loop()
            #    if loop.is_running():
            #        loop.create_task(self.reportAgentSteps(step_output,coordinator_expert))
            #    else:
            #        print("reportAgentStepsSync (taskagent)->EVENT LOOP IS NOT RUNNIN; not creating")
                    #loop.run_until_complete(self.reportAgentSteps(step_output))
            #except Exception as e:
            #    print("reportAgentStepsSync (taskagent)->EVENT LOOP ERROR; not creating",e)
                #loop = asyncio.new_event_loop()
                #loop.run_until_complete(self.reportAgentSteps(step_output,coordinator_expert))

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
            llm=get_llm("gpt-4-0125-preview"),
            tools=[],
            step_callback=reportAgentStepsSync
        )
    
    def launch_task(self):
        # build a better description for the task using the task context, name and task
        # let frontend kwnow that the task is being created/thinked
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        self.sendDataSync({
            "action": "createTask",
            "data": "Improving task definition",
        })
        experts = self.experts
        task = self.meta
        # TODO: create instructor call here
        improved = client_instructor_sync.chat.completions.create(
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
        self.sendDataSync({
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
        # create a task object
        task = Task(
            description=improved.description,
            output_pydantic=pydantic_schema,
            expected_output=improved.expected_output,
            async_execution=False,
            agent=coordinator
        )
        # build crew
        def task_callback(task_output: TaskOutput):
            # send the task output to the frontend
            try:
                # build payload
                data_json = task_output.raw_output
                try:
                    data_json = json.loads(data_json)
                except Exception as e:
                    pass
                payload = {
                    "action": "raw_output",
                    "agent": task_output.agent,
                    "data": data_json
                }
                self.sendDataSync(payload)
            except Exception as e:
                print('DEBUG: task_callback ERROR',e)

        crew = Crew(
            agents=experts,
            tasks=[task],
            verbose=2,
            process=Process.hierarchical,
            manager_llm=ChatOpenAI(model="gpt-4o"),
            memory=False, 
            task_callback=task_callback
        )
        # launch the crew
        print("Starting CREW processing ..")
        result = crew.kickoff()
        #result = await crew.kickoff_async()
        result_json = result
        try:
            result_json = result.model_dump()
        except Exception as e:
            print("DEBUG: result_json ERROR",e)
            result_json = str(result)
        print("DEBUG: result",result_json)
        # reply END to the frontend
        payload = { 
            "action": "finishedMeeting",
            "data": result_json
        }
        self.sendDataSync(payload)
        return result

    async def launch_task2(self):
        # build a better description for the task using the task context, name and task
        # let frontend kwnow that the task is being created/thinked
        await self.send_data({
            "action": "createTask",
            "data": "Improving task definition",
        })
        experts = self.experts
        task = self.meta
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
        # create a task object
        task = Task(
            description=improved.description,
            output_pydantic=pydantic_schema,
            expected_output=improved.expected_output,
            async_execution=False,
            agent=coordinator
        )
        # build crew
        def task_callback(task_output: TaskOutput):
            # send the task output to the frontend
            try:
                # build payload
                data_json = task_output.raw_output
                try:
                    data_json = json.loads(data_json)
                except Exception as e:
                    pass
                payload = {
                    "action": "finishedMeeting",
                    "agent": task_output.agent,
                    "data": data_json
                }
                self.sendDataSync(payload)
            except Exception as e:
                print('DEBUG: task_callback ERROR',e)

        crew = Crew(
            agents=experts,
            tasks=[task],
            verbose=2,
            process=Process.hierarchical,
            manager_llm=ChatOpenAI(model="gpt-4o"),
            memory=False, 
            task_callback=task_callback
        )
        # launch the crew
        print("Starting CREW processing ..")
        #result = crew.kickoff()
        result = await crew.kickoff_async()
        result_json = result
        try:
            result_json = result.model_dump()
        except Exception as e:
            print("DEBUG: result_json ERROR",e)
            result_json = str(result)
        print("DEBUG: result",result_json)
        # reply END to the frontend
        ##to_frontend = { 
        ##    "action": "finishedMeeting",
        ##    "data": result_json
        ##}
        ##await self.send_data(to_frontend)
        ##return result

    def get_tool(self, tool_id):
        # get the tool object given the tool_id
        if tool_id == "search":
            from crewai_tools import SerperDevTool
            return SerperDevTool()
        elif tool_id == "website_search":
            from crewai_tools import WebsiteSearchTool
            return WebsiteSearchTool()
        elif tool_id == "scrape":
            #from tools.scrape_website_html_tool import ScrapeWebsiteTool
            from crewai_tools import ScrapeWebsiteTool
            return ScrapeWebsiteTool() 
        #elif tool_id == "pdf_reader":
        #    from crewai_tools import PDFSearchTool
        #    return PDFSearchTool()
        elif tool_id == "youtube_video_search":
            from crewai_tools import YoutubeVideoSearchTool
            return YoutubeVideoSearchTool() 
        return None
    
    def create_meeting(self, request):
        print("DEBUG: called meeting")
        return request.hello