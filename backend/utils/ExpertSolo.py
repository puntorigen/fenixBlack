# Creates a single AI Expert agent for solo tasks
# such as: handling a phone call conversation, learning from a user, single chatting (chrome ext?)
# uses embedchain for knowning the stuff the agent has assigned as 'study'; by default
# if we need to use tools, we can create a crewai agent and chat with it (although it will be much slower)

from schemas import ExpertModel
from string import Template
from embedchain import App
from embedchain.config import BaseLlmConfig
from embedchain.store.assistants import AIAssistant, OpenAIAssistant
import hashlib, os
from contextlib import contextmanager

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Stream, Connect
import tools.phone.utils as phone_utils

# helper utils (is_sentence_complete, etc)
import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import Literal
from langcodes import Language as LangCode

PROMPT_HISTORY_MAKE_QUESTION = """
You are a Q&A expert system designed to facilitate a dynamic question-asking session. Your main goal is to generate questions based on the user's input ($query), using the provided context and the existing conversation history.

Here are some guidelines to follow:

1. Assess the user's input ($query) to understand the focus of their inquiry.
2. From the list of available questions (_queries_), select those that are most relevant to the user's input and that have not yet been addressed in the conversation.
3. Ensure your questions encourage the user to provide detailed responses or clarifications that delve deeper into the topic.
4. Use the context and prior interactions to formulate questions that are both relevant and insightful.
5. Avoid redundancy by not asking questions that have already been discussed as per the conversation history.
6. Do not directly reference the context or the history in your questions. Let them guide the formulation of your questions implicitly.

Context information:
----------------------
$context
----------------------

Conversation history:
----------------------
$history
----------------------

Last User's input (_input_):
----------------------
$query
----------------------

Available questions (_queries_):
----------------------
$queries
----------------------

Your task: Formulate a question from _queries_ that aligns with the user's _input_ and has not yet been addressed in the conversation history.
Last user input: $query
Question: 
"""

