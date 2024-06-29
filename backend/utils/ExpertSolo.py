# Creates a single AI Expert agent for solo tasks
# such as: handling a phone call conversation, learning from a user, single chatting (chrome ext?)
# uses embedchain for knowning the stuff the agent has assigned as 'study'; by default
# if we need to use tools, we can create a crewai agent and chat with it (although it will be much slower)

from schemas import ExpertModel
from embedchain import App
from embedchain.config import BaseLlmConfig
import hashlib, os
from contextlib import contextmanager

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Stream, Connect

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
    def __init__(self, expert:ExpertModel, session_data:dict = None, vector_config:dict = None, session_id:str = None, language:str = "en", envs:dict = {}, public_url:str = None):
        self.embed_chat = None
        self.chat_history = []
        self.session_id = session_id
        self.session_data = session_data # this has all of the phone call session data: user_name, etc
        self.language = language
        self.envs = envs
        self.expert = expert
        self.public_url = public_url
        meeting_meta = self.session_data.get('meeting_meta', {})
        self.system_prompt = f"""# You are {self.expert.role}. {self.expert.backstory}\nYour personal goal is: {self.expert.goal}
        # Your name is {self.expert.name} and you are {self.expert.age} years old. You're having a conversation with {self.session_data.get('user_name', 'someone')} over the phone.
        # You called because you are participating on a group meeting at "Fenix Black" about an assigned task that has the context of '{meeting_meta.get('context', 'unknown')}'.
        # Your group meeting has the following queries you need to get from the user: 
        ```
        {meeting_meta.get('queries', {}).model_dump()}
        ```
        # Your objective for this chatting session is to get the user to answer all of these questions/queries in a natural conversation manner.
        # You may ask the user to repeat or clarify the questions if needed.
        """
        if self.session_data.get('intro'):
            self.system_prompt += f"""# The first message said to the user was: {self.session_data.get('intro')}."""
            self.chat_history.append({ "role":"expert", "text":self.session_data.get('intro'), "sources":None })
        if self.language == "es":
            self.system_prompt += f"""
# You need to make sure to always reply in spanish, and to be patient with the user, but always reply in spanish.
            """
        print(f"DEBUG: ExpertSolo system_prompt: {self.system_prompt}")
        self.query_config = BaseLlmConfig(
            number_documents=5, 
            temperature=0.3,
            #set system prompt to expert role, backstory and goal
            system_prompt=self.system_prompt
        )
        if self.session_id is None:
            self.session_id = hashlib.md5(os.urandom(32)).hexdigest()

        print("Creating ExpertSolo instance ..")

        with temporary_env_vars(self.envs):
            if vector_config:
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
    
    # TODO: create method to check if user has answered all queries in chat_history
    # TODO: create method to translate intro message to language if not english; lets just use direct query
    # TODO: create method to test if given sentence is a complete sentence
    # TODO: create llm method to detect if a given sentence means farewell in any language (to hangup and end the call)

    def set_closing_prompt(self):
        # method to change system_prompt to provide a closing chat flow for the following user messages.
        meeting_meta = self.session_data.get('meeting_meta', {})
        self.system_prompt = f"""# You are {self.expert.role}. {self.expert.backstory}\nYour personal goal is: {self.expert.goal}
        # Your name is {self.expert.name} and you are {self.expert.age} years old. You're having a conversation with {self.session_data.get('user_name', 'someone')} over the phone.
        # You called because you are participating on a group meeting at "Fenix Black" about an assigned task that has the context of '{meeting_meta.get('context', 'unknown')}'.
        # Your group meeting has the following queries you need to get from the user: 
        ```
        {meeting_meta.get('queries', {}).model_dump()}
        ```
        # The user has just finished answering all the queries. You can now provide a natural flowing closing message to end the conversation in a natural way. Always be nice, be grateful of the time the user gave you and ask if the user needs to say any additional thing.
        # Be sure to always say 'goodbye' or 'adios' when you think the conversation is over.
        """
        if self.language == "es":
            self.system_prompt += f"""
# You need to make sure to always reply in spanish, and to be patient with the user, but always reply in spanish.
            """
        self.query_config = BaseLlmConfig(
            number_documents=5, 
            temperature=0.3,
            system_prompt=self.system_prompt
        )

    async def make_phone_call(self, to_number:str, meeting_id:str):
        with temporary_env_vars(self.envs):
            twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
            ## fetch the USER list of purchased phone numbers
            incoming_phone_numbers = twilio_client.incoming_phone_numbers.list()
            if not incoming_phone_numbers:
                return { "error":True, "code": "NO_FROM_NUMBERS_AVAILABLE" ,"message":"User doesn't have any available incoming phone number to call from."}
            ## grab the first available phone number - TODO: get definition from ExpertModel when we have an admin
            from_number = incoming_phone_numbers[0].phone_number
            response = VoiceResponse()
            if self.language == "es":
                response.say("Hola, te estamos llamando de Fenix. Por favor, espera mientras te conecto con un experto.", voice="alice", language="es-MX")
            else:
                response.say("Hi there, we are calling from Fenix. Please wait while we connect you with an expert.", voice="alice", language="en-US")
            #
            response.pause(length=2)
            connect = Connect()
            stream = Stream(url=f"wss://{self.public_url}/audio/{self.session_id}/{meeting_id}")
            connect.append(stream)
            response.append(connect)
            # Make a call using Twilio and connect it to the websocket endpoint with meeting_id and voice_id parameters
            call = twilio_client.calls.create(
                #twiml=f'<Response><Connect><Stream url="wss://{self.public_url}/audio/{self.session_id}/{meeting_id}" statusCallback="https://{self.public_url}/callstatus/{self.session_id}/{meeting_id}" /></Connect></Response>',
                to = to_number,
                from_ = from_number,
                twiml = response,
                status_callback = f"https://{self.public_url}/callstatus/{self.session_id}/{meeting_id}",
                status_callback_event = ['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method = "POST"
            )
            return {"status": "call initiated", "sid": call.sid, "from": from_number, "url": f"wss://{self.public_url}/audio/{self.session_id}/{meeting_id}" }



