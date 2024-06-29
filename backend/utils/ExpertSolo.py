# Creates a single AI Expert agent for solo tasks
# such as: handling a phone call conversation, learning from a user, single chatting (chrome ext?)
# uses embedchain for knowning the stuff the agent has assigned as 'study'; by default
# if we need to use tools, we can create a crewai agent and chat with it (although it will be much slower)

from schemas import ExpertModel
from embedchain import App
from embedchain.config import BaseLlmConfig
import hashlib, os
from contextlib import contextmanager

@contextmanager
def temporary_env_vars(new_vars):
    old_vars = {key: os.getenv(key) for key in new_vars}
    try:
        # Set new environment variables
        print("DEBUG Setting custom env variables",new_vars)
        os.environ.update(new_vars)
        yield
    finally: 
        # Restore old values
        for key, value in old_vars.items():
            if value is None:
                del os.environ[key]
            else:
                os.environ[key] = value

class ExpertSolo:
    def __init__(self, expert:ExpertModel, vector_config:dict = None, session_id:str = None, language:str = "en", envs:dict = {}):
        self.embed_chat = None
        self.chat_history = []
        self.session_id = session_id
        self.language = language
        self.envs = envs
        self.query_config = BaseLlmConfig(
            number_documents=5, 
            temperature=0.3,
            #set system prompt to expert role, backstory and goal
            #system_prompt=f"""
            #"""
        )
        if self.session_id is None:
            self.session_id = hashlib.md5(os.urandom(32)).hexdigest()

        print("Creating ExpertSolo instance ..")

        with temporary_env_vars(self.envs):
            if vector_config:
                # adapt crewai vector_config for embedchain
                embed_config = {
                    "app": vector_config.get("config",{}),
                    "vectordb": vector_config.get("vectordb",{}),
                }
                self.embed_chat = App.from_config(config=vector_config)
            else:
                self.embed_chat = App()
            print(f"DEBUG: ExpertSolo created with session_id: {self.session_id}")
            # add studies if needed 
            if expert.study:
                for url in expert.study:
                    print(f"DEBUG: Adding study url: {url}")
                    self.embed_chat.add(url)

    def query(self, question:str):
        with temporary_env_vars(self.envs):
            self.chat_history.append({ "role":"user", "text":question })
            answer, sources = self.embed_chat.chat(question, citations=True, session_id=self.session_id, config=self.query_config)
            self.chat_history.append({ "role":"expert", "text":answer, "sources":sources })
            return (answer, sources)

    def get_chat_history(self):
        return self.chat_history