PROMPT_HISTORY_MAKE_QUESTION_ES = """
Eres un sistema experto de preguntas y respuestas diseñado para facilitar una sesión dinámica de formulación de preguntas. Tu objetivo principal es generar preguntas basadas en la entrada del usuario ($query), utilizando el contexto proporcionado y el historial de conversación existente.

Aquí tienes algunas pautas a seguir:

1. Evalúa la entrada del usuario ($query) para entender el enfoque de su consulta.
2. De la lista de preguntas disponibles (_queries_), selecciona aquellas que sean más relevantes para la entrada del usuario y que aún no se hayan abordado en la conversación.
3. Asegúrate de que tus preguntas alienten al usuario a proporcionar respuestas detalladas o aclaraciones que profundicen en el tema.
4. Utiliza el contexto y las interacciones previas para formular preguntas que sean tanto relevantes como perspicaces.
5. Evita la redundancia al no hacer preguntas que ya se hayan discutido según el historial de la conversación.
6. No hagas referencia directamente al contexto o al historial en tus preguntas. Deja que estos guíen la formulación de tus preguntas de manera implícita.

Información del contexto:
----------------------
$context
----------------------

Historial de conversación:
----------------------
$history
----------------------

Última entrada del usuario (_input_):
----------------------
$query
----------------------

Preguntas disponibles (_queries_):
----------------------
$queries
----------------------

Tu tarea: Formula una pregunta de _queries_ que se alinee con la entrada del usuario _input_ y que aún no se haya abordado en el historial de la conversación.
Última entrada del usuario: $query
Pregunta:
"""

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
        self.language_full = LangCode.get(self.language).display_name()
        self.envs = envs
        self.expert = expert
        self.prepared = False
        self.public_url = public_url
        self.current_question = None
        self.system_prompt = f"""Act as a friendly interviewer; your name is {self.expert.name}, and you need to make the user answer your given questions in a natural conversation manner.
        # Always end your responses with a question that the user can answer, to keep the conversation going, but don't parrrot the user's input. If all th questions have being answered, you can end the conversation.
        """
        # make some prepared texts (for repeating the answer, etc)
        self.premade_texts = {
            "repeat_answer": "I'm sorry, I didn't understand your answer, please repeat it in a different way.",
            "goodbye": "We have all the answers we need, thank you for your time, goodbye."
        }
        self.premade_texts_translated = {}
        # if language includes es, or es-* then add spanish instructions
        base_template = PROMPT_HISTORY_MAKE_QUESTION
        if self.language in ["es", "es-MX", "es-ES", "es-CL"] or self.language.startswith("es-"):
            base_template = PROMPT_HISTORY_MAKE_QUESTION_ES 
        print(f"DEBUG: ExpertSolo system_prompt: {self.system_prompt}")
        base_template_ = Template(base_template)
        base_template = base_template_.safe_substitute({
            "queries": str(self.session_data.get('queries', []))
        })
        #print(f"DEBUG base_template: {base_template}")
        self.query_config = BaseLlmConfig(
            number_documents=3,   
            temperature=0.0,
            #model="gpt-4o",
            prompt=Template(base_template),
            #set system prompt to expert role, backstory and goal
            system_prompt=self.system_prompt
        ) 
        if self.session_id is None:
            self.session_id = hashlib.md5(os.urandom(32)).hexdigest()

        print("Creating ExpertSolo instance ..")

        with temporary_env_vars(self.envs):
            #self.assistant = AIAssistant(
            #    name=f"ExpertSolo-{self.expert.name}",
            #    data_sources=[], 
            #    instructions=self.system_prompt,
            #    collect_metrics=False
            #)
            self.client_instructor = instructor.apatch(AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))
            print(f"DEBUG: using voice_id: {self.session_data.get('voice_id', 'aEO01A4wXwd1O8GPgGlF')} for ExpertSolo Voice")
            if os.getenv("ELEVEN_LABS_API_KEY") is None:
                print("ERROR: ELEVEN_LABS_API_KEY not found in environment variables (can't use phone_call tool)")
                raise "ERROR: ELEVEN_LABS_API_KEY not found in environment variables"
            self.synthethizer = phone_utils.VoiceSynthesizer(os.getenv("ELEVEN_LABS_API_KEY"), voice_id=self.session_data.get('voice_id', 'aEO01A4wXwd1O8GPgGlF'))
            self.basic_config = {
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": "gpt-4", 
                        "temperature": 0.01,
                        "max_tokens": 1000
                    }
                },
            }
            self.basic_config = {
                "llm": {
                    "provider": "groq",
                    "config": {
                        "model": "llama3-70b-8192",
                        "api_key": os.environ.get("GROQ_API_KEY"),
                        "temperature": 0.1,
                        "max_tokens": 1000
                    }
                },
            }
            if vector_config:
                self.basic_config.update(vector_config)
                self.embed_chat = App.from_config(config=self.basic_config)
            else:
                self.embed_chat = App.from_config(config=self.basic_config)
            print(f"DEBUG: ExpertSolo created with session_id: {self.session_id}")

    async def prepare(self):
        # execute agent preparation steps
        # like: translating the queries, pre-generating the audio for the intro, queries, mark the first message, etc
        # translate the premade_texts
        for key, value in self.premade_texts.items():  
            translated_text = await self.translate_from_english(value)
            self.premade_texts_translated[key] = translated_text
            # pre-generate the audios for the premade texts as well
            translated_ms = self.synthethizer.get_audio_base64(value, "")
        # add studies if needed
        if self.expert.study:
            for url in self.expert.study:
                print(f"DEBUG: Adding study url: {url}")
                self.embed_chat.add(url)                
        # invent a first user message
        if self.language in ["es", "es-MX", "es-ES", "es-CL"] or self.language.startswith("es-"):
            if self.session_data.get('user_name', ''):
                self.first_answer = await self.query(f"Hola {self.expert.name}, mi nombre es {self.session_data.get('user_name', '')}, por favor hazme las preguntas que tienes para mi en esta llamada.")
            else:
                self.first_answer = await self.query(f"Hola {self.expert.name}, por favor hazme las preguntas que tienes para mi en esta llamada.")
        else: 
            if self.session_data.get('user_name', ''):
                self.first_answer = await self.query(f"Hi {self.expert.name}, my name is {self.session_data.get('user_name', '')}, please ask me the questions you need from me.")
            else:
                self.first_answer = await self.query(f"Hi {self.expert.name}, please ask me the questions you need from me.")
             
        # translate the intro & queries if needed
        intro = self.session_data.get('intro','')
        queries = self.session_data.get('queries', [])
        self.translated_queries = []
        self.translated_intro = intro
        if self.language != "en" and not self.language.startswith("en-"):
            self.translated_intro = await self.translate_from_english(intro)
            print(f"DEBUG: Translated INTRO",self.translated_intro)
            for query in queries:
                translated_query = await self.translate_from_english(query)
                print(f"DEBUG: Translated query: {translated_query}")
                self.translated_queries.append(translated_query)
        # add expert intro to chat_history
        self.chat_history.append({ "role":"interviewer", "text":self.translated_intro })
        # if self.translated_queries is empty, use the original queries
        if not self.translated_queries:  
            self.translated_queries = queries
        # mark current question as the first one
        self.current_question = self.translated_queries.pop(0)
        # add expert's current question to chat_history
        self.chat_history.append({ "role":"interviewer", "text":self.current_question })
        # pre-generate the audio for the intro message and first answer
        intro = self.session_data.get('intro','') 
        intro_ms = self.synthethizer.get_audio_base64(intro, "")
        first_answer_ms = self.synthethizer.get_audio_base64(self.first_answer, intro)
        current_question_ms = self.synthethizer.get_audio_base64(self.current_question, "")
        # mark as ready to be used
        self.prepared = True

    async def validate_answer_for_current_question(self, user_answer):
        # returns True if the current answer is valid for the current question
        # idea: we can use the llm to check if the answer is a valid answer for the current question
        # intention: 1) we send audio of current question, then we call this method to validate user answer, if it's valid, we move to the next question
        class IsValid(BaseModel):
            is_answer_valid_for_question: bool = Field(True, description="Is the user text a valid answer for the current question?")
            alternate_question: str = Field("", description="Alternate question to ask if the answer is not valid, in the same original question language")

        test = await self.client_instructor.chat.completions.create(
            model="gpt-4", #"mixtral-8x7b-32768", #llama3-8b-8192",
            response_model=IsValid,
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""# the following is the question made to the user:
                    ```{self.current_question}```
                    # consider the user answered the question through a phone call so it may have some mispellings but be correct nonetheless, and the transcribed text was the following:
                    ```{user_answer}``` 
                    # is the given answer, valid for the given question? 
                    """
                }
            ]
        )
        if test.is_answer_valid_for_question:
            # move to the next question, if there's any
            if self.translated_queries:
                self.current_question = self.translated_queries.pop(0)
                print(f"DEBUG: Moving to next question: {self.current_question}")
                print(f"Alternate version of question: {test.alternate_question}")
            else:
                self.current_question = None # no more questions to ask
                print(f"DEBUG: No more questions to ask, ending conversation.")

        return test.is_answer_valid_for_question

    async def query(self, user_text:str):
        with temporary_env_vars(self.envs):
            self.chat_history.append({ "role":"user", "text":user_text })
            #answer = self.assistant.chat(question)
            # 1) let's validate that the received user text is a valid answer for the current question
            valid = await self.validate_answer_for_current_question(user_text)
            # 2) if it's valid, we move to the next question
            if valid:
                if self.current_question:
                    # add next expert's question to chat_history
                    self.chat_history.append({ "role":"interviewer", "text":self.current_question })
                    return self.current_question # this is the next question for the user
                else:
                    # if None, then we have no more questions to ask, we should say goodbye in the user language
                    return self.premade_texts_translated["goodbye"] #TODO: replace with pre-generated audio
            # 3) if it's not valid, we ask the user to repeat the answer
            return self.premade_texts_translated["repeat_answer"] #TODO: replace with pre-generated audio
            #answer = self.embed_chat.chat(user_text, citations=False, session_id=self.session_id, config=self.query_config)
            #self.chat_history.append({ "role":"expert", "text":answer })
            #return answer
            #return (answer, sources)

    def get_chat_history(self):
        return self.chat_history

    # DONE: create method to translate intro message to language if not english; lets just use direct query
    async def translate_from_english(self, english_sentence, target_language:str = None):
        if target_language is None:
            target_language = self.language_full
        class Response(BaseModel):
            translated_sentence: str = Field(True, description=f"Translated sentence in {target_language}")

        run_ = await self.client_instructor.chat.completions.create(
            model="gpt-4", #"mixtral-8x7b-32768", #llama3-8b-8192",
            response_model=Response,
            messages=[
                {
                    "role": "user",
                    "content": f"""# You're an expert translator, and you need to translate the following sentence from English to '{target_language}' and be friendly:
                    ```{english_sentence}```
                    """
                }
            ]
        )
        return run_.translated_sentence

    # TODO: create llm method to detect if a given sentence means farewell in any language (to hangup and end the call)

    # DONE: create method to test if given sentence is a complete sentence
    async def is_complete_sentence(self, prev_sentence,current_sentence):
        class DoesSentenceAppearComplete(BaseModel):
            does_it_look_complete: bool = Field(True, description="Does the sentence appear to be complete?")
        test = await self.client_instructor.chat.completions.create(
            model="gpt-4o", #"mixtral-8x7b-32768", #llama3-8b-8192",
            response_model=DoesSentenceAppearComplete,
            messages=[
                {
                    "role": "user",
                    "content": f"""# the following is the previous part of the sentence:
                    ```{prev_sentence}```
                    # is the following sentence complete or do you think there's more to come? 
                    ```{current_sentence}```
                    """
                }
            ]
        )
        return test.does_it_look_complete

    def set_closing_prompt(self):
        # method to change system_prompt to provide a closing chat flow for the following user messages.
        meeting_meta = self.session_data.get('meeting_meta', {})
        self.system_prompt = f"""# Your name is '{self.expert.name}', and your role is a '{self.expert.role}'. {self.expert.backstory}\nYour personal goal this session is: '{self.expert.goal}'
        # You are {self.expert.age} years old. You're having a conversation with {self.session_data.get('user_name', 'someone')} over the phone.
        # You called because you are participating on a group meeting at "Fenix Black" about an assigned task that has the context of '{meeting_meta.get('context', 'unknown')}'.
        # Your group meeting has the following queries for which you need to query the user about: 
        ```
        {str(self.session_data.get('queries', {}))}
        ```
        # Your objective for this chatting session is to get the user to answer all of these questions/queries in a natural conversation manner.
        # You may ask the user to repeat or clarify the questions if needed.
        """
        if self.language in ["es", "es-MX", "es-ES"] or self.language.startswith("es-"):
            self.system_prompt += f"""
# You need to make sure to always reply in spanish, and to be patient with the user, but always reply in spanish.
            """
        self.query_config = BaseLlmConfig(
            number_documents=5, 
            temperature=0.02,
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
            if self.language in ["es", "es-MX", "es-ES"] or self.language.startswith("es-"):
                response.say("Hola, te estamos llamando de Fenix.", voice="alice", language="es-MX")
            else:
                response.say("Hi there, we are calling from Fenix.", voice="alice", language="en-US")
            #
            response.pause(length=0)
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



