### TEMPORAL LANGUAGE MODEL PROCESSOR => WE SHOULD REPLACE IT BY THE EXPERT MODEL THAT'S USING THE TOOL
import time, os
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain

# Helper for testing if the given sentence is complete
import instructor
from openai import AsyncOpenAI, OpenAI
from groq import Groq
from pydantic import BaseModel, Field
from typing import Literal 

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
groq_client = instructor.from_groq(groq_client, mode=instructor.Mode.TOOLS)
client_instructor = instructor.apatch(AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))

class LanguageModelProcessor:
    def __init__(self, our_name, groq_api_key):
        #self.llm = ChatGroq(temperature=0, model_name="mixtral-8x7b-32768", groq_api_key=groq_api_key)
        self.llm = ChatOpenAI(temperature=0.3, model_name="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))
        # self.llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-0125", openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.our_name = our_name
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        # Load the system prompt from a file
        system_prompt = f"""
# Current date and time is {time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}
# Our location is Santiago, Chile.
# Guidelines:
- You are a friendly conversational human assistant named Gabriela.
- Never say you're a bot or AI. Behave as a human.
- Use short, conversational responses as if you're having a live conversation.
- Your response should be under 20 words, no parentheses, and no bullet points. Don't be too formal.
- Never repeat what the user says, and don't repeat yourself too much. Try not to end in questions.
- Since the user text is being transcribed from speech, there may be errors and misspellings; try your best to understand at the first shot.
- Do not respond with any code, only conversation. Propose interesting questions if the conversation is stuck.
- Always be polite and respectful.
- Always respond in Spanish since the user is from Chile.
"""

        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{text}")
        ])

        self.conversation = LLMChain(
            llm=self.llm,
            prompt=self.prompt,
            memory=self.memory
        )

    async def is_complete_sentence(self, prev_sentence,current_sentence):
        class DoesSentenceAppearComplete(BaseModel):
            does_it_look_complete: bool = Field(True, description="Does the sentence appear to be complete?")
        test = await client_instructor.chat.completions.create(
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

    def process(self, text):
        self.memory.chat_memory.add_user_message(text)  # Add user message to memory

        start_time = time.time()

        # Go get the response from the LLM
        response = self.conversation.invoke({"text": text})
        end_time = time.time()

        self.memory.chat_memory.add_ai_message(response['text'])  # Add AI response to memory

        elapsed_time = int((end_time - start_time) * 1000)
        print(f"LLM ({elapsed_time}ms): {response['text']}")
        return response['text']