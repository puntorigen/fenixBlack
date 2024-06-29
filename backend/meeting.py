from crewai import Agent, Task, Crew, Process
from crewai.tasks.task_output import TaskOutput
from utils.LLMs import get_llm, get_max_num_iterations, get_ollama_model
from schemas import TaskContext, ExpertModel, ImprovedTask

from textwrap import dedent
from utils.utils import json2pydantic, MyBaseModel, extract_sections
from utils.cypher import decryptJSON
import json, os, asyncio, dirtyjson, re
from contextlib import contextmanager

import instructor
from openai import AsyncOpenAI, OpenAI
from langchain_openai import ChatOpenAI

# increase connection pool size
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=50)
session.mount('https://', adapter)
session.mount('http://', adapter)

# TODO: add support for ollama here
client_instructor = instructor.apatch(AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))
client_instructor_sync = instructor.apatch(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))


class Meeting:
    def __init__(self, manager, experts, meeting_id, meta, settings, user_fingerprint):
        self.tool_name_map = {} # map tool names to tool ids
        self.manager = manager 
        self.loop = None
 
        self.meeting_id = meeting_id
        self.experts = []
        self.experts_ = experts
        self.meta = TaskContext(**meta) # full meta data
        self.settings = settings # encrypted settings
        self.user_fingerprint = user_fingerprint

        #DEPRECTATED:: soon to be removed
        #self.name = meta["name"] # TODO refactor code below to use self.meta["key"] instead
        #self.context = meta["context"] 
        #self.task = meta["task"]
        #self.schema = meta["schema"]


    async def send_data(self, data): 
        try:
            print("DEBUG: send_data called (meeting_id:"+self.meeting_id+")")
            await self.manager.send_message(json.dumps(data), self.meeting_id)
        except Exception as e:
            print("DEBUG: send_data ERROR",e)

    def adaptTextToPersonality(self, text: str, expert: ExpertModel, max_tokens=100):
        from typing import Dict, Optional
        from pydantic import BaseModel, Field
        rules = ""
        #if self.meta.rules:
        #    rules = dedent(f"""
        #        # You must also always follow the rules given by the user, which are:
        #        ```{self.meta.rules}```
        #    """)
        class AdaptedStyle(BaseModel):
            new_text: str = Field(None, description="New text adapted to the given personality using a maximum of 140 characters. Don't include either actions and/or action inputs.")
        
        system_prompt = "# act as an excellent and engaging writer, expert in adapting the given text to a specific given personality, style and voice. Always consider using a maximum of 140 characters, and always focus on the latest action being done. You speak like a friendly human, removing any unnecessary words and JSON objects and/or parameters."
        if max_tokens > 100:
            system_prompt = "# act as an excellent and engaging writer, expert in summarizing while adapting the given text to a specific given personality, style and voice, without loosing any content. You speak like a friendly human, removing any unnecessary words and JSON objects and/or parameters. If there's a conclusion or recommendations, always include them."

        adaptText = client_instructor_sync.chat.completions.create(
            model="gpt-4o",
            response_model=AdaptedStyle, 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": dedent(f"""
                    # Consider the following personality instruction for adapting the text:
                    ```{expert.personality}```

                    {rules}
                    # adapt the following text to the given personality: 
                    ```{text}``` 

                    # always use We instead of You, and use present continuous tense if 'you' are performing something.
                """)},
            ],
            temperature=0.6,
            max_tokens=max_tokens,
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
                            # filter the log to just include the 'Thought:' part if available
                            action_["thought"] = extract_sections(action.log)

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
                    # re-format if step["data"]["thought"]["Thought"] is not empty
                    if step["data"]["thought"] and step["data"]["thought"]["Thought"]:
                        expert_action["speak"] = step["data"]["thought"]["Thought"]
                        expert_action["kind"] = "thought"
                    break
            
            # create thought version if necessary
            if expert_action["kind"] == "":
                for step in step_object:
                    if step["type"] == "response_str" and step["data"]:
                        expert_action["kind"] = "thought"
                        expert_action["valid"] = True
                        expert_action["speak"] = step["data"]
                        try:
                            as_json_test = dirtyjson.loads(step["data"])
                            expert_action["speak"] = as_json_test["output"]
                        except Exception as e:
                            pass
                        # if expert_action["speak"] is just a word, then valid=False
                        if len(expert_action["speak"].split()) == 1:
                            expert_action["valid"] = False
                        elif "final answer" in expert_action["speak"]:
                            expert_action["valid"] = False
                        elif "I did it wrong." in expert_action["speak"]:
                            expert_action["valid"] = False
                        if expert_action["valid"]:
                            break

            # if expert.personality is not empty and expert_action is not empty
            if expert.personality and expert_action["valid"]:
                # adapt the expert_action to the expert's personality
                if expert_action["speak"]: 
                    expert_action["speak_raw"] = expert_action["speak"]
                    try:
                        speak_text = expert_action["speak"]
                        adapted_ = self.adaptTextToPersonality(speak_text, expert)
                        expert_action["speak"] = adapted_
                    except Exception as e2: 
                        print("DEBUG: adaptTextToPersonality ERROR3",e2)
                        expert_action["speak"] = ". ".join(expert_action["speak"]) + "." # convert list to string
                        expert_action["speak"] = self.adaptTextToPersonality(expert_action["speak"], expert)
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
            self.loop = asyncio.new_event_loop()
            #asyncio.set_event_loop(loop)
            self.loop.run_until_complete(self.send_data(data))
            #asyncio.create_task(self.send_data(data))
        try:
            if self.loop is None:
                self.loop = asyncio.get_event_loop() 
            self.loop.run_until_complete(self.send_data(data))
            #asyncio.create_task(self.send_data(data))

        except Exception as e:
            print("sendDataSync->EVENT LOOP ERROR; creating new",e)
            createNewLoop()

    def create_expert(self, expert: ExpertModel):
        self.sendDataSync({
            "action": "creating_expert",
            "expert_id": expert.avatar_id,
            "in_progress": True
        }) 
        # create list of tools for this expert
        tools = []
        tools_dict = expert.tools.model_dump(exclude_none=True)
        print(f"DEBUG expert_id ({expert.avatar_id}) tools:", tools_dict)
        for key,value in tools_dict.items():
            print(f"DEBUG {expert.avatar_id} expert TOOLS:", key, value)
            tool = None
            if value:
                try:
                    value = json.loads(value)
                except Exception as e:
                    pass
            if isinstance(value,dict) and "meta" in value:
                tool = self.get_tool(key, value["meta"], expert)
            else:
                tool = self.get_tool(key, value, expert)
            if tool is not None: 
                self.tool_name_map[tool.name] = key
                tools.append(tool) 
        # add RAG tool for each 'expert.study' item
        if expert.study:
            for url in expert.study:
                rag_tool = self.get_study_tool(url)
                if rag_tool is not None: 
                    self.tool_name_map[rag_tool.name] = 'study'
                    tools.append(rag_tool)

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
            max_execution_time=expert.max_execution_time,
            max_iter=expert.max_num_iterations, #get_max_num_iterations(7),
            llm=get_llm(openai="gpt-4o", temperature=0.0), #gpt-4 temp 0.1, works best, but it's pricier
            tools=tools,
            step_callback=reportAgentStepsSync 
        )
        self.sendDataSync({
            "action": "creating_expert",
            "expert_id": expert.avatar_id,
            "in_progress": False
        })
        return temp

    def create_task_agent(self, task: TaskContext, improvedTask: ImprovedTask):
        # create report specific for Expert
        def reportAgentStepsSync(step_output):
            # Get the current running loop and create a new task
            coordinator_expert = ExpertModel(role="coordinator",goal="coordinator",backstory="coordinator",collaborate=True,avatar_id="coordinator")
            self.reportAgentStepsSync2(step_output,coordinator_expert)

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
            max_iter=get_max_num_iterations(5),
            llm=get_llm("gpt-4o",temperature=0.0),
            tools=[],
            step_callback=reportAgentStepsSync
        )

    @contextmanager
    def temporary_env_vars(self, new_vars):
        old_vars = {key: os.getenv(key) for key in new_vars}
        try:
            # Set new environment variables
            print("DEBUG Setting custom meeting env variables",new_vars)
            os.environ.update(new_vars)
            yield
        finally: 
            # Restore old values
            for key, value in old_vars.items():
                if value is None:
                    del os.environ[key]
                else:
                    os.environ[key] = value

    def launch_task(self):
        # build a better description for the task using the task context, name and task
        # let frontend kwnow that the task is being created/thinked
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop) 
        settings_env = self.settings.get("env", {})

        with self.temporary_env_vars(settings_env):
            # create experts
            for expert in self.experts_:
                expert_json = ExpertModel(**self.experts_[expert])
                expert_ = self.create_expert(expert=expert_json)
                self.experts.append(expert_)

            self.sendDataSync({
                "action": "createTask",
                "data": "Improving task definition",
            })
            experts = self.experts
            task_ = self.meta
            rules = ""
            # add rules to the task description and if they are not empty
            if self.meta.rules:
                rules = dedent(f"""
                    # You must also always follow the rules given by the user, which are:
                    ```{self.meta.rules}```
                """)
            # TODO: create instructor call here
            try:
                improved = None
                if task_.schema:
                    improved = client_instructor_sync.chat.completions.create(
                        model="gpt-4",
                        response_model=ImprovedTask, 
                        messages=[
                            {"role": "system", "content": "# act as an expert prompt engineer. Consider the following JSON object as the context for writing an easier to understand task 'description' that a junior analyst can understand, and a clear 'expected_output' field that describes the expected data output from the given schema in a couple of paragraphs. Check everything prior to sharing with me to ensure accuracy. You only have one shot, so take your time and think step by step."},
                            {"role": "user", "content": dedent(f"""
                                # Use the following JSON schema to understand the expected_output:
                                ```{json.dumps(task_.schema)}```

                                # It's most important that you never loose focus on the task expected to be achieved by the user, which is:
                                ```{task_.task}```

                                # also use the following context:
                                ```{task_.context}```

                                # Now, improve the task description and expected_output fields, also adding a default https schema to any url if not correctly formed:
                            """)}, 
                        ],
                        temperature=0.0,
                        stream=False, 
                    )
                else:
                    # improve the task description without schema
                    improved = client_instructor_sync.chat.completions.create(
                        model="gpt-4",
                        response_model=ImprovedTask, 
                        messages=[
                            {"role": "system", "content": "# act as an expert prompt engineer. Consider the following user given task and the given context for writing an easier to understand task 'description' that a junior analyst can understand, and a clear 'expected_output' field that clearly describes the expected data output in a couple of paragraphs. Check everything prior to sharing with me to ensure accuracy. You only have one shot, so take your time and think step by step."},
                            {"role": "user", "content": dedent(f"""
                                # It's most important that you never loose focus on the task expected to be achieved by the user, which is:
                                ```{task_.task}```

                                # also use the following context:
                                ```{task_.context}```

                                # Now, improve the task description and expected_output fields, also adding a default https schema to any url if not correctly formed:
                            """)}, 
                        ],
                        temperature=0.0,
                        stream=False, 
                    )

                self.sendDataSync({
                    "action": "improvedTask",
                    "data": improved.model_dump(),
                })
                print("Improved task", improved.model_dump())
            except Exception as e:
                print("DEBUG: improving task ERROR",e)
                payload = { 
                    "action": "error",
                    "type": "improved_task",
                    "data": str(e)
                }
                self.sendDataSync(payload)
                raise 
            
            # create Task Agent (Coordinator)
            print("DEBUG: creating task agent (coordinator)")
            coordinator = self.create_task_agent(task_, improved)
            # TODO: convert task JSON schema into Pydantic model
            task = None
            pydantic_schema = None
            if task_.schema:
                pydantic_schema = json2pydantic(task_.schema)
                print("Pydantic schema", pydantic_schema)
                # create a task object
                task = Task(
                    description=improved.description,
                    output_pydantic=pydantic_schema,
                    expected_output=improved.expected_output,
                    async_execution=False,
                    agent=coordinator
                )
            else:
                # create task without enforcing schema
                print("Creating task without given schema")
                # create a task object
                task = Task(
                    description=improved.description,
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
                verbose=False,
                process=Process.hierarchical,
                manager_llm=ChatOpenAI(model="gpt-4o", temperature=0.0),
                memory=False,  
                task_callback=task_callback,
                full_output=True
            ) 
            # launch the crew
            print("Starting CREW processing ..")
            try:
                result = crew.kickoff() 
            except Exception as e:
                print("DEBUG: meeting ERROR",e)
                payload = { 
                    "action": "error",
                    "type": "crew_kickoff",
                    "data": str(e)
                }
                self.sendDataSync(payload)
                raise
                #self.manager.disconnect(self.meeting_id)
                # raise error to disconnect the meeting
            
            #result = await crew.kickoff_async()
            result_json = result["final_output"]
            if task_.schema:
                result_json:MyBaseModel = result["final_output"]
            metrics:dict = result["usage_metrics"]
            print("DEBUG: result",result_json)
            try: 
                result_json = result_json.json()
            except Exception as e:
                pass
            # generate friendly text from the result_json
            final_expert = ExpertModel(role="virtual",goal="virtual",backstory="virtual",collaborate=True,avatar_id="virtual", personality="Use easy to understand terms, don't use exagerated words, and talk about what was achieved.", max_execution_time=500, max_num_iterations=7)
            final_report = self.adaptTextToPersonality(result_json, final_expert, 4000)
            # reply END to the frontend
            payload = { 
                "action": "finishedMeeting",
                "data": result_json,
                "final_report": final_report,
                "metrics": metrics,
                #"tasks": result["tasks_outputs"].dict(),
            } 
            self.sendDataSync(payload)
        return self

    def vector_config(self, keyword="youtube"):
        # TODO: check if we have PINECONE_API_KEY in the environment and if not return chroma config
        pinecone_api_key = os.getenv('PINECONE_API_KEY', '').strip()
        if pinecone_api_key:
            return {
                "app": {
                    "config": {
                        "name": f"{keyword}_pinecone",
                    }
                },
                "vectordb" : {
                    "provider": "pinecone",
                    "config": {
                        "metric": "cosine",
                        "vector_dimension": 1536, 
                        "index_name": f"fenix-black-test",
                    } 
                },
            }
        # default is chroma vectordb config
        return {
            "app": {
                "config": {
                    "name": f"{keyword}_chroma",
                }
            },
            "vectordb" : { 
                "provider": "chroma",
                "config": { 
                    "collection_name": "fenix-black-meeting",
                    "dir": "meetings-data",
                    "allow_reset": True,
                    #"vector_dimension": 1536, # openai embeddings
                } 
            },
        }

    def get_study_tool(self, url):
        # depending on url extension (.pdf, .html, .txt) return the appropriate tool
        if url.endswith(".pdf"):
            from crewai_tools import PDFSearchTool
            return PDFSearchTool(config=self.vector_config("study"),pdf=url)
        elif url.endswith(".txt"):
            from crewai_tools import TXTSearchTool
            return TXTSearchTool(config=self.vector_config("study"),txt=url)
        elif url.endswith(".csv"):
            from crewai_tools import CSVSearchTool
            return TXTSearchTool(config=self.vector_config("study"),csv=url)
        elif url.endswith(".xml"):
            from crewai_tools import XMLSearchTool
            return XMLSearchTool(config=self.vector_config("study"),xml=url)
        elif url.endswith(".xml"):
            from crewai_tools import JSONSearchTool
            return JSONSearchTool(config=self.vector_config("study"),json_path=url)
        elif url.endswith(".docx"):
            from crewai_tools import DOCXSearchTool
            return DOCXSearchTool(config=self.vector_config("study"),docx=url)
        elif url.endswith(".mdx"):
            from crewai_tools import MDXSearchTool
            return MDXSearchTool(config=self.vector_config("study"),mdx=url)
        elif "github.com" in url:
            from crewai_tools import GithubSearchTool
            return GithubSearchTool(config=self.vector_config("study"), github_url=url, content_types=['code','issue'])
        elif "youtube.com" in url and "watch?" in url:
            from crewai_tools import YoutubeVideoSearchTool
            return YoutubeVideoSearchTool(config=self.vector_config("study"), youtube_video_url=url)
        elif "postgresql://" in url and "|" in url:
            #postgresql://user:password@localhost:5432/mydatabase|mytable
            from crewai_tools import PGSearchTool
            db_uri = url.split("|").pop(0)
            db_table = url.split("|").pop(1)
            return PGSearchTool(config=self.vector_config("study"), db_uri=db_uri, db_table=db_table)
        
        elif url.startswith("http"): # else if url contains website https:// or http://
            from crewai_tools import WebsiteSearchTool
            return WebsiteSearchTool(config=self.vector_config("study"), website=url)
        return None

    def get_tool(self, tool_id, tool_meta, expert=ExpertModel):
        print(f"DEBUG ({expert.avatar_id}) get_tool tool_id",tool_id)
        # get the tool object given the tool_id
        if tool_id == "search":
            from crewai_tools import SerperDevTool
            return SerperDevTool()
        elif tool_id == "website_search":
            from crewai_tools import WebsiteSearchTool
            return WebsiteSearchTool(config=self.vector_config("websites"))
        elif tool_id == "scrape":
            #from tools.scrape_website_html_tool import ScrapeWebsiteTool
            from crewai_tools import ScrapeWebsiteTool
            return ScrapeWebsiteTool() 
        elif tool_id == "pdf_reader":
            from crewai_tools import PDFSearchTool
            #from tools.pdf_search_tool import PDFSearchTool
            return PDFSearchTool(config=self.vector_config("youtube"))
        elif tool_id == "youtube_video_search":
            from crewai_tools import YoutubeVideoSearchTool
            return YoutubeVideoSearchTool(config=self.vector_config("youtube")) 
        elif tool_id == "query_visual_website": 
            from tools.vision import QueryVisualWebsite 
            return QueryVisualWebsite()
        elif tool_id == "phone_call":
            from tools.phone import PhoneCall
            meta = tool_meta
            meta["config"] = self.vector_config("phone_call")
            meta["expert"] = expert
            meta["meeting_meta"] = self.meta.model_dump(exclude_none=True)
            meta["meeting_id"] = self.meeting_id # active user channel_id
            meta["user_fingerprint"] = self.user_fingerprint # required for sending encrypted data to the user channel
            meta["envs"] = self.settings.get("env", {})
            #print(f"DEBUG 'meta' call",meta) 
            return PhoneCall(**meta)
        return None
    
    def create_meeting(self, request):
        print("DEBUG: called meeting")
        return request.hello